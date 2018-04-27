'''获取B站番剧的今日更新'''
import json
import re

import requests

from smart_qq_bot.logger import logger
from smart_qq_bot.signals import on_all_message


@on_all_message(name="bilibili[今日番剧表]")
def bilibili_today(msg, bot):
    match = re.match(r'^\/bilibili', msg.content)
    if match:
        try:
            output = ''
            response = requests.get(
                "https://bangumi.bilibili.com/web_api/timeline_global")
            data = response.content.decode('utf-8')
            rjson = json.loads(data)
            for day in rjson['result']:
                if(day['is_today'] == 1):
                    for item in day['seasons']:
                        output += item['pub_time'] + " : " + item['title'] + "\n"
            bot.reply_msg(msg, output)
        except:
            bot.reply_msg(msg, "获取番剧信息失败了~>_<~")
