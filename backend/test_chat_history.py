#!/usr/bin/env python3
"""
会話履歴機能のテストスクリプト
"""

import requests
import json
import uuid

# APIエンドポイント
API_URL = "http://localhost:8000/api/chat"

def test_chat_history():
    """会話履歴機能をテストする"""
    
    # セッションIDを生成
    session_id = str(uuid.uuid4())
    print(f"テスト用セッションID: {session_id}")
    print("=" * 50)
    
    # テスト会話のシナリオ
    test_conversations = [
        "こんにちは！金沢市について教えてください",
        "さっき質問した内容を覚えていますか？",
        "兼六園の営業時間を教えてください",
        "前に話した兼六園の話をもう少し詳しく聞かせて"
    ]
    
    for i, message in enumerate(test_conversations, 1):
        print(f"\n🗣️  メッセージ {i}: {message}")
        
        # APIリクエスト
        response = requests.post(
            API_URL,
            json={
                "query": message,
                "session_id": session_id
            },
            headers={
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 AI応答: {data['answer']}")
        else:
            print(f"❌ エラー: {response.status_code} - {response.text}")
        
        print("-" * 30)
    
    print(f"\n✅ 会話履歴テスト完了！（セッションID: {session_id}）")

if __name__ == "__main__":
    test_chat_history() 