"""
金沢AI助手 - メインFlaskアプリケーション
金沢市のオープンデータを活用したチャットボットAPI
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import httpx
from openai import OpenAI
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

app = Flask(__name__, 
           template_folder='../frontend',
           static_folder='../static')
CORS(app)

# OpenAI クライアント設定
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class KanazawaDataAPI:
    """金沢市オープンデータAPIクライアント"""
    
    def __init__(self):
        self.base_url = "https://catalog-data.city.kanazawa.ishikawa.jp/api/3"
        self.timeout = 10.0
    
    async def search_datasets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """データセットを検索"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/action/package_search",
                    params={
                        "q": query,
                        "rows": limit,
                        "sort": "score desc"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # dataがNoneまたは空の場合の処理
                if not data:
                    print(f"データセット検索: 空のレスポンス (query: {query})")
                    return []
                
                result = data.get("result")
                if not result:
                    print(f"データセット検索: resultが見つからない (query: {query})")
                    return []
                
                results = result.get("results", [])
                print(f"データセット検索成功: {len(results)}件 (query: {query})")
                return results
                
        except Exception as e:
            print(f"データセット検索エラー: {e}")
            return []
    
    async def get_dataset_detail(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """データセットの詳細情報を取得"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/action/package_show",
                    params={"id": dataset_id}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("result")
        except Exception as e:
            print(f"データセット詳細取得エラー: {e}")
            return None
    
    async def get_resource_data(self, resource_url: str) -> Optional[str]:
        """リソースデータを取得（CSV/JSONなど）"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(resource_url)
                response.raise_for_status()
                return response.text[:5000]  # 最初の5000文字のみ
        except Exception as e:
            print(f"リソースデータ取得エラー: {e}")
            return None

class KanazawaAI:
    """金沢AI助手 - OpenAI GPTを使用した質問応答システム"""
    
    def __init__(self):
        self.data_api = KanazawaDataAPI()
        self.system_prompt = """
あなたは金沢市の情報に詳しいAI助手です。
金沢市のオープンデータを活用して、市民の質問に親切で分かりやすく答えてください。

回答の際は以下を心がけてください：
- 正確で最新の情報を提供する
- 分かりやすい日本語で説明する
- 具体的な数値やデータがある場合は積極的に活用する
- 情報源を明記する
- 不明な点は素直に「分からない」と答える

金沢市の魅力や観光情報、行政サービス、統計データなど幅広く対応してください。
"""
    
    async def generate_response(self, user_question: str) -> Dict[str, Any]:
        """ユーザーの質問に対してAI応答を生成"""
        try:
            print(f"質問受信: {user_question}")
            
            # 関連データセットを検索
            datasets = await self.data_api.search_datasets(user_question, limit=5)
            print(f"データセット検索結果: {len(datasets) if datasets else 0}件")
            
            # データセットの情報を整理
            context_data = []
            if datasets:  # データセットが存在する場合のみ処理
                print("データセット情報を処理中...")
                for i, dataset in enumerate(datasets):
                    print(f"データセット{i+1}: {dataset.get('title', 'タイトルなし') if dataset else 'None'}")
                    
                    if dataset is None:
                        print(f"警告: データセット{i+1}がNoneです")
                        continue
                        
                    try:
                        dataset_info = {
                            "title": dataset.get("title", ""),
                            "notes": dataset.get("notes", ""),
                            "tags": [tag.get("display_name", "") for tag in dataset.get("tags", []) if tag],
                            "organization": dataset.get("organization", {}).get("title", "") if dataset.get("organization") else "",
                            "resources": len(dataset.get("resources", []))
                        }
                        context_data.append(dataset_info)
                        print(f"データセット{i+1}処理完了")
                    except Exception as e:
                        print(f"データセット{i+1}処理エラー: {e}")
                        continue
            
            print(f"処理済みデータセット: {len(context_data)}件")
            
            # プロンプト作成
            if context_data:
                context_text = json.dumps(context_data, ensure_ascii=False, indent=2)
                context_message = f"""
質問: {user_question}

関連する金沢市オープンデータ:
{context_text}

上記のデータを参考に、質問に答えてください。
"""
            else:
                context_message = f"""
質問: {user_question}

関連する金沢市オープンデータは見つかりませんでしたが、金沢市の一般的な情報を基に質問にお答えください。
特に観光地、文化施設、行政サービスなどについて、知っている情報があれば教えてください。
"""
            
            print("OpenAI APIを呼び出し中...")
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": context_message}
            ]
            
            # OpenAI API呼び出し（同期版を使用）
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "success": True,
                "response": ai_response,
                "datasets_used": len(datasets),
                "context_data": context_data[:3]  # 最初の3件のみ返す
            }
            
        except Exception as e:
            print(f"AI応答生成エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "申し訳ございません。現在システムに問題が発生しています。しばらく時間をおいてから再度お試しください。"
            }

# グローバルインスタンス
kanazawa_ai = KanazawaAI()

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """チャットAPI - ユーザーの質問に応答"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                "success": False,
                "error": "メッセージが空です"
            }), 400
        
        # AI応答生成（非同期処理を同期的に実行）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(kanazawa_ai.generate_response(user_message))
        finally:
            loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"チャットAPIエラー: {e}")
        return jsonify({
            "success": False,
            "error": "サーバーエラーが発生しました",
            "response": "申し訳ございません。システムエラーが発生しました。"
        }), 500

@app.route('/api/datasets/search')
def search_datasets():
    """データセット検索API"""
    try:
        query = request.args.get('q', '')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        data_api = KanazawaDataAPI()
        
        # 非同期処理を同期的に実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            datasets = loop.run_until_complete(data_api.search_datasets(query, limit))
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "datasets": datasets,
            "count": len(datasets)
        })
        
    except Exception as e:
        print(f"データセット検索エラー: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """ヘルスチェックAPI"""
    return jsonify({
        "status": "healthy",
        "service": "金沢AI助手",
        "version": "1.0.0"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "エンドポイントが見つかりません"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "内部サーバーエラー"
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 金沢AI助手を起動中...")
    print(f"📍 http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 