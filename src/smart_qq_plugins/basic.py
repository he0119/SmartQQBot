# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
from random import randint

from smart_qq_bot.logger import logger
from smart_qq_bot.signals import on_group_message


# =====复读插件=====
class Recorder(object):
    def __init__(self):
        self.last_message_on = datetime.utcnow()

recorder = Recorder()


def is_repeat(recorder, msg):
    if msg.src_group_name != '圆环之理':
        return False
    #[群消息]blabla
    match = re.match(r'^\[\w+\]\w+', msg.content)
    if match:
        return False
    rand = randint(1, 100)
    logger.debug(rand)
    if rand > 15:
        return False
    time = recorder.last_message_on
    if datetime.utcnow() < time + timedelta(minutes=1):
        return False

    recorder.last_message_on = datetime.utcnow()
    return True

@on_group_message(name='basic[人类本质]')
def repeat(msg, bot):
    global recorder
    if is_repeat(recorder, msg):
        bot.reply_msg(msg, msg.content)


@on_group_message(name='basic[三个问题]')
def nick_call(msg, bot):
    if "/我是谁" == msg.content:
        bot.reply_msg(msg, "你是{}!".format(msg.src_sender_card or msg.src_sender_name))

    elif "/我在哪" == msg.content:
        bot.reply_msg(msg, "你在{name}!".format(name=msg.src_group_name))

    elif msg.content in ("/我在干什么", "/我在做什么"):
        bot.reply_msg(msg, "你在调戏我!!")
