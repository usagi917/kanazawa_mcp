from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json
from typing import List, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai

# 環境変数の読み込み
load_dotenv()

# OpenAI APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Facility(BaseModel):
    id: int
    name: str
    summary: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tel: Optional[str] = None
    opening_hours: Optional[str] = None
    closed_days: Optional[str] = None
    fee: Optional[str] = None
    url: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

@app.get("/api/facilities", response_model=List[Facility])
async def get_facilities():
    """施設情報を取得するエンドポイント"""
    try:
        df = pd.read_csv('data/facilities.csv')
        facilities = df.to_dict('records')
        return facilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/facilities/{facility_id}", response_model=Facility)
async def get_facility(facility_id: int):
    """特定の施設情報を取得するエンドポイント"""
    try:
        df = pd.read_csv('data/facilities.csv')
        facility = df[df['id'] == facility_id].to_dict('records')
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        return facility[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """チャットのエンドポイント"""
    try:
        # 施設情報を取得
        df = pd.read_csv('data/facilities.csv')
        facilities = df.to_dict('records')
        
        # システムプロンプトの作成
        system_prompt = f"""
        あなたは金沢市の観光案内アシスタントです。
        以下の施設情報を使って、ユーザーの質問に答えてください。
        
        施設情報:
        {json.dumps(facilities, ensure_ascii=False, indent=2)}
        
        回答は以下の形式でお願いします：
        1. 結論（簡潔に）
        2. 補足情報（必要な場合）
        3. 提案（関連する施設や情報）
        """
        
        # GPTに質問を送信
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # 応答を返す
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 