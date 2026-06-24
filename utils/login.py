from __future__ import annotations

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def login(driver, url: str, phone: str, password: str, timeout: int = 10) -> bool:
    if not url:
        raise ValueError("login url is required")
    if not phone:
        raise ValueError("phone is required")
    if not password:
        raise ValueError("password is required")

    try:
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "phone"))
        ).send_keys(phone)
        driver.find_element(By.ID, "pwd").send_keys(password)
        driver.find_element(By.ID, "loginBtn").click()

        WebDriverWait(driver, timeout).until(EC.url_contains("mooc"))
        print("登录成功! 当前URL:", driver.current_url)
        return True
    except TimeoutException as exc:
        print(f"登录超时: {exc}")
        return False
    except WebDriverException as exc:
        print(f"登录失败: {exc}")
        return False
