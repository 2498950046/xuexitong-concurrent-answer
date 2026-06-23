# import requests
# from bs4 import BeautifulSoup

# url = "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/dowork?courseId=250185572&classId=115403087&cpi=352094458&workId=43395011&answerId=54348093&standardEnc=52985879a5bed07b872cd265450dc68e&enc=061d4f1d125b134e493a9bdf740b7402"  # 替换为实际题目页面URL

# # 获取网页内容
# response = requests.get(url)
# soup = BeautifulSoup(response.text, 'html.parser')

# # 查找所有题目容器
# questions = soup.find_all('div', class_='questionLi')

# # 遍历处理每个题目
# for question in questions:
#     # 提取题目信息
#     question_header = question.find('h3', class_='mark_name')
#     question_text = question_header.get_text(strip=True).replace('\n', ' ').replace('(单选题)', '').strip()
    
#     # 提取选项信息
#     options = []
#     for option in question.find_all('div', class_='answerBg'):
#         option_text = option.find('div', class_='answer_p').get_text(strip=True)
#         options.append(option_text)
    
#     # 打印结果
#     print(f"题目：{question_text}")
#     for idx, opt in enumerate(options, start=0):
#         print(f"{chr(65+idx)}. {opt}")
#     print("\n" + "-"*50 + "\n")






from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re
from utils.ai import*
import json

# 配置参数
target_url = "https://passport2.chaoxing.com/login"
phone='13551296193'
password='jiangyuhao1004'




def start_browser():
# 启动浏览器
    
    service = Service(executable_path=r"F:\tools\chromedriver-win64\chromedriver-win64\chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)  # 关键：浏览器不自动关闭
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用无关日志
    driver = webdriver.Chrome(service=service, options=options)
    return driver






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

#获取网页上的题
def get_questions(driver):
    """
    获取页面上的所有题目及其选项
    
    参数:
        driver: Selenium WebDriver 实例
        
    返回:
        list: 包含所有题目信息的列表，每个题目是一个字典
    """
    questions = []
    
    try:
        # 等待题目元素加载完成
        question_elements = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.questionLi"))
        )
        
        for question in question_elements:
            # 获取题目基本信息
            question_id = question.get_attribute("id")
            question_type = question.get_attribute("typename")
            
            # 获取题目文本
            question_text = question.find_element(By.TAG_NAME, "h3").text
            # 清理题目文本，移除序号和题型提示
            question_text = re.sub(r'^\d+\.\s*$.*?$\s*', '', question_text).strip()
            
            
            # 获取选项
            options = []
      
            option_elements = WebDriverWait(question, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.stem_answer div.answerBg"))
            )
            # for option in option_elements:
            #     option_letter = option.find_element(By.CSS_SELECTOR, "span.num_option").get_attribute("data")
            #     # option_text = option.find_element(By.CSS_SELECTOR, "div.answer_p p").text
            #     # 使用更通用的文本提取方式
            #     option_text = option.find_element(By.CSS_SELECTOR, "div.answer_p").get_attribute("textContent").strip()
            for idx, option in enumerate(option_elements):
                try:
                    if question_type == "多选题":
                        option_letter = option.find_element(By.CSS_SELECTOR, "span.num_option_dx").get_attribute("data")
                    else:
                        option_letter = option.find_element(By.CSS_SELECTOR, "span.num_option").get_attribute("data")

                    option_text = option.find_element(By.CSS_SELECTOR, "div.answer_p").text.strip()
                except Exception as e:
                    print(f"选项提取失败: {e}")
                    option_letter = chr(65 + idx)
                    option_text = ""

                options.append({
                    "letter": option_letter,
                    "text": option_text
                })
            


            # 构建题目字典
            questions.append({
                "id": question_id,
                "type": question_type,
                "text": question_text,
                "options": options
            })
            
        print(f"成功获取 {len(questions)} 道题目")
        return questions
        
    except Exception as e:
        print(f"获取题目失败: {str(e)}")
        return None


# def get_questions(driver):
#     questions = []
    
#     try:
#         question_elements = WebDriverWait(driver, 20).until(
#             EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "div.questionLi"))
#         )
        
#         for index, question in enumerate(question_elements):
#             # 滚动到题目元素确保可见
#             driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", question)
            
#             # 获取题目ID和类型
#             question_id = question.get_attribute("id")
#             question_type = question.get_attribute("typename")
            
#             # 优化题目文本提取
#             question_text = question.find_element(By.TAG_NAME, "h3").get_attribute("textContent")
#             # 使用更精确的正则表达式清理题目编号和题型
#             question_text = re.sub(r'^\d+\.\s*$.*?$\s*', '', question_text).strip()
            
