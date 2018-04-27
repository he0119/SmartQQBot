# coding:utf-8

import json
import logging
import re
import urllib

import requests

from smart_qq_bot.logger import logger
from smart_qq_bot.signals import on_all_message


@on_all_message(name="weather[天气]")
def weather(msg, bot):
    match = re.match(r'^\/天气 ?(\w*)?', msg.content)
    if match:
        city = match.group(1)
        str_data = weather_old(city)
        if not str_data:
            str_data = weather_extend(city)
        if not str_data:
            str_data = "我才不是因为不知道才不告诉你{}的天气呢".format(city)
        bot.reply_msg(msg, str_data)


KEY1 = '31662bc776555612e3639dbca1ad1fd5'


def weather_old(city):
    '''百度天气'''
    try:
        city_name = urllib.parse.quote(city.encode('utf-8'))
        url_str = "http://api.map.baidu.com/telematics/v3/weather?location={city}&ak={key}&output=json".format(
            city=city_name,
            key=KEY1
        )
        response = requests.get(url_str)
        data = response.content.decode('utf-8')
        json_result = json.loads(data)['results'][0]

        str_data = ''
        str_data += json_result['currentCity'] + \
            " PM:" + json_result['pm25'] + "\n"
        try:
            str_data += json_result["index"][0]['des'] + "\n"
        except:
            pass

        for data in json_result["weather_data"]:
            str_data += data['date'] + " "
            str_data += data['weather'] + " "
            str_data += data['wind'] + " "
            str_data += data['temperature']
            str_data += '\n'

        return str_data
    except Exception as e:
        logging.exception(e)
        return None


KEY2 = '6ff5a040195245328b3cdc693d1c0bb2'


def weather_extend(city):
    '''
    和风天气API
    中国 长沙 PM:74
    建议着薄外套、开衫牛仔衫裤等服装。年老体弱者应适当添加衣物，宜着夹克衫、薄毛衣等。
    周四 04月26日 (实时：16℃) 阵雨转多云 西北风微风 20 ~ 15℃
    周五 多云 东北风微风 27 ~ 17℃
    周六 多云转雷阵雨 南风微风 28 ~ 21℃
    周日 阵雨 南风微风 25 ~ 21℃
    '''
    try:
        city_name = urllib.parse.quote(city.encode('utf-8'))
        url_str = "https://free-api.heweather.com/s6/weather?location={city}&key={key}".format(
            city=city_name,
            key=KEY2
        )
        response = requests.get(url_str)
        data = response.content.decode('utf-8')
        weather_result = json.loads(data)['HeWeather6'][0]
        weather_basic = weather_result['basic']

        str_data = weather_basic['cnty'] + ' ' + \
            weather_basic['location']  # 中国 成都

        return str_data
    except Exception as e:
        logging.exception(e)
        return None
