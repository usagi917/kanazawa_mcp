import requests
import pandas as pd
import json
from datetime import datetime
import os

def fetch_facilities():
    """金沢市の施設情報を取得"""
    # ジャンル一覧を取得
    genres_url = "https://infra-api.city.kanazawa.ishikawa.jp/v1/genres/list.json"
    genres_response = requests.get(genres_url, params={"lang": "ja"})
    genres_data = genres_response.json()
    
    # 施設情報を取得（例：観光施設）
    facilities_url = "https://infra-api.city.kanazawa.ishikawa.jp/v1/facilities/search.json"
    facilities_response = requests.get(
        facilities_url,
        params={
            "lang": "ja",
            "count": 100,  # 最大100件取得
            "genre": "3"   # 観光施設のジャンルID
        }
    )
    facilities_data = facilities_response.json()
    
    # データを整形
    records = []
    for facility in facilities_data.get("facilities", []):
        records.append({
            'id': facility['id'],
            'name': facility['name'],
            'summary': facility.get('summary', ''),
            'address': facility.get('address', ''),
            'latitude': facility.get('coordinates', {}).get('latitude', ''),
            'longitude': facility.get('coordinates', {}).get('longitude', ''),
            'tel': facility.get('tel', ''),
            'opening_hours': facility.get('opening_hours', ''),
            'closed_days': facility.get('closed_days', ''),
            'fee': facility.get('fee', ''),
            'url': facility.get('url', '')
        })
    
    # CSVに保存
    df = pd.DataFrame(records)
    df.to_csv('data/facilities.csv', index=False)
    print("施設情報の取得が完了しました！")

def main():
    # データディレクトリの作成
    os.makedirs('data', exist_ok=True)
    
    # 施設情報の取得
    fetch_facilities()
    
    print("全てのデータの取得が完了しました！")

if __name__ == "__main__":
    main() 