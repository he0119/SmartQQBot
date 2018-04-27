'''掷骰子'''
import re
from random import randint

from smart_qq_bot.logger import logger
from smart_qq_bot.signals import on_group_message


@on_group_message(name="rand[随机数]")
def rand(msg, bot):
    match = re.match(r'^\/rand ?(\w*)?', msg.content)
    if match:
        args = match.group(1)
        str_data = '@{}'.format(msg.src_sender_name)

        probability = re.match(r'\w+(可能性|几率|概率)$', args)
        if probability:
            str_data += ' '
            str_data += args
            str_data += '是 '
            str_data += str(randint(0, 100))
            str_data += '%'
        else:
            str_data += ' 你的点数是 '
            str_data += str(randint(0, 100))

        bot.reply_msg(msg, str_data)
