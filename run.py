"""富山市の受付サイネージ。APIキーは環境変数 WEATHERAPI_KEY に設定する。"""

import datetime as dt
import math
import os
import threading
import time
from urllib.parse import urlsplit

import requests
from flask import Flask, make_response, render_template

app = Flask(__name__)
JST = dt.timezone(dt.timedelta(hours=9))
API_URL = "https://api.weatherapi.com/v1/forecast.json"
CACHE_SECONDS = 15 * 60
MAX_CACHE_SECONDS = 60 * 60  # 現在情報のキャッシュ上限。予報も同時に破棄する。
RETRY_SECONDS = 60
PAGE_REFRESH_SECONDS = 5 * 60


def jst_now():
    return dt.datetime.now(JST)


class WeatherUnavailable(Exception):
    pass


def as_dict(value):
    return value if isinstance(value, dict) else {}


def number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def display_number(value, unit="", minimum=None, maximum=None):
    value = number(value)
    if value is None or (minimum is not None and value < minimum):
        return "—"
    if maximum is not None and value > maximum:
        return "—"
    return "{:g}{}".format(round(value, 1), unit)


def icon_url(value):
    # APIが提供するアイコンのみ許可。既存のstatic画像は不要。
    if not isinstance(value, str):
        return ""
    url = "https:" + value if value.startswith("//") else value
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    if parts.scheme == "https" and parts.netloc == "cdn.weatherapi.com":
        return url
    return ""


def fetch_weather():
    api_key = os.environ.get("WEATHERAPI_KEY", "").strip()
    if not api_key:
        raise WeatherUnavailable("APIキーが未設定です")
    params = {
        "key": api_key,
        "q": os.environ.get("WEATHERAPI_LOCATION", "36.6953,137.2113"),
        "days": 2,
        "lang": "ja",
        "aqi": "no",
        "alerts": "no",
    }
    try:
        with requests.get(API_URL, params=params, timeout=(3, 8),
                          allow_redirects=False) as response:
            if response.status_code != 200:
                # エラー本文やURLにはAPIキーが含まれ得るため、ログに出さない。
                app.logger.warning("WeatherAPI HTTP status=%s", response.status_code)
                raise WeatherUnavailable("天気情報を取得できませんでした")
            payload = response.json()
    except requests.RequestException:
        app.logger.warning("WeatherAPI request failed (URL and key omitted)")
        raise WeatherUnavailable("天気情報を取得できませんでした") from None
    except ValueError:
        raise WeatherUnavailable("天気情報の応答形式を確認できませんでした") from None

    if not isinstance(payload, dict) or payload.get("error"):
        raise WeatherUnavailable("天気情報の応答形式を確認できませんでした")
    days = as_dict(payload.get("forecast")).get("forecastday")
    if not isinstance(days, list) or not days or not all(isinstance(d, dict) for d in days):
        raise WeatherUnavailable("予報情報を取得できませんでした")
    # 正常HTTPでも当日の予報がない応答は、新しい正常データとして採用しない。
    today = jst_now().date().isoformat()
    if not any(d.get("date") == today and isinstance(d.get("day"), dict) for d in days):
        raise WeatherUnavailable("当日の予報情報を取得できませんでした")
    return payload


