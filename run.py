from flask import Flask
from flask import render_template
import requests
from bs4 import BeautifulSoup
from mutagen.mp3 import MP3 as mp3
import pygame
import time
import schedule
import datetime
from PIL import Image, ImageFilter
# import cv2
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

#今日の気温・降水量ランキング
    rank = bsObj.find(class_="common-amedas-ranking-parts")
    rank = rank.find(class_="common-amedas-ranking-temp common-amedas-ranking-box")
    rank = rank.find(class_="ranking").text
    precip_rank = bsObj.find(class_="common-amedas-ranking-parts")
    precip_rank = precip_rank.find(class_="common-amedas-ranking-precip common-amedas-ranking-box")
    precip_rank = precip_rank.find(class_="ranking").text

#今日の降水確率の取得
    precip = bsObj.find(class_="precip-table")
    precip = precip.find("tr", class_='rain-probability').find_all('td')
    precip_earlymorning = precip[0].text #00-06
    precip_morning = precip[1].text #06-12
    precip_noon = precip[2].text #12-18
    precip_afternoon = precip[3].text #18-24

#今日の降水量の取得
    amedas = bsObj.find(class_="common-amedas-ranking-parts")
    fall = amedas.find(class_="common-amedas-ranking-precip common-amedas-ranking-box").find_all('li')
    precip_amount = fall[0].text
    precip_amount = precip_amount.strip("降水量")

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

#災害情報の取得
    city = []
    #alert = []
    warnurl = 'https://tenki.jp/bousai/warn/4/19/'
    r = requests.get(warnurl)
    bsObj = BeautifulSoup(r.content, "html.parser")
    main = bsObj.find(class_="main-column")
    cityname = main.find_all("th", class_="map-warn-point")
    alertname = main.find_all('p', class_='warn-kind-entries')
    alert_toyama_prefecture = main.find("div", class_="map-warn-pref-entries").find_all("p")
    alert_toyama_prefecture = alert_toyama_prefecture[0].text

#各市町村の名前と注意報の取得
    k = 0
    for set_city in range(15):
        city.append(cityname[k].text)
        alert.append(alertname[k].text)
        k = k + 1

#警報が出た市町村を塗りつぶす
    # height = 600
    # width = 600
    # k = 0
    # i = 40
    # img = cv2.imread('static/img/map/toyama_prefecture.png', cv2.IMREAD_COLOR)
    # #富山市(40,250,40),舟橋村(41,250,40),上市町(42,250,40),立山町(43,250,40),魚津市(44,250,40)
    # #滑川市(45,250,40),黒部市(46,250,40),入善町(47,250,40),朝日町(48,250,40),高岡市(49,250,40)
    # #氷見市(50,250,40),小矢部市(51,250,40),射水市(52,250,40),砺波市(53,250,40),南砺市(54,250,40)
    # for city in range(15):
    #     if(alert[k]) != '発表なし':
    #         for x in range(width):
    #             for y in range(height):
    #                 b, g, r = img[y,x]
    #                 if(b,g,r) == (i,250,40):
    #                     img[y,x] = (0,0,255)
    #     k = k + 1
    #     i = i + 1
    #
    # cv2.imwrite('static/img/map/alertmap.png', img)


#index.htmlに送る変数の定義
    values = {"weather": weather, "temp_max": temp_max, "temp_max_diff": temp_max_diff, "temp_min": temp_min, "temp_min_diff": temp_min_diff, "get_time": get_time, 'now_temp': now_temp, 'now_humidity': now_humidity, 'now_precip': now_precip}
    precip = {"precip_earlymorning": precip_earlymorning, "precip_morning": precip_morning, "precip_noon": precip_noon, "precip_afternoon": precip_afternoon}
    wind = {'wind': wind}
    tomorrow = {"weather": tomorrow_weather, "temp_max": temp_tomorrow_max, "temp_max_diff": temp_tomorrow_max_diff, "temp_min": temp_tomorrow_min, "temp_min_diff": temp_tomorrow_min_diff}
    tomorrow_precip = {"precip_earlymorning_tomorrow": precip_earlymorning_tomorrow, "precip_morning_tomorrow": precip_morning_tomorrow, "precip_noon_tomorrow": precip_noon_tomorrow, "precip_afternoon_tomorrow": precip_afternoon_tomorrow}
    tomorrow_wind = {'wind_tomorrow': wind_tomorrow}
    warning = {'warning': alert_toyama_prefecture}
    warning_city = {'toyama': alert[0], 'hunahasi': alert[1], 'kamichi': alert[2], 'tateyama': alert[3], 'uodu': alert[4], 'namerikawa': alert[5], 'kurobe': alert[6], 'nyuzen': alert[7], 'asahi': alert[8], 'takaoka': alert[9], 'himi': alert[10], 'oyabe': alert[11], 'imizu': alert[12], 'tonami': alert[13], 'nanto': alert[14]}
    icon = '/static/img/晴.png'
    icon = {'icon': icon}
    precip_amount = {'precip_amount': precip_amount}
    rank = {'rank': rank}
    precip_rank = {'precip_rank': precip_rank}

#index.htmlに現在時刻を送るが、表示はしていない(サイネージのスライドだとズレが生じる)　日付だけだといいかも？
    now = datetime.datetime.now()
    now = "{0:%Y/%m/%d  %H:%M:%S}".format(now)
    now = {"now": now}

    return render_template('index.html', icon = icon, values = values, precip = precip, wind = wind, tomorrow = tomorrow, tomorrow_precip = tomorrow_precip, tomorrow_wind = tomorrow_wind, warning = warning, warning_city = warning_city, precip_amount = precip_amount, rank = rank, precip_rank = precip_rank, now = now)

@app.route('/alertmap')
def map():
#災害情報の取得
    city = []
    #alert = []
    warnurl = 'https://tenki.jp/bousai/warn/4/19/'
    r = requests.get(warnurl)
    bsObj = BeautifulSoup(r.content, "html.parser")
    main = bsObj.find(class_="main-column")
    cityname = main.find_all("th", class_="map-warn-point")
    alertname = main.find_all('p', class_='warn-kind-entries')
    alert_toyama_prefecture = main.find("div", class_="map-warn-pref-entries").find_all("p")
    alert_toyama_prefecture = alert_toyama_prefecture[0].text

#alertmap.htmlに送る変数の定義
    warning_city = {'toyama': alert[0], 'hunahasi': alert[1], 'kamichi': alert[2], 'tateyama': alert[3], 'uodu': alert[4], 'namerikawa': alert[5], 'kurobe': alert[6], 'nyuzen': alert[7], 'asahi': alert[8], 'takaoka': alert[9], 'himi': alert[10], 'oyabe': alert[11], 'imizu': alert[12], 'tonami': alert[13], 'nanto': alert[14]}
    return render_template('alertmap.html', warning_city = warning_city)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
    schedule.every(5).minute.do(web)



    # im = Image.open('C:/Python/weather/晴れ.jpg')
    # print(im.format, im.size, im.mode)