#             # 优化选项提取逻辑
#             options = []
#             option_elements = WebDriverWait(question, 10).until(
#                 EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.stem_answer div.answerBg"))
#             )
#             for option in option_elements:
#                 try:
#                     option_letter = option.find_element(By.CSS_SELECTOR, "span.num_option").get_attribute("data")
#                     # 使用更通用的文本提取方式
#                     option_text = option.find_element(By.CSS_SELECTOR, "div.answer_p").get_attribute("textContent").strip()
#                 except Exception as opt_e:
#                     print(f"选项提取失败: {str(opt_e)}")
#                     option_text = ""
#                 options.append({
#                     "letter": option_letter,
#                     "text": option_text
#                 })
            
#             questions.append({
#                 "id": question_id,
#                 "type": question_type,
#                 "text": question_text,
#                 "options": options
#             })
            
#             # 增加题目间延迟确保加载
#             time.sleep(0.5)
        
#         print(f"成功获取 {len(questions)} 道题目")
#         return questions
        
#     except Exception as e:
#         print(f"获取题目失败: {str(e)}")
#         return None
    
def format_question(q):
    options = '\n'.join([f"{opt['letter']}. {opt['text']}" for opt in q['options']])
    return f"题目{q['id']} ({q['type']}):\n{q['text']}\n选项:\n{options}"


def batch_questions(questions, batch_size=20):
    for i in range(0, len(questions), batch_size):
        yield questions[i:i+batch_size]


if __name__ == "__main__":
    driver = start_browser()

    login_success = login(driver,target_url,phone, password)
    url = "https://mooc1.chaoxing.com/mooc-ans/mooc2/work/dowork?courseId=249843142&classId=116600873&cpi=352094458&workId=44449198&answerId=54316872&standardEnc=09f6c02bcf683c5dd47a342aa3fb40f8&enc=4d457e963138662699cfa70ca3e62f55"
    driver.get(url)
    # 在登录成功后调用
    if login_success:
        questions = get_questions(driver)
        # if questions:
        #     for i, q in enumerate(questions, 1):
        #         print(f"\n题目 {q['id']}: {q['text']}")
        #         print(f"题型: {q['type']}")
        #         print("选项:")
        #         for opt in q['options']:
        #             print(f"{opt['letter']}. {opt['text']}")
        

        # 构建符合要求的提问文本
        instruction = """你将接受不定数量的单选题和多选题，请严格按以下格式回答（只输出数组，不要输出任何解释或多余内容）：
["第一题答案","第二题答案","第三题答案",...]
例如：["A","BC","AC","AD","A",...]
以下是需要作答的题目："""




        # question_list = "\n\n".join([format_question(q) for q in questions])
        # full_prompt = f"{instruction}\n\n{question_list}"  # 组合指令和题目

        # # 调用API获取答案

        # print(full_prompt)

        # answer_str = get_deepseek_answer(full_prompt) ## 原始字符串（外层有单引号）外层有单引号包裹  '["B","B","A","B","C","B","B","A","C","B"]'
        # if not answer_str:
        #     print("获取答案失败，answer_str 为空！")
        #     exit(1)
        # try:
        #     answers = json.loads(answer_str)
        # except Exception as e:
        #     print(f"答案解析失败: {e}")
        #     exit(1)

        # # 准备数据
        # question_ids = [q["id"] for q in questions]  # 提取所有题目ID
        # answers =  json.loads(answer_str)  # 结果：["B", "B", "A", "B", "C", "B", "B", "A", "C", "B"]         # 答案列表（需与题目顺序一致）
        # # 点击选项
        # from utils.click_answer import *
        # auto_select_answers(driver,question_ids,answers)


        all_answers = []
        for batch in batch_questions(questions, batch_size=20):
            question_list = "\n\n".join([format_question(q) for q in batch])
            full_prompt = f"{instruction}\n\n{question_list}"
            print(full_prompt)  # 可选，调试用
            answer_str = get_deepseek_answer(full_prompt)
            if not answer_str:
                print("获取答案失败，answer_str 为空！")
                exit(1)
            try:
                answers = json.loads(answer_str)
                if len(answers) != len(batch):
                    print(f"警告：AI返回答案数量({len(answers)})与题目数量({len(batch)})不符！")
                all_answers.extend(answers)
            except Exception as e:
                print(f"答案解析失败: {e}")
                exit(1)

        print("所有答案：", all_answers)
        # 后续可直接用 all_answers 进行自动点击等操作
        question_ids = [q["id"] for q in questions]
        from utils.click_answer import *
        auto_select_answers(driver, question_ids, all_answers)




