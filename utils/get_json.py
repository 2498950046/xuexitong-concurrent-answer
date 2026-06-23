

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re



def format_question(q):
    options = '\n'.join([f"{opt['letter']}. {opt['text']}" for opt in q['options']])
    return f"题目{q['id']} ({q['type']}):\n{q['text']}\n选项:\n{options}"
