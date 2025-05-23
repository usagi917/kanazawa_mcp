from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from mcp.service import MCPService
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
from database import SessionDep, create_tables
from models import ChatHistory
from sqlalchemy.orm import Session
import uuid

load_dotenv()

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベーステーブルの作成
create_tables()

app = FastAPI(
    title="金沢市 MCP API",
    description="金沢市の情報検索チャットボットAPI（会話履歴機能付き）",
    version="1.1.0"
)

# CORS設定（環境変数から設定）
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAIクライアントの初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MCPサービスのインスタンス化
mcp_service = MCPService()

# 会話履歴を取得する関数
def get_recent_chat_history(db: Session, session_id: str, limit: int = 3) -> List[Dict]:
    """指定されたセッションの最近の会話履歴を取得（前後3つまで）"""
    histories = db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.timestamp.desc()).limit(limit * 2).all()
    
    # 時系列順に並び替え
    histories.reverse()
    
    # メッセージ形式に変換
    messages = []
    for history in histories:
        if history.is_user_message:
            messages.append({"role": "user", "content": history.message})
        else:
            messages.append({"role": "assistant", "content": history.response})
    
    return messages

# 会話履歴を保存する関数  
def save_chat_history(db: Session, session_id: str, user_message: str, ai_response: str):
    """会話履歴をデータベースに保存"""
    # ユーザーメッセージを保存
    user_history = ChatHistory(
        session_id=session_id,
        message=user_message,
        response="",
        is_user_message=1
    )
    db.add(user_history)
    
    # AI応答を保存
    ai_history = ChatHistory(
        session_id=session_id,
        message="",
        response=ai_response,
        is_user_message=0
    )
    db.add(ai_history)
    db.commit()

# リクエスト/レスポンスの型定義
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # セッションIDを追加

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
    """アプリケーションの健康状態をチェック"""
    return {
        "status": "ok", 
        "message": "金沢市MCPサーバーは正常に動作しています",
        "version": "1.0.0"
    }

# MCPツール一覧取得
@app.get("/mcp/tools")
async def get_tools():
    """利用可能なMCPツールの一覧を取得"""
    return mcp_service.get_tools()

# MCPツール実行
@app.post("/mcp/execute", response_model=MCPToolResponse)
async def execute_tool(request: MCPToolRequest):
    """指定されたMCPツールを実行"""
    try:
        logger.info(f"MCPツール実行リクエスト: {request.tool_name}")
        result = await mcp_service.execute_tool(request.tool_name, request.params)
        return MCPToolResponse(result=result)
    except Exception as e:
        logger.error(f"MCPツール実行エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# チャットエンドポイント
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(SessionDep)):
    """チャットメッセージを処理してAI応答を生成"""
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="クエリが空です")

        # セッションIDがない場合は新規作成
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"チャットリクエスト: {query} (session: {session_id})")

        # 過去の会話履歴を取得
        chat_history = get_recent_chat_history(db, session_id, limit=3)

        # クエリの種類を判定してMCPツールを呼び出し
        system_prompt = "あなたは金沢市の親切な案内アシスタントです。過去の会話内容も参考にして、継続的で自然な会話をしてください。"
        context_info = ""

        if any(keyword in query for keyword in ["観光", "スポット", "見る", "遊ぶ"]):
            try:
                result = await mcp_service.execute_tool(
                    "search_tourist_spots", {"keyword": query, "limit": 5}
                )
                if result.get("spots"):
                    spots_text = "\n".join(
                        f"・{s['name']}: {s['description']}"
                        + (f" ({s['address']})" if s.get('address') else "")
                        for s in result["spots"]
                    )
                    context_info = f"参考となる観光スポット情報:\n{spots_text}"
                    system_prompt = "あなたは金沢市の観光案内の専門家です。以下の情報と過去の会話を参考に、親切で詳しい回答をしてください。"
            except Exception as e:
                logger.error(f"観光スポット検索エラー: {str(e)}")

        elif any(keyword in query for keyword in ["交通", "バス", "駅", "電車", "アクセス"]):
            try:
                # バス時刻表の検索かどうかを判定
                if any(k in query for k in ["時刻", "時間", "何時", "運行", "15時", "16時", "17時", "18時", "19時", "20時", "14時", "13時", "12時", "11時", "10時", "9時", "8時", "7時", "6時"]):
                    # 時間帯を抽出
                    import re
                    time_match = re.search(r'(\d{1,2})時', query)
                    time_range = None
                    if time_match:
                        hour = time_match.group(1)
                        time_range = f"{hour}:00"
                    
                    # 路線名を抽出
                    route_name = None
                    if "材木" in query:
                        route_name = "材木"
                    elif "此花" in query:
                        route_name = "此花"
                    elif "ふらっと" in query:
                        route_name = "ふらっとバス"
                    
                    result = await mcp_service.execute_tool(
                        "get_bus_schedule", 
                        {
                            "time_range": time_range,
                            "route_name": route_name,
                            "limit": 10
                        }
                    )
                    
                    if result.get("schedules"):
                        schedules_text = "\n".join(
                            f"・{s['departure_time']} - {s['route_name']} ({s['stop_name']} → {s['destination']}) [{s['bus_number']}]"
                            for s in result["schedules"]
                        )
                        context_info = f"金沢市バス時刻表（{time_range or '指定時間帯'}）:\n{schedules_text}"
                        system_prompt = "あなたは金沢市のバス時刻表の専門家です。以下の正確な時刻表情報と過去の会話を使用して、具体的で詳しい回答をしてください。"
                    else:
                        context_info = "申し訳ございません。該当する時刻表データが見つかりませんでした。"
                else:
                    # 一般的な交通情報検索
                    stop_type = "bus_stop" if any(k in query for k in ["バス", "バス停"]) else "train_station"
                    result = await mcp_service.execute_tool(
                        "get_transportation_info", {"type": stop_type}
                    )
                    if result.get("stops"):
                        stops_text = "\n".join(
                            f"・{s['name']} ({s['type']})"
                            + (f" - {s['address']}" if s.get('address') else "")
                            for s in result["stops"]
                        )
                        context_info = f"参考となる交通情報:\n{stops_text}"
                        system_prompt = "あなたは金沢市の交通案内の専門家です。以下の情報と過去の会話を参考に、親切で詳しい回答をしてください。"
            except Exception as e:
                logger.error(f"交通情報検索エラー: {str(e)}")

        elif any(keyword in query for keyword in ["ごみ", "ゴミ", "廃棄", "収集"]):
            context_info = "ごみ収集については、お住まいの地区コードと日付をお教えいただければ、詳しい収集スケジュールをお調べできます。"
            system_prompt = "あなたは金沢市のごみ収集案内の専門家です。過去の会話と合わせて親切で詳しい回答をしてください。"

        # OpenAI APIを使用してレスポンス生成
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if context_info:
            messages.append({"role": "system", "content": context_info})
        
        # 過去の会話履歴を追加
        messages.extend(chat_history)
        
        # 現在のユーザーメッセージを追加
        messages.append({"role": "user", "content": query})

        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )

        answer = response.choices[0].message.content
        logger.info(f"AI応答生成完了: {len(answer)}文字")
        
        # 会話履歴をデータベースに保存
        save_chat_history(db, session_id, query, answer)
        
        return ChatResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チャット処理エラー: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="申し訳ございません。一時的にサービスが利用できません。しばらく後でお試しください。"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 