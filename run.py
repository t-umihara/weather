from flask import Flask
from flask import render_template
import requests
from bs4 import BeautifulSoup
import time
import schedule
import datetime
import numpy as np

app = Flask(__name__)
alert = []

@app.route('/')
def web():
#HTML解析
    url = 'https://tenki.jp/forecast/4/19/5510/16201/'
    r = requests.get(url)
    bsObj = BeautifulSoup(r.content, "html.parser")
    today = bsObj.find(class_="today-weather")

#今日の天気の取得
    weather = today.p.string

#今日の気温の取得
    temp = today.div.find(class_="date-value-wrap")
    temp = temp.find_all("dd")
    temp_max = temp[0].span.string #最高気温
    temp_max_diff = temp[1].string #最高気温の前日比
    temp_min = temp[2].span.string #最低気温
    temp_min_diff = temp[3].string #最低気温の前日比

#今日の降水確率の取得
    precip = bsObj.find(class_="precip-table")
    precip = precip.find("tr", class_='rain-probability').find_all('td')
    precip_earlymorning = precip[0].text #00-06
    precip_morning = precip[1].text #06-12
    precip_noon = precip[2].text #12-18
    precip_afternoon = precip[3].text #18-24

#風向きの取得
    wind = bsObj.find(class_="precip-table")
    wind = wind.find("tr", class_='wind-wave').find_all('td')
    wind = wind[0].text

#明日の天気の取得
    tomorrow = bsObj.find(class_="tomorrow-weather")
    tomorrow_weather = tomorrow.p.string

#明日の気温の取得
    temp_tomorrow = tomorrow.div.find(class_="date-value-wrap")
    temp_tomorrow = temp_tomorrow.find_all("dd")
    temp_tomorrow_max = temp_tomorrow[0].span.string #最高気温
    temp_tomorrow_max_diff = temp_tomorrow[1].string #最高気温の前日比
    temp_tomorrow_min = temp_tomorrow[2].span.string #最低気温
    temp_tomorrow_min_diff = temp_tomorrow[3].string #最低気温の前日比

#明日の降水確率の取得
    precip = tomorrow.find(class_="precip-table")
    precip = precip.find("tr", class_='rain-probability').find_all('td')
    precip_earlymorning_tomorrow = precip[0].text #00-06
    precip_morning_tomorrow = precip[1].text #06-12
    precip_noon_tomorrow = precip[2].text #12-18
    precip_afternoon_tomorrow = precip[3].text #18-24

#明日の風向きの取得
    wind_tomorrow = tomorrow.find(class_="precip-table")
    wind_tomorrow = wind_tomorrow.find("tr", class_="wind-wave").find_all('td')
    wind_tomorrow = wind_tomorrow[0].text

#現在情報の取得(気温、湿度)
    nowurl = 'https://tenki.jp/live/4/19/'
    r = requests.get(nowurl)
    bsObj = BeautifulSoup(r.content, "html.parser")
    main_column = bsObj.find(class_="main-column")
    get_time = main_column.find("time", class_="date-time").text
    now_temp = main_column.find("td", class_="temp-entry").text
    now_humidity = main_column.find("td", class_="humidity-entry").text
    now_precip = main_column.find("td", class_="precip-entry").text

#index.htmlに送る変数の定義
    values = {"weather": weather, "temp_max": temp_max, "temp_max_diff": temp_max_diff, "temp_min": temp_min, "temp_min_diff": temp_min_diff, "get_time": get_time, 'now_temp': now_temp, 'now_humidity': now_humidity, 'now_precip': now_precip}
    precip = {"precip_earlymorning": precip_earlymorning, "precip_morning": precip_morning, "precip_noon": precip_noon, "precip_afternoon": precip_afternoon}
    wind = {'wind': wind}
    tomorrow = {"weather": tomorrow_weather, "temp_max": temp_tomorrow_max, "temp_max_diff": temp_tomorrow_max_diff, "temp_min": temp_tomorrow_min, "temp_min_diff": temp_tomorrow_min_diff}
    tomorrow_precip = {"precip_earlymorning_tomorrow": precip_earlymorning_tomorrow, "precip_morning_tomorrow": precip_morning_tomorrow, "precip_noon_tomorrow": precip_noon_tomorrow, "precip_afternoon_tomorrow": precip_afternoon_tomorrow}
    tomorrow_wind = {'wind_tomorrow': wind_tomorrow}
    icon = '/static/img/晴.png'
    icon = {'icon': icon}

#index.htmlに現在時刻を送るが、表示はしていない(サイネージのスライドだとズレが生じる)　日付だけだといいかも？
    now = datetime.datetime.now()
    now = "{0:%Y/%m/%d  %H:%M:%S}".format(now)
    now = {"now": now}

    return render_template('index.html', icon = icon, values = values, precip = precip, wind = wind, tomorrow = tomorrow, tomorrow_precip = tomorrow_precip, tomorrow_wind = tomorrow_wind, now = now)

