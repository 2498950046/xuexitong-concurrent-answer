

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re








def login(driver,url,phone,password):
     # 登录流程
    try:
        # 访问目标网址
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "phone"))).send_keys(phone)
        driver.find_element(By.ID, "pwd").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()

    # 等待登录完成
        WebDriverWait(driver, 10).until(EC.url_contains("mooc"))
        print("登录成功!当前URL:", driver.current_url)
        return True
    except Exception as e:
        print(f"登录失败: {str(e)}")
        return False
