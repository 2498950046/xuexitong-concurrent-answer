from __future__ import annotations

from utils.config import AppConfig
from utils.course import (
    click_homework_tab,
    enter_exercise,
    enter_iframe,
    enter_target_course,
    find_course_name,
    find_course_url,
    get_all_exercise,
    print_iframe,
    select_exercise_interactively,
    switch_to_target_iframe,
)
from utils.login import login
from utils.start_browser import start_browser


def main() -> int:
    print("正在读取配置...", flush=True)
    config = AppConfig.from_env()
    phone, password = config.require_login()
    print("配置读取完成，准备启动浏览器...", flush=True)
    driver = start_browser(config)

    try:
        print("浏览器启动完成，准备登录...", flush=True)
        if not login(driver, config.login_url, phone, password):
            return 1
        if not find_course_url(driver):
            return 1

        target_course = find_course_name(driver)
        if not enter_target_course(driver, target_course):
            return 1
        if not click_homework_tab(driver):
            return 1
        if not enter_iframe(driver):
            return 1

        exercises_info = get_all_exercise(driver)
        selected_info = select_exercise_interactively(exercises_info)
        if not selected_info:
            return 1

        print(f"准备进入: {selected_info['title']} (ID: {selected_info['activeid']})")
        return 0 if enter_exercise(driver, selected_info) else 1
    finally:
        print("执行完毕（浏览器保持打开）")


if __name__ == "__main__":
    raise SystemExit(main())