@app.route('/honsya')
def honsya():
    #HTML解析
    url = 'https://tenki.jp/forecast/4/19/5510/16201/'
    r = requests.get(url)
    bsObj = BeautifulSoup(r.content, "html.parser")
    today = bsObj.find(class_="today-weather")

#今日の天気の取得
    weather = today.p.string

#今日の気温の取得
    temp = today.div.find(class_="date-value-wrap")
    temp = temp.find_all("dd")
    temp_max = temp[0].span.string #最高気温
    temp_max_diff = temp[1].string #最高気温の前日比
    temp_min = temp[2].span.string #最低気温
    temp_min_diff = temp[3].string #最低気温の前日比

#今日の降水確率の取得
    precip = bsObj.find(class_="precip-table")
    precip = precip.find("tr", class_='rain-probability').find_all('td')
    precip_earlymorning = precip[0].text #00-06
    precip_morning = precip[1].text #06-12
    precip_noon = precip[2].text #12-18
    precip_afternoon = precip[3].text #18-24

#風向きの取得
    wind = bsObj.find(class_="precip-table")
    wind = wind.find("tr", class_='wind-wave').find_all('td')
    wind = wind[0].text

#明日の天気の取得
    tomorrow = bsObj.find(class_="tomorrow-weather")
    tomorrow_weather = tomorrow.p.string

#明日の気温の取得
    temp_tomorrow = tomorrow.div.find(class_="date-value-wrap")
    temp_tomorrow = temp_tomorrow.find_all("dd")
    temp_tomorrow_max = temp_tomorrow[0].span.string #最高気温
    temp_tomorrow_max_diff = temp_tomorrow[1].string #最高気温の前日比
    temp_tomorrow_min = temp_tomorrow[2].span.string #最低気温
    temp_tomorrow_min_diff = temp_tomorrow[3].string #最低気温の前日比

#明日の降水確率の取得
    precip = tomorrow.find(class_="precip-table")
    precip = precip.find("tr", class_='rain-probability').find_all('td')
    precip_earlymorning_tomorrow = precip[0].text #00-06
    precip_morning_tomorrow = precip[1].text #06-12
    precip_noon_tomorrow = precip[2].text #12-18
    precip_afternoon_tomorrow = precip[3].text #18-24

#明日の風向きの取得
    wind_tomorrow = tomorrow.find(class_="precip-table")
    wind_tomorrow = wind_tomorrow.find("tr", class_="wind-wave").find_all('td')
    wind_tomorrow = wind_tomorrow[0].text

#現在情報の取得(気温、湿度)
    nowurl = 'https://tenki.jp/live/4/19/'
    r = requests.get(nowurl)
    bsObj = BeautifulSoup(r.content, "html.parser")
    main_column = bsObj.find(class_="main-column")
    get_time = main_column.find("time", class_="date-time").text
    now_temp = main_column.find("td", class_="temp-entry").text
    now_humidity = main_column.find("td", class_="humidity-entry").text
    now_precip = main_column.find("td", class_="precip-entry").text

#honsya.htmlに送る変数の定義
    values = {"weather": weather, "temp_max": temp_max, "temp_max_diff": temp_max_diff, "temp_min": temp_min, "temp_min_diff": temp_min_diff, "get_time": get_time, 'now_temp': now_temp, 'now_humidity': now_humidity, 'now_precip': now_precip}
    precip = {"precip_earlymorning": precip_earlymorning, "precip_morning": precip_morning, "precip_noon": precip_noon, "precip_afternoon": precip_afternoon}
    wind = {'wind': wind}
    tomorrow = {"weather": tomorrow_weather, "temp_max": temp_tomorrow_max, "temp_max_diff": temp_tomorrow_max_diff, "temp_min": temp_tomorrow_min, "temp_min_diff": temp_tomorrow_min_diff}
    tomorrow_precip = {"precip_earlymorning_tomorrow": precip_earlymorning_tomorrow, "precip_morning_tomorrow": precip_morning_tomorrow, "precip_noon_tomorrow": precip_noon_tomorrow, "precip_afternoon_tomorrow": precip_afternoon_tomorrow}
    tomorrow_wind = {'wind_tomorrow': wind_tomorrow}
    icon = '/static/img/晴.png'
    icon = {'icon': icon}

#honsya.htmlに現在時刻を送るが、表示はしていない(サイネージのスライドだとズレが生じる)　日付だけだといいかも？
    now = datetime.datetime.now()
    now = "{0:%Y/%m/%d  %H:%M:%S}".format(now)
    now = {"now": now}
    return render_template('honsya.html', icon = icon, values = values, precip = precip, wind = wind, tomorrow = tomorrow, tomorrow_precip = tomorrow_precip, tomorrow_wind = tomorrow_wind, now = now)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
    schedule.every(5).minute.do(web)
