from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from mcp.service import MCPService

app = FastAPI(title="金沢市 MCP API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCPサービスのインスタンス化
mcp_service = MCPService()

# リクエスト/レスポンスの型定義
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

class MCPToolRequest(BaseModel):
    tool_name: str
    params: Dict[str, Any]

class MCPToolResponse(BaseModel):
    result: Dict[str, Any]

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# MCPツール一覧取得
@app.get("/mcp/tools")
async def get_tools():
    return mcp_service.get_tools()

# MCPツール実行
@app.post("/mcp/execute", response_model=MCPToolResponse)
async def execute_tool(request: MCPToolRequest):
    try:
        result = await mcp_service.execute_tool(request.tool_name, request.params)
        return MCPToolResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# チャットエンドポイント
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # TODO: OpenAI APIを使用してMCPツールを呼び出す処理を実装
        return ChatResponse(
            answer="ご質問ありがとうございます！\n現在、APIの実装中です。\nもうしばらくお待ちください。"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 