








from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import re
from utils.start_browser import *
from utils.login import *
# 配置参数
login_url = "https://passport2.chaoxing.com/login"



phone='13551296193'
password='jiangyuhao1004'





#进入所有课程url
def find_course_url(driver):

    try:
            # 定位课程链接并获取URL
        course_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "zne_kc_icon"))
        )
       
        js_code = course_link.get_attribute("href")

        match = re.search(r"switchM\([^,]+,['\"](https?://[^'\"]+)", js_code)
        if match:
            url = match.group(1)
            print("提取的课程URL:", url)  # 输出: https://mooc1-1.chaoxing.com/visit/interaction?s=5c283e43c909cae404d066f1c761a912
            driver.get(url)
        else:
            print("未匹配到URL")

        WebDriverWait(driver, 10).until(EC.url_contains("mooc1-1"))
        print("进入课程成功，当前URL:", driver.current_url)

    except NoSuchElementException:
        print("未找到课程链接元素")
    except Exception as e:
        print(f"提取URL失败: {e}")


#加载课程名称，用户选择课程得到target_course
def find_course_name(driver):

    try:
        # 等待课程列表加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".course-name"))
        )
        
        # 获取所有课程名称元素
        course_names = driver.find_elements(By.CSS_SELECTOR, ".course-name")#course_names是一个WebElement 对象，
        
        print("\n所有课程列表:")
        for idx, course in enumerate(course_names, 1):
            print(f"{idx}. {course.text}")

        
        # 用户选择课程
        while True:
            try:
                choice = int(input("\n请输入要选择的课程编号: "))
                if 1 <= choice <= len(course_names):
                    target_course = course_names[choice-1].text      #.text	从 WebElement 中提取实际显示的课程名称（字符串）。
                    return target_course
                    
                else:
                    print(f"请输入有效的编号(1-{len(course_names)})")
            except ValueError:
                print("请输入数字编号")

    except TimeoutException:
        print("课程列表加载超时")
    except Exception as e:
        print(f"获取课程列表出错: {e}")




# 进入目标课程
def enter_target_course(driver,target_course):

    try:
        # 获取当前窗口句柄（原始窗口）
        original_window = driver.current_window_handle

        target_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//*[contains(@class, "course-name") and contains(text(), "{target_course}")]/ancestor::a'))
        )
        #点击该课程
        target_link.click()
        print(f"\n选择进入课程: {target_course}")

            # 等待新窗口出现并切换到新窗口
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        
        #获取新窗口的URL
        print("新窗口URL:", driver.current_url)

        # 验证是否成功进入（检查课程标题）
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//*[contains(text(), "{target_course}")]'))
        )
        print("成功进入该课程")


    except TimeoutException:
        print(f"\n错误：未找到课程 '{target_course}'")
    except Exception as e:
        print(f"\n其他错误: {e}")




#定位并点击"作业"标签
def click_homework_tab(driver):
    """
    定位并点击"作业"标签
    """
    try:
        # 等待导航栏加载完成
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".nav-content.stuNavigationList"))   #.nav-content.stuNavigationList 表示 ​同时具有这两个class的元素
        )
        
        # 定位"作业"标签（通过span文本内容）
        homework_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//span[@class="nav_content" and text()="作业"]'))
        )
        
        # 点击"作业"标签
        homework_tab.click()
        print("成功点击作业标签")
        

        
    except TimeoutException:
        print("查找或点击作业标签超时")
    except Exception as e:
        print(f"点击作业标签时出错: {e}")

# 打印当前所有iframe的层级关系
def print_iframe(driver):
       # 打印当前所有iframe的层级关系
    try:

       
        print("当前所有iframe的ID和名称:")
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            print(f"ID: {iframe.get_attribute('id')}, Name: {iframe.get_attribute('name')}")


        print("✅ iframe加载成功")
    except:
        print("❌ iframe加载超时")


