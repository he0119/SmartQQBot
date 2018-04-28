# -*- coding: utf-8 -*-
import json
import os
import platform
import shutil
import time

import requests
from requests import exceptions as excps

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from six.moves import http_cookiejar as cookielib
from smart_qq_bot.config import (COOKIE_FILE, DEFAULT_PLUGIN_CONFIG,
                                 SMART_QQ_REFER, SSL_VERIFY)
from smart_qq_bot.excpetions import ConfigFileDoesNotExist, ConfigKeyError
from smart_qq_bot.logger import logger


def _get_cookiejar(cookie_file):
    return cookielib.LWPCookieJar(cookie_file)


class HttpClient(object):

    # urllib2.install_opener(_req)

    def __init__(self, load_cookie=False, cookie_file=COOKIE_FILE):
        if not os.path.isdir(os.path.dirname(cookie_file)):
            os.mkdir(os.path.dirname(cookie_file))
        self._cookie_file = cookie_file
        self._cookies = _get_cookiejar(cookie_file)
        if load_cookie:
            self.load_cookie()
        self.session = requests.session()
        self.session.cookies = self._cookies

    @staticmethod
    def _get_headers(headers):
        """
        :type headers: dict
        :rtype: dict
        """
        _headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
            'Referer': 'http://s.web2.qq.com/proxy.html?v=20130916001&callback=1&id=1',
        }
        _headers.update(headers)
        return _headers

    def load_cookie(self):
        try:
            self._cookies.load(ignore_discard=True, ignore_expires=True)
        except :
            logger.warn("Failed to load cookie file {0}".format(self._cookie_file))
        finally:
            self._cookies.save(ignore_discard=True, ignore_expires=True)

    @staticmethod
    def get_timestamp():
        return str(int(time.time()*1000))

    def get(self, url, refer=None):
        try:
            resp = self.session.get(
                url,
                headers=self._get_headers({'Referer': refer or SMART_QQ_REFER}),
                verify=SSL_VERIFY,
            )
        except (excps.ConnectTimeout, excps.HTTPError):
            error_msg = "Failed to send finish request to `{0}`".format(
                url
            )
            logger.exception(error_msg)
            return error_msg
        except requests.exceptions.SSLError:
            logger.exception("SSL连接验证失败，请检查您所在的网络环境。如果需要禁用SSL验证，请修改config.py中的SSL_VERIFY为False")
        else:
            self._cookies.save(COOKIE_FILE, ignore_discard=True, ignore_expires=True)
            return resp.text

    def post(self, url, data, refer=None):
        try:
            resp = self.session.post(
                url,
                data,
                headers=self._get_headers({'Referer': refer or SMART_QQ_REFER}),
                verify=SSL_VERIFY,
            )
        except requests.exceptions.SSLError:
            logger.exception("SSL连接验证失败，请检查您所在的网络环境。如果需要禁用SSL验证，请修改config.py中的SSL_VERIFY为False")
        except (excps.ConnectTimeout, excps.HTTPError):
            error_msg = "Failed to send request to `{0}`".format(
                url
            )
            logger.exception(error_msg)
            return error_msg
        else:
            self._cookies.save(COOKIE_FILE, ignore_discard=True, ignore_expires=True)
            return resp.text

    def get_cookie(self, key):
        for c in self._cookies:
            if c.name == key:
                return c.value
        return ''

    def download(self, url, fname):
        with open(fname, "wb") as o_file:
            try:
                resp = self.session.get(url, stream=True, verify=SSL_VERIFY)
            except requests.exceptions.SSLError:
                logger.exception("SSL连接验证失败，请检查您所在的网络环境。如果需要禁用SSL验证，请修改config.py中的SSL_VERIFY为False")
            except (excps.ConnectTimeout, excps.HTTPError):
                error_msg = "Failed to send request to `{0}`".format(
                    url
                )
                logger.exception(error_msg)
                return error_msg
            else:
                self._cookies.save(COOKIE_FILE, ignore_discard=True, ignore_expires=True)
                o_file.write(resp.raw.read())

