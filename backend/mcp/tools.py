from typing import List, Optional
from pydantic import BaseModel

class GarbageScheduleInput(BaseModel):
    area_code: str
    date: str

class TouristSpotInput(BaseModel):
    keyword: str
    limit: int = 5

class TransportationInput(BaseModel):
    type: str  # bus_stop, train_station, etc.
    filter: Optional[dict] = None

# MCPツール定義
MCP_TOOLS = [
    {
        "name": "get_garbage_schedule",
        "description": "地区コードと日付で収集ごみ種別を返す",
        "input_schema": GarbageScheduleInput.model_json_schema(),
    },
    {
        "name": "search_tourist_spots",
        "description": "キーワードで観光スポットを検索",
        "input_schema": TouristSpotInput.model_json_schema(),
    },
    {
        "name": "get_transportation_info",
        "description": "交通情報を取得（バス停、駅など）",
        "input_schema": TransportationInput.model_json_schema(),
    }
] 