# 进入iframe（默认第一个）
def enter_iframe(driver):


    try:

       
        iframes= driver.find_elements(By.TAG_NAME, "iframe")#find_elements返回的值是列表
        if not iframes:
            print("❌ 未找到任何iframe")
            return False
        
        # 获取第一个iframe
        first_iframe = iframes[0]
        print(f"ID: {first_iframe.get_attribute('id')}, Name: {first_iframe.get_attribute('name')}")


        # 显式等待iframe加载并切换（兼容动态加载场景）
        WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID,first_iframe.get_attribute('id')))
    )
        print("✅ 已切换到当前iframe")

        return True



    except Exception as e:
        print(f"❌ 切换iframe失败: {e}")
        driver.switch_to.default_content()  # 失败时切回主文档
        return False





#def get_all_exercise(driver):
    try:
        # 显式等待活动列表加载（更精准的XPath定位）
        section = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, 
            '//div[@class="bottomList"]/ul'))
    )
        

            # 精准获取随堂练习（activetype=42）
        exercises = section.find_elements(By.XPATH, './li')
        print(f"成功找到 {len(exercises)} 个练习")


        exercises_info = []  # 新增列表存储活动信息
         # 提取详细信息
        for idx, exercise in enumerate(exercises, 1):
            try:
            # 标题
                title = exercise.find_element(By.XPATH, './/p[contains(@class, "overHidden2")]').text.strip()
            
            # 结束时间
                time_element = exercise.find_element(By.XPATH, './/div[contains(@class, "time")]')
                end_time = time_element.text.replace("结束时间：", "").strip()
            
            # 活动类型（随堂练习）
                activity_type = "随堂练习" if exercise.get_attribute("activetype") == "42" else "其他活动"

            # 获取唯一标识
                active_id = exercise.get_attribute("activeid")  

                print(f"{idx}. {activity_type}: {title} (结束时间: {end_time}) {active_id}")
                 # 存储到信息字典
                exercises_info.append({
            "index": idx,
            "activeid": active_id,
            "title": title,
            "end_time": end_time
        })
            
            except Exception as e:
                print(f"解析第{idx}个练习时出错: {e}")

    except TimeoutException:
        print("⚠️ 未找到练习")


#得到所有练习，返回的是练习列表exercises_info ，其中每个exercises_info[i]对应一个item
'''
基础信息容器
                item = {
                    "index": idx,
                    "activeid": None,
                    "title": None,
                    "status": None,
                    "end_time": None,
                    "analysis_url": None
                }
'''
def get_all_exercise(driver):
    try:
        # 显式等待活动列表加载
        section = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="bottomList"]/ul'))
        )
        
        exercises = section.find_elements(By.XPATH, './li')
        print(f"成功找到 {len(exercises)} 个练习")

        exercises_info = []
        for idx, exercise in enumerate(exercises, 1):
            try:
                # 基础信息容器
                item = {
                    "index": idx,
                    "activeid": None,
                    "title": None,
                    "status": None,
                    "end_time": None,
                    "analysis_url": None
                }

                # 获取data属性中的workId (关键标识)
                data_url = exercise.get_attribute("data")
                if data_url:
                    item["activeid"] = data_url.split("workId=")[1].split("&")[0] if "workId=" in data_url else None

                # 标题提取
                title_element = exercise.find_element(By.XPATH, './/p[contains(@class, "overHidden2")]')
                item["title"] = title_element.text.strip()

                # 状态判断（优先status元素，其次time元素）
                try:
                    status_element = exercise.find_element(By.XPATH, './/p[contains(@class, "status")]')
                    item["status"] = status_element.text.strip()
                except:
                    time_element = exercise.find_element(By.XPATH, './/div[contains(@class, "time")]')
                    item["status"] = "进行中" if "剩余" in time_element.text else "未知状态"

                # 结束时间提取
                try:
                    time_element = exercise.find_element(By.XPATH, './/div[contains(@class, "time")]')
                    item["end_time"] = time_element.text.replace("剩余", "").replace("结束时间：", "").strip()
                except:
                    item["end_time"] = "无时间信息"

                # 智能分析链接
                try:
                    analysis_link = exercise.find_element(By.XPATH, './/a[contains(@class, "insightBtn")]')
                    item["analysis_url"] = analysis_link.get_attribute("href")
                except:
                    pass

                # 活动类型判断
                item["activity_type"] = "随堂练习" if "随堂练习" in item["title"] else "其他活动"

                # 打印并存储
                print(f"{idx}. [{item['activity_type']}] {item['title']}")
                print(f"   ▪ 状态: {item['status']} | 结束时间: {item['end_time']}")
                print(f"   ▪ 活动ID: {item['activeid']}")
                if item["analysis_url"]:
                    print(f"   ▪ 分析链接: {item['analysis_url']}")
                
                exercises_info.append(item)

            except Exception as e:
                print(f"解析第{idx}个练习时出错: {str(e)}")
                continue

        return exercises_info

    except TimeoutException:
        print("⚠️ 未找到练习列表")
        return []
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        return []


