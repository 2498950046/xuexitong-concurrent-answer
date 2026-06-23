import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 正确导入方式（假设你的模块中有这些函数）
# from login import login  # 从login.py导入login函数
# from start_browser import start_browser  # 从start_browser.py导入start_browser函数
# 答案列表（索引对应题号-1）


# def auto_select_answers(driver,question_ids,answers):
#     try:
#         # 遍历所有题目
#          for i, (q_id, answer) in enumerate(zip(question_ids, answers)):


            
#             # 定位题目容器
#             question_div = WebDriverWait(driver, 10).until(
#                 EC.presence_of_element_located((By.ID, q_id))
#             )
            
#             # 构建选项选择器（根据data属性精准定位）
#             option_selector = f"span[data='{answer}']"
#             target_option = question_div.find_element(By.CSS_SELECTOR, option_selector)
            
#             # 点击父级容器触发事件
#             answer_div = target_option.find_element(By.XPATH, "./ancestor::div[contains(@class, 'answerBg')]")
#             answer_div.click()
            
#             print(f"已选择第{(i+1)}题答案：{answer}")
            
#         # 提交试卷（根据实际按钮ID调整）
#         #submit_btn = WebDriverWait(driver, 10).until(
#         #    EC.element_to_be_clickable((By.CLASS_NAME, "btnJJ"))
#         #)
#         #submit_btn.click()
        
#     except Exception as e:
#         print(f"操作异常：{str(e)}")
#         driver.save_screenshot('error.png')

def auto_select_answers(driver, question_ids, answers):
    try:
        for i, (q_id, answer) in enumerate(zip(question_ids, answers)):
            # 定位题目容器
            question_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, q_id))
            )
            
            # 处理多选题逻辑（当答案长度>1时）
            if len(answer) > 1:
                # 依次点击每个选项字母（如"BC"拆分为"B"和"C"）
                for char in answer:
                    # 构建含字母的特征属性选择器[5,7](@ref)
                    option_selector = f"span[data='{char}']"
                    target_options = question_div.find_elements(By.CSS_SELECTOR, option_selector)
                    
                    if target_options:
                        # 点击选项的父级容器（根据网页结构适配）[6](@ref)
                        answer_div = target_options[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'answerBg')]")
                        #针对未选中的选项，避免重复选择
                        if "active" not in answer_div.get_attribute("class"):
                            answer_div.click()
                            print(f"第{i+1}题多选点击：{char}")
            
            # 处理单选题逻辑
            else:
                # 原单选处理逻辑优化
                option_selector = f"span[data='{answer}']"
                target_option = question_div.find_element(By.CSS_SELECTOR, option_selector)
                answer_div = target_option.find_element(By.XPATH, "./ancestor::div[contains(@class, 'answerBg')]")
                answer_div.click()
                print(f"已选择第{i+1}题答案：{answer}")

            # 添加题目间延迟防止操作过快
            time.sleep(0.5)
            
    except Exception as e:
        print(f"操作异常：{str(e)}")
        driver.save_screenshot('error.png')



# 配置参数
target_url = "https://passport2.chaoxing.com/login"
phone='13551296193'
password='jiangyuhao1004'



# 使用示例
# if __name__ == "__main__":
#     driver = start_browser()
#     login_success = login(driver,target_url,phone, password)
#     #作业网址
#     url="https://mooc1.chaoxing.com/mooc-ans/mooc2/work/dowork?courseId=250185572&classId=115403087&cpi=352094458&workId=43399036&answerId=54354842&standardEnc=b675e5a1585f5c84344aa14478deef58&enc=30d4322fe4719073a85f9c794762a061"

#     driver.get(url)

#     auto_select_answers(driver)