QQ = 'qq'
PASSWORD = 'password'
class ChromeClient(object):
    def __init__(self, no_gui, cookie_file=COOKIE_FILE, config_file=None):
        if not os.path.isdir(os.path.dirname(cookie_file)):
            os.mkdir(os.path.dirname(cookie_file))
        self._cookie_file = cookie_file
        self._cookies = _get_cookiejar(cookie_file)
        self._options = webdriver.ChromeOptions()
        if no_gui:
            self._options.add_argument("--headless")
            self._options.add_argument('--disable-gpu')
        #如果是Linux上则关掉sandbox
        if platform.system() == 'Linux':
            self._options.add_argument('--no-sandbox')
        self._driver = webdriver.Chrome(chrome_options=self._options)
        self.config = {
            QQ: '',
            PASSWORD: '',
        }
        self._load_config(config_file)

    def login(self):
        wait = WebDriverWait(self._driver, 20)
        logger.info('正在登录网页')
        self._driver.get('http://m.qzone.com')
        wait.until(EC.presence_of_element_located((By.ID, "go")))
        self._driver.find_element_by_id('u').clear()
        self._driver.find_element_by_id('u').send_keys(self.config[QQ])
        self._driver.find_element_by_id('p').clear()
        self._driver.find_element_by_id('p').send_keys(self.config[PASSWORD])
        self._driver.find_element_by_id('go').click()
        try:
            wait.until(EC.element_to_be_clickable((By.ID, 'header')))
            logger.info('登陆完成')
            time.sleep(5)
        except:
            try:
                iframe = self._driver.find_element_by_id(
                    'tcaptcha_iframe')    # 找到“嵌套”的iframe
                time.sleep(2)    # 等待资源加载
                self._driver.switch_to.frame(iframe)     # 切换到iframe
                logger.info('切换iframe')

                #等待滑条加载
                WebDriverWait(self._driver, 30).until(
                    EC.presence_of_element_located((By.ID, "tcaptcha_drag_button")))

                logger.info('处理验证滑条')
                button = self._driver.find_element_by_id(
                    'tcaptcha_drag_button')    # 找到“蓝色滑块”
                # 开始拖动 perform()用来执行ActionChains中存储的行为
                distance = 195
                offset = 5
                times = 0
                while True:
                    action = ActionChains(self._driver)
                    action.click_and_hold(button).perform()
                    action.reset_actions()  # 清除之前的action
                    logger.info(distance)
                    track = self._get_track(distance)
                    for i in track:
                        action.move_by_offset(xoffset=i, yoffset=0).perform()
                        action.reset_actions()
                    time.sleep(0.5)
                    action.release().perform()
                    time.sleep(5)

                    # 判断某元素是否被加载到DOM树里，并不代表该元素一定可见
                    try:
                        alert = self._driver.find_element_by_class_name(
                            'tcaptcha-title').text
                    except Exception as e:
                        logger.info('get alert error: %s' % e)
                        alert = ''
                    if alert:
                        logger.info('滑块位移需要调整: %s' % alert)
                        distance -= offset
                        times += 1
                        time.sleep(5)
                    else:
                        logger.info('滑块验证通过')
                        break
                wait.until(EC.element_to_be_clickable((By.ID, 'header')))
                logger.info('登陆完成')
            except:
                pass

        logger.info('尝试登录webqq')
        self._driver.get('http://web2.qq.com')
        try:
            self._driver.switch_to_frame('ptlogin')
            time.sleep(2)
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'face'))).click()
            time.sleep(2)
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'face'))).click()
        except:
            pass

        logger.info('正在验证登陆')
        self._driver.get('http://web2.qq.com')
        try:
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'face'))).click()
            logger.warn('需重新登陆')
        except:
            logger.info('登陆成功')

        session = requests.session()
        for item in self._driver.get_cookies():
            session.cookies.set(item['name'], item['value'])

        session.cookies.set(
            'ptwebqq', self._driver.execute_script('return mq.ptwebqq'))
        session.cookies.set(
            'vfwebqq', self._driver.execute_script('return mq.vfwebqq'))
        session.cookies.set(
            'psessionid', self._driver.execute_script('return mq.psessionid'))

        #登陆qun.qq.com
        # self._driver.get('http://qun.qq.com/')
        # wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'user-info'))).click()
        # time.sleep(2)
        # self._driver.switch_to_frame('login_frame')
        # time.sleep(2)
        # wait.until(EC.element_to_be_clickable(
        #     (By.ID, 'switcher_plogin'))).click()
        # wait.until(EC.presence_of_element_located((By.ID, "login_button")))
        # self._driver.find_element_by_id('u').clear()
        # self._driver.find_element_by_id('u').send_keys(self.config[QQ])
        # self._driver.find_element_by_id('p').clear()
        # self._driver.find_element_by_id('p').send_keys(self.config[PASSWORD])
        # self._driver.find_element_by_id('login_button').click()

        # time.sleep(10)
        # for item in self._driver.get_cookies():
        #     session.cookies.set(item['name'], item['value'])

        logger.debug(session.cookies)
        requests.utils.cookiejar_from_dict(
            {c.name: c.value for c in session.cookies}, self._cookies)
        self._driver.close()
        time.sleep(2)
        self._cookies.save(COOKIE_FILE, ignore_discard=True,
                           ignore_expires=True)
        return True

    @staticmethod
    def _get_track(distance):
        track = []
        current = 0
        mid = distance * 3 / 4
        t = 0.2
        v = 0
        while current < distance:
            if current < mid:
                a = 2
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        return track

    def _load_config(self, config_file):
        config = None
        if config_file is not None:
            # 指定了特定配置文件
            if os.path.isfile(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)
            else:
                raise ConfigFileDoesNotExist(
                    "Config file {} does not exist.".format(config_file)
                )
        elif os.path.isfile(DEFAULT_PLUGIN_CONFIG):
            # 存在配置文件
            with open(DEFAULT_PLUGIN_CONFIG, "r") as f:
                config = json.load(f)

        elif os.path.isfile(DEFAULT_PLUGIN_CONFIG + ".example"):
            # 不存在配置文件但有example文件
            shutil.copy(DEFAULT_PLUGIN_CONFIG +
                        ".example", DEFAULT_PLUGIN_CONFIG)
            logger.warning("No plugin config file found. Auto copied.")
            with open(DEFAULT_PLUGIN_CONFIG, "r") as f:
                config = json.load(f)
        else:
            # 缺少配置文件以及example文件
            exception_str = "Config file does not exist, please check the config path."
            logger.exception(exception_str)
            raise ConfigFileDoesNotExist(exception_str)

        self.config[QQ] = config[QQ]
        self.config[PASSWORD] = config[PASSWORD]
