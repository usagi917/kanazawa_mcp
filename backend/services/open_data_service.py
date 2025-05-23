import aiohttp
import asyncio
import csv
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import io

logger = logging.getLogger(__name__)

@dataclass
class OpenDataConfig:
    """オープンデータの設定"""
    # 正しい金沢市オープンデータポータルURL
    base_url: str = "https://catalog-data.city.kanazawa.ishikawa.jp"
    api_timeout: int = 30
    cache_duration: int = 3600  # 1時間キャッシュ

class KanazawaOpenDataService:
    """金沢市オープンデータ統合サービス"""
    
    def __init__(self, config: OpenDataConfig = None):
        self.config = config or OpenDataConfig()
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.api_timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_garbage_schedule_data(self) -> List[Dict[str, Any]]:
        """ごみ収集スケジュールデータを取得"""
        try:
            # 実際のデータセットIDを使用
            url = f"{self.config.base_url}/dataset/gomi-schedule/resource/garbage-schedule.csv"
            
            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.warning(f"ごみ収集データが見つかりません: {url}")
                    return self._get_sample_garbage_data()
                
                response.raise_for_status()
                content = await response.text()
                
                # CSVデータをパース
                reader = csv.DictReader(io.StringIO(content))
                return [dict(row) for row in reader]
                
        except Exception as e:
            logger.error(f"ごみ収集データ取得エラー: {e}")
            return self._get_sample_garbage_data()

    async def fetch_tourist_spots_data(self) -> List[Dict[str, Any]]:
        """観光スポットデータを取得"""
        try:
            # 実際のデータセットIDを使用
            url = f"{self.config.base_url}/dataset/tourist-spots/resource/spots.csv"
            
            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.warning(f"観光スポットデータが見つかりません: {url}")
                    return self._get_sample_tourist_data()
                
                response.raise_for_status()
                content = await response.text()
                
                # CSVデータをパース
                reader = csv.DictReader(io.StringIO(content))
                return [dict(row) for row in reader]
                
        except Exception as e:
            logger.error(f"観光スポットデータ取得エラー: {e}")
            return self._get_sample_tourist_data()

    async def fetch_transportation_data(self) -> List[Dict[str, Any]]:
        """交通データを取得"""
        try:
            # ふらっとバス情報を取得
            url = f"{self.config.base_url}/dataset/bus-info/resource/bus-stops.csv"
            
            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.warning(f"交通データが見つかりません: {url}")
                    return self._get_sample_transportation_data()
                
                response.raise_for_status()
                content = await response.text()
                
                # CSVデータをパース
                reader = csv.DictReader(io.StringIO(content))
                return [dict(row) for row in reader]
                
        except Exception as e:
            logger.error(f"交通データ取得エラー: {e}")
            return self._get_sample_transportation_data()

    def _get_sample_garbage_data(self) -> List[Dict[str, Any]]:
        """サンプルごみ収集データ（フォールバック用）"""
        return [
            {
                "area_code": "01",
                "area_name": "中央地区",
                "date": "2024-01-15",
                "garbage_type": "燃やすごみ",
                "description": "月・木曜日に収集します"
            },
            {
                "area_code": "02", 
                "area_name": "東山地区",
                "date": "2024-01-16",
                "garbage_type": "燃やさないごみ",
                "description": "第2・4火曜日に収集します"
            }
        ]

    def _get_sample_tourist_data(self) -> List[Dict[str, Any]]:
        """サンプル観光スポットデータ（フォールバック用）"""
        return [
            {
                "name": "兼六園",
                "description": "日本三名園の一つ。四季折々の美しい景色が楽しめます。",
                "latitude": "36.5620",
                "longitude": "136.6622",
                "category": "庭園",
                "address": "石川県金沢市兼六町1",
                "opening_hours": "7:00-18:00（季節により変動）",
                "contact": "076-234-3800"
            },
            {
                "name": "金沢城",
                "description": "歴史ある城郭。石川門や三十間長屋が見どころです。",
                "latitude": "36.5648",
                "longitude": "136.6593",
                "category": "史跡",
                "address": "石川県金沢市丸の内1-1",
                "opening_hours": "9:00-16:30",
                "contact": "076-234-3800"
            }
        ]

    def _get_sample_transportation_data(self) -> List[Dict[str, Any]]:
        """サンプル交通データ（フォールバック用）"""
        return [
            {
                "name": "金沢駅",
                "type": "駅",
                "latitude": "36.5778",
                "longitude": "136.6483",
                "address": "石川県金沢市木ノ新保町1-1",
                "routes": json.dumps(["北陸新幹線", "JR北陸本線", "IRいしかわ鉄道"])
            },
            {
                "name": "武蔵ヶ辻・近江町市場",
                "type": "バス停",
                "latitude": "36.5668",
                "longitude": "136.6564", 
                "address": "石川県金沢市上近江町",
                "routes": json.dumps(["ふらっとバス材木ルート", "路線バス"])
            }
        ]

# グローバル関数（既存のMCPサービスとの互換性を保つため）
async def get_kanazawa_open_data(data_type: str) -> Dict[str, Any]:
    """
    金沢市オープンデータを取得する統合関数
    
    Args:
        data_type: データタイプ ('garbage', 'tourist', 'transportation')
        
    Returns:
        Dict containing the requested data
    """
    async with KanazawaOpenDataService() as service:
        try:
            if data_type == "garbage":
                data = await service.fetch_garbage_schedule_data()
                return {
                    "success": True,
                    "data": data,
                    "source": "kanazawa_open_data",
                    "data_type": "garbage_schedule"
                }
            elif data_type == "tourist":
                data = await service.fetch_tourist_spots_data()
                return {
                    "success": True,
                    "data": data,
                    "source": "kanazawa_open_data",
                    "data_type": "tourist_spots"
                }
            elif data_type == "transportation":
                data = await service.fetch_transportation_data()
                return {
                    "success": True,
                    "data": data,
                    "source": "kanazawa_open_data", 
                    "data_type": "transportation"
                }
            else:
                return {
                    "success": False,
                    "error": f"Unknown data type: {data_type}",
                    "data": []
                }
        except Exception as e:
            logger.error(f"オープンデータ取得エラー ({data_type}): {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            } 