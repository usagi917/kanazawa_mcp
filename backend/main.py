from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from mcp.service import MCPService
import openai

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
        query = request.query
        if "観光" in query:
            result = await mcp_service.execute_tool(
                "search_tourist_spots", {"keyword": query, "limit": 5}
            )
            spots_text = "\n".join(
                f"{s['name']} - {s['description']}" for s in result.get("spots", [])
            )
            system_prompt = (
                "あなたは金沢市の観光案内アシスタントです。以下の観光スポット情報を参考に回答してください。\n"
                + spots_text
            )
        elif "交通" in query or "バス" in query or "駅" in query:
            stop_type = "bus_stop" if "バス" in query else "train_station"
            result = await mcp_service.execute_tool(
                "get_transportation_info", {"type": stop_type}
            )
            stops_text = "\n".join(
                f"{s['name']}({s['type']})" for s in result.get("stops", [])
            )
            system_prompt = (
                "あなたは金沢市の交通案内アシスタントです。以下の交通情報を参考に回答してください。\n"
                + stops_text
            )
        else:
            system_prompt = "あなたは金沢市の案内アシスタントです。"

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        answer = response.choices[0].message.content
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 