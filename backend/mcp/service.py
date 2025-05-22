from typing import Any, Dict, List
from .tools import MCP_TOOLS, GarbageScheduleInput, TouristSpotInput, TransportationInput
from cache import get_cache, set_cache
from database import SessionLocal
from models import GarbageSchedule, TouristSpot, TransportationStop
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
import json

class MCPService:
    def __init__(self):
        self.tools = {tool["name"]: tool for tool in MCP_TOOLS}

    def _get_db(self) -> Session:
        """Create a new DB session"""
        return SessionLocal()

    def get_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツールの一覧を返す"""
        return MCP_TOOLS

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """ツールを実行して結果を返す"""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        # キャッシュキーの生成
        cache_key = f"mcp:{tool_name}:{json.dumps(params, sort_keys=True)}"
        
        # キャッシュから結果を取得
        cached_result = get_cache(cache_key)
        if cached_result:
            return cached_result

        # ツールの実行
        result = await self._execute_tool_internal(tool_name, params)
        
        # 結果をキャッシュに保存
        set_cache(cache_key, result)
        
        return result

    async def _execute_tool_internal(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """実際のツール実行ロジック"""
        if tool_name == "get_garbage_schedule":
            input_data = GarbageScheduleInput(**params)
            db = self._get_db()
            try:
                date_obj = datetime.strptime(input_data.date, "%Y-%m-%d").date()
                stmt = (
                    select(GarbageSchedule)
                    .where(GarbageSchedule.area_code == input_data.area_code)
                    .where(GarbageSchedule.date == date_obj)
                )
                schedules = db.scalars(stmt).all()
                garbage_types = [s.garbage_type for s in schedules]
                return {
                    "garbage_types": garbage_types,
                    "area_code": input_data.area_code,
                    "date": input_data.date,
                }
            finally:
                db.close()

        elif tool_name == "search_tourist_spots":
            input_data = TouristSpotInput(**params)
            db = self._get_db()
            try:
                keyword = f"%{input_data.keyword}%"
                stmt = (
                    select(TouristSpot)
                    .where(TouristSpot.name.like(keyword) | TouristSpot.description.like(keyword))
                    .limit(input_data.limit)
                )
                spots = db.scalars(stmt).all()
                return {
                    "spots": [
                        {
                            "name": s.name,
                            "description": s.description,
                            "location": {"lat": s.latitude, "lng": s.longitude},
                            "address": s.address,
                        }
                        for s in spots
                    ]
                }
            finally:
                db.close()

        elif tool_name == "get_transportation_info":
            input_data = TransportationInput(**params)
            db = self._get_db()
            try:
                stmt = select(TransportationStop).where(TransportationStop.type == input_data.type)
                stops = db.scalars(stmt).all()
                return {
                    "stops": [
                        {
                            "name": s.name,
                            "type": s.type,
                            "location": {"lat": s.latitude, "lng": s.longitude},
                            "address": s.address,
                        }
                        for s in stops
                    ]
                }
            finally:
                db.close()
        
        raise ValueError(f"Tool execution not implemented: {tool_name}") 