class WeatherCache:
    """1プロセス内で両URL・複数スレッドが共有する、アクセス時更新キャッシュ。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.payload = None
        self.saved_at = None
        self.saved_mono = None
        self.last_attempt = None
        self.error = ""

    def get(self):
        with self.lock:
            now = time.monotonic()
            # 期限切れのデータは表示しないだけでなく参照も破棄する。
            if self.saved_mono is not None and now - self.saved_mono >= MAX_CACHE_SECONDS:
                self.payload = None
                self.saved_at = None
                self.saved_mono = None
            same_date = self.saved_at is not None and self.saved_at.date() == jst_now().date()
            fresh = (self.payload is not None and same_date and
                     now - self.saved_mono < CACHE_SECONDS)
            retry_ready = self.last_attempt is None or now - self.last_attempt >= RETRY_SECONDS
            if not fresh and retry_ready:
                self.last_attempt = now
                try:
                    payload = fetch_weather()
                    self.payload = payload
                    self.saved_at = jst_now()
                    self.saved_mono = time.monotonic()
                    self.error = ""
                except WeatherUnavailable as exc:
                    self.error = str(exc)
            stale = self.payload is not None and bool(self.error)
            return self.payload, self.saved_at, stale, self.error


weather_cache = WeatherCache()


def rain_slots(forecast, date):
    """6時間の発生確率は計算できないため、時間別の雨・雪の確率の最大値を表示。"""
    by_hour = {}
    hours = forecast.get("hour", [])
    for item in hours if isinstance(hours, list) else []:
        item = as_dict(item)
        try:
            stamp = dt.datetime.strptime(item.get("time", ""), "%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            continue
        if stamp.date() == date:
            by_hour[stamp.hour] = item
    slots = []
    for start in (0, 6, 12, 18):
        probabilities = []
        for hour in range(start, start + 6):
            entry = by_hour.get(hour, {})
            rain = number(entry.get("chance_of_rain"))
            snow = number(entry.get("chance_of_snow"))
            if (rain is not None and snow is not None and
                    0 <= rain <= 100 and 0 <= snow <= 100):
                probabilities.append(max(rain, snow))
        # 欠損を0%扱いしない。全6時間がそろった場合だけ表示。
        value = display_number(max(probabilities), "%") if len(probabilities) == 6 else "—"
        slots.append({"label": "{}時～{}時".format(start, start + 6), "value": value})
    return slots


def forecast_card(payload, date, title):
    days = as_dict(as_dict(payload).get("forecast")).get("forecastday", [])
    forecast = next((as_dict(d) for d in days if as_dict(d).get("date") == date.isoformat()), {})
    day = as_dict(forecast.get("day"))
    condition = as_dict(day.get("condition"))
    return {
        "title": title,
        "date": date.strftime("%m/%d"),
        "weather": condition.get("text") or "取得できません",
        "icon": icon_url(condition.get("icon")),
        "temp_max": display_number(day.get("maxtemp_c"), "℃"),
        "temp_min": display_number(day.get("mintemp_c"), "℃"),
        "slots": rain_slots(forecast, date),
    }


def page_context():
    payload, fetched_at, stale, error = weather_cache.get()
    today = jst_now().date()
    cards = [forecast_card(payload, today, "今日"),
             forecast_card(payload, today + dt.timedelta(days=1), "明日")]
    current = as_dict(as_dict(payload).get("current"))
    updated_text = "—"
    current_recent = False
    try:
        # epochはUTCの絶対時刻として扱い、画面では日本時間へ変換。
        updated = dt.datetime.fromtimestamp(float(current["last_updated_epoch"]), JST)
        updated_text = updated.strftime("%Y/%m/%d %H:%M")
        current_recent = -300 <= (jst_now() - updated).total_seconds() < MAX_CACHE_SECONDS
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        pass
    if not current_recent:
        current = {}
    state = "最新の取得結果"
    message = ""
    if payload is None:
        state = "天気情報を取得できません"
        message = "時間をおいて再取得します。"
    elif stale:
        state = "更新できないため、前回の取得結果を表示しています"
    elif not current_recent or any(c["temp_max"] == "—" or c["weather"] == "取得できません" for c in cards):
        state = "一部の情報を取得できません"
    return {
        "location_label": os.environ.get("WEATHER_LOCATION_LABEL", "富山市"),
        "cards": cards,
        "current": {
            "temp": display_number(current.get("temp_c"), "℃"),
            "humidity": display_number(current.get("humidity"), "%", 0, 100),
            "precip": display_number(current.get("precip_mm"), "mm", 0),
            "updated": updated_text,
            "unavailable": not current_recent,
        },
        "fetched_at": fetched_at.strftime("%Y/%m/%d %H:%M") if fetched_at else "—",
        "state": state,
        "message": message,
        "warning": payload is None or stale or state == "一部の情報を取得できません",
        "refresh_seconds": PAGE_REFRESH_SECONDS,
    }


def weather_page(template):
    response = make_response(render_template(template, **page_context()))
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/")
def web():
    return weather_page("index.html")


@app.route("/honsya")
def honsya():
    return weather_page("honsya.html")


@app.route("/healthz")
def healthz():
    # Renderの生存確認では外部APIを呼ばない。
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
