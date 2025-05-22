from typing import Any, Dict, List
from .tools import MCP_TOOLS, GarbageScheduleInput, TouristSpotInput, TransportationInput
from cache import get_cache, set_cache
import json

class MCPService:
    def __init__(self):
        self.tools = {tool["name"]: tool for tool in MCP_TOOLS}

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
            # TODO: 実際のデータベースクエリを実装
            return {
                "garbage_types": ["燃えるごみ", "資源ごみ"],
                "area_code": input_data.area_code,
                "date": input_data.date
            }
        
        elif tool_name == "search_tourist_spots":
            input_data = TouristSpotInput(**params)
            # TODO: 実際の観光スポット検索を実装
            return {
                "spots": [
                    {
                        "name": "兼六園",
                        "description": "日本三名園の一つ",
                        "location": {"lat": 36.5621, "lng": 136.6625}
                    }
                ]
            }
        
        elif tool_name == "get_transportation_info":
            input_data = TransportationInput(**params)
            # TODO: 実際の交通情報取得を実装
            return {
                "stops": [
                    {
                        "name": "金沢駅",
                        "type": "train_station",
                        "location": {"lat": 36.5781, "lng": 136.6567}
                    }
                ]
            }
        
        raise ValueError(f"Tool execution not implemented: {tool_name}") 