#总过程
try:
    
    # 启动浏览器
    driver=start_browser()
    # 登录流程
    login_success = login(driver,login_url,phone, password)

    # # 切换到课程列表iframe（如果存在）
    # try:
    #     iframe = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[name='frame_content']"))
    #     )
    #     driver.switch_to.frame(iframe)
    #     print("已切换到课程列表iframe")
    # except:
    #     print("未找到课程列表iframe，继续主页面操作")

    #进入所有课程页面
    find_course_url(driver)

    #加载课程名称
    target_course=find_course_name(driver)


    # 进入目标课程
    enter_target_course(driver,target_course)    



    click_homework_tab(driver)

    enter_iframe(driver)





    exercises_info=get_all_exercise(driver)




    # 用户交互模块
    while True:
        try:
            selected = int(input(f"请输入要查看的练习序号 (1-{len(exercises_info)}): "))
            if 1 <= selected <= len(exercises_info):
                selected_info = exercises_info[selected-1]
                print(f"准备进入：{selected_info['title']} (ID: {selected_info['activeid']})")


                # 元素定位与点击

                # 使用保存的activeid重新定位
                target_xpath = f'//div[@class="bottomList"]/ul/li[contains(@data, "workId={selected_info["activeid"]}")]'

    
                # 显式等待元素可点击
                target_element = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, target_xpath))
                )
                target_element.click()
                print("✅ 成功进入该练习页")
                break
            else:
                print("⚠️ 序号超出范围，请重新输入")
        except ValueError:
            print("⚠️ 请输入有效数字")
        except TimeoutException as e:
            print(f"❌ 页面跳转超时: {str(e)}")
        except Exception as e:
            print(f"❌ 发生未预期错误: {str(e)}")





    

# # 等待iframe内至少有一个有效元素
#     try:
#         WebDriverWait(driver, 15).until(
#         lambda d: d.find_elements(By.XPATH, "//*[text()]")  # 查找任何包含文本的元素
#     )
#         print("✅ 成功进入练习详情页")
#         # # 打印当前iframe的HTML
#         # print(driver.page_source)
#     except TimeoutException:
#         print("⚠️ iframe内容为空或未加载")



finally:
    print("执行完毕（浏览器保持打开）")






def switch_to_target_iframe(driver):
    try:
        # 确保回到主文档
        driver.switch_to.default_content()

        # 方案1：直接通过ID定位（优先尝试）
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "frame_content-hd"))
            )
            driver.switch_to.frame(iframe)
            print("✅ 通过ID定位切换到iframe")
            return True
        except:
            pass

        # 方案2：通过名称定位
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "frame_content-hd"))
            )
            driver.switch_to.frame(iframe)
            print("✅ 通过Name定位切换到iframe")
            return True
        except:
            pass

        # 方案3：通过XPath模糊匹配
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, 'frame_content')]"))
            )
            driver.switch_to.frame(iframe)
            print("✅ 通过XPath模糊匹配切换到iframe")
            return True
        except:
            pass

        # 所有方案均失败
        print("❌ 所有定位方式均失败，请检查以下内容：")
        print("1. 页面是否包含目标iframe")
        print("2. iframe是否被动态加载或隐藏")
        print("3. 是否需先切换到其他iframe")
        return False

    except Exception as e:
        print(f"切换iframe时发生错误: {e}")
        return False

