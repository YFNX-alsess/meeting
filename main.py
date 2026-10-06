import os
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. 加载 .env 文件里的环境变量
load_dotenv()

# 2. 从环境变量中读取，而不是硬编码
DIFY_API_KEY = os.getenv("DIFY_API_KEY")
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL")

# 检查是否读取成功（调试用）
if not DIFY_API_KEY:
    print("❌ 错误：没有找到 DIFY_API_KEY，请检查 .env 文件！")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法（包含 POST）
    allow_headers=["*"], # 允许所有请求头
)

# 定义前端发来的数据格式
class ChatRequest(BaseModel):
    query: str

@app.post("/api/chat")
async def chat_with_dify(request: ChatRequest):
    # 这里就是把你阶段一跑通的代码搬过来，封装成接口
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {},
        "query": request.query,
        "response_mode": "blocking",
        "user": "web-user-001"
    }
    
    response = requests.post(f"{DIFY_BASE_URL}/chat-messages", headers=headers, json=payload)
    
    if response.status_code == 200:
        result_json = response.json()
        # 安全地提取回答，如果没找到 answer 字段，就返回一段提示
        answer = result_json.get("answer", "（Dify 没有返回文本内容）")
        return {"reply": answer}
    else:
        # ⚠️ 确保这里有打印真实错误的代码
        print(f"❌ Dify 接口报错！状态码：{response.status_code}")
        print(f"❌ 错误详情：{response.text}")
        return {"reply": f"Dify报错了！状态码：{response.status_code}，错误信息：{response.text}"}