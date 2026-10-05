import requests
import json

# 1. 配置你的凭证
API_KEY = "app-4wNmoZB0KybZ4xUyX9H6469H" # 替换为你刚才复制的 API Key
BASE_URL = "http://localhost/v1" # 替换为你的 Dify 地址
USER_ID = "abc-123" # 随便填一个唯一标识用户的字符串即可

# 2. 设置请求头 (Headers) - 用于鉴权
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 3. 准备请求数据 (Payload)
payload = {
    "inputs": {}, # 如果你的应用有自定义变量，在这里填入，没有就留空字典
    "query": "你好，请用一句话介绍一下你自己。", # 你要问的问题
    "response_mode": "blocking", # 关键：blocking 代表非流式（等全部生成完再返回）
    "user": USER_ID
}

# 4. 发送 POST 请求
print("正在向 Dify 发送请求...")
response = requests.post(f"{BASE_URL}/chat-messages", headers=headers, json=payload)

# 5. 处理返回结果
if response.status_code == 200:
    result = response.json()
    # 提取 Dify 的回答
    answer = result.get("answer")
    print("\n--- Dify 回答 ---")
    print(answer)
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)