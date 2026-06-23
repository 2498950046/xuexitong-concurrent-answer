from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re


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
            for option in option_elements:
                option_letter = option.find_element(By.CSS_SELECTOR, "span.num_option").get_attribute("data")
                # option_text = option.find_element(By.CSS_SELECTOR, "div.answer_p p").text
                # 使用更通用的文本提取方式
                option_text = option.find_element(By.CSS_SELECTOR, "div.answer_p").get_attribute("textContent").strip()
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