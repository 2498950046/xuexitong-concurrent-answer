
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re



def start_browser():
# 启动浏览器
    service = Service(executable_path="F:/tools/chromedriver-win64/chromedriver-win64/chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # 关键：浏览器不自动关闭
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用无关日志
    driver = webdriver.Chrome(service=service, options=options)
    return driver




