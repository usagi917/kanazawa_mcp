from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="金沢市 MCP API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエスト/レスポンスの型定義
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# チャットエンドポイント
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # TODO: MCPプロトコルでの処理を実装
        return ChatResponse(
            answer="ご質問ありがとうございます！\n現在、APIの実装中です。\nもうしばらくお待ちください。"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 