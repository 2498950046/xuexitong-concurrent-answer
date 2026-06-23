from openai import OpenAI
import sys

# client = OpenAI(
#     api_key="sk-119af223a9044b809f2dfb4ce0959db8",
#     base_url="https://api.deepseek.com"
# )




def get_deepseek_answer(user_input):
    """
    调用DeepSeek API获取问题答案
    
    参数:
        user_input (str): 需要查询的问题文本
        
    返回:
        str: 生成的答案内容，失败时返回None
    """
    # 初始化客户端
    client = OpenAI(
        api_key="sk-119af223a9044b809f2dfb4ce0959db8",
        base_url="https://api.deepseek.com"
    )
    
    # 构建消息结构
    messages = [{"role": "user", "content": user_input}]
    
    try:
        # 发送流式请求
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            timeout=30
        )
        
        # 收集响应内容
        final_answer = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                delta_content = chunk.choices[0].delta.content
                # 实时输出流式响应
                sys.stdout.write(delta_content)
                sys.stdout.flush()
                final_answer += delta_content
        
        # 返回完整答案
        return final_answer.strip()
        
    except Exception as e:
        print(f"\n请求失败: {str(e)}")
        return None
        
    finally:
        # 确保关闭响应连接
        if 'response' in locals():
            try:
                response.close()
            except Exception as close_error:
                pass


# 使用示例
# if __name__ == "__main__":
#     question = """
# 以下问题你的回答必须遵守以下规则：题目序号和具体选项，例如(1.A /n 2.AC)


# 1[多选题]科学家对1994年发生的彗星撞击木星的天文现象进行了大量的观察研究和准确的预报, 说明()
# A.
# 世界是可以认识的

# B.
# 人类已经可以预测一切天文现象

# C.
# 人类对宇宙的认识在不断深化  

# 2[多选题]下列各项正确反映绝对真理与相对真理的关系的有(     )
# A.
# 相对真理是在一定条件下可以转化为绝对真理

# B.
# 任何相对真理中都包含着绝对真理的颗粒

# C.
# 绝对真理是由无数相对真理的总和构成的



# """
#     answer = get_deepseek_answer(question)
