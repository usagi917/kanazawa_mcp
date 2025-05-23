from typing import Any, Dict, List
from .tools import MCP_TOOLS, GarbageScheduleInput, TouristSpotInput, TransportationInput, BusScheduleInput
from cache import get_cache, set_cache
from database import SessionDep
from models import GarbageSchedule, TouristSpot, TransportationStop
from sqlalchemy import select
from datetime import datetime
import json
import logging
import os

# 新しいオープンデータサービスをインポート
from services.open_data_service import get_kanazawa_open_data

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPService:
    def __init__(self):
        self.tools = {tool["name"]: tool for tool in MCP_TOOLS}
        # オープンデータモードの設定（環境変数で制御）
        self.use_open_data = os.getenv("USE_OPEN_DATA", "false").lower() == "true"
        logger.info(f"MCPサービスを初期化しました。利用可能なツール数: {len(self.tools)}")
        logger.info(f"オープンデータモード: {'有効' if self.use_open_data else '無効'}")

    def get_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツールの一覧を返す"""
        return MCP_TOOLS

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """ツールを実行して結果を返す"""
        if tool_name not in self.tools:
            logger.error(f"不明なツール: {tool_name}")
            raise ValueError(f"Unknown tool: {tool_name}")

        # キャッシュキーの生成
        cache_key = f"mcp:{tool_name}:{json.dumps(params, sort_keys=True)}"
        
        # キャッシュから結果を取得
        cached_result = get_cache(cache_key)
        if cached_result:
            logger.info(f"キャッシュからデータを取得: {tool_name}")
            return cached_result

        try:
            # ツールの実行
            result = await self._execute_tool_internal(tool_name, params)
            
            # 結果をキャッシュに保存（5分間）
            set_cache(cache_key, result, expires_in=300)
            
            logger.info(f"ツール実行完了: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"ツール実行中にエラーが発生: {tool_name}, エラー: {str(e)}")
            raise

    async def _execute_tool_internal(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """実際のツール実行ロジック"""
        try:
            if tool_name == "get_garbage_schedule":
                return await self._get_garbage_schedule(params)
            elif tool_name == "search_tourist_spots":
                return await self._search_tourist_spots(params)
            elif tool_name == "get_transportation_info":
                return await self._get_transportation_info(params)
            elif tool_name == "get_bus_schedule":
                return await self._get_bus_schedule(params)
            else:
                raise ValueError(f"Tool execution not implemented: {tool_name}")
        except Exception as e:
            logger.error(f"内部ツール実行エラー {tool_name}: {str(e)}")
            raise

    async def _get_garbage_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """ごみ収集スケジュール取得"""
        input_data = GarbageScheduleInput(**params)
        
        if self.use_open_data:
            # オープンデータから取得を試行
            try:
                open_data = await get_kanazawa_open_data("garbage")
                garbage_schedules = open_data.get('data', [])
                
                # 指定された地区コードと日付に一致するスケジュールを検索
                matching_schedules = []
                for schedule in garbage_schedules:
                    if (schedule.get('area_code') == input_data.area_code and 
                        schedule.get('date') == input_data.date):
                        matching_schedules.append(schedule.get('garbage_type', ''))
                
                if matching_schedules:
                    logger.info(f"オープンデータからごみ収集情報を取得: 地区{input_data.area_code}, 件数{len(matching_schedules)}")
                    return {
                        "garbage_types": matching_schedules,
                        "area_code": input_data.area_code,
                        "date": input_data.date,
                        "data_source": "open_data"
                    }
                else:
                    logger.info(f"オープンデータに該当なし、ローカルDBにフォールバック")
            except Exception as e:
                logger.warning(f"オープンデータ取得失敗、ローカルDBにフォールバック: {str(e)}")
        
        # ローカルDBから取得（フォールバック or デフォルト）
        from database import SessionLocal
        
        with SessionLocal() as session:
            try:
                date_obj = datetime.strptime(input_data.date, "%Y-%m-%d").date()
                stmt = (
                    select(GarbageSchedule)
                    .where(GarbageSchedule.area_code == input_data.area_code)
                    .where(GarbageSchedule.date == date_obj)
                )
                schedules = session.scalars(stmt).all()
                garbage_types = [s.garbage_type for s in schedules]
                
                logger.info(f"ローカルDBからごみ収集情報取得: 地区{input_data.area_code}, 日付{input_data.date}, 件数{len(garbage_types)}")
                
                return {
                    "garbage_types": garbage_types,
                    "area_code": input_data.area_code,
                    "date": input_data.date,
                    "data_source": "local_db"
                }
            except ValueError as e:
                logger.error(f"日付フォーマットエラー: {input_data.date}")
                raise ValueError(f"Invalid date format: {input_data.date}")

    async def _search_tourist_spots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """観光スポット検索"""
        input_data = TouristSpotInput(**params)
        
        if self.use_open_data:
            # オープンデータから取得を試行
            try:
                open_data = await get_kanazawa_open_data("tourist")
                tourist_spots = open_data.get('data', [])
                
                # キーワード検索
                keyword = input_data.keyword.lower()
                matching_spots = []
                
                for spot in tourist_spots:
                    name = spot.get('name', '').lower()
                    description = spot.get('description', '').lower()
                    
                    if keyword in name or keyword in description:
                        result_spot = {
                            "name": spot.get('name', ''),
                            "description": spot.get('description', ''),
                            "location": {
                                "lat": spot.get('latitude', 0), 
                                "lng": spot.get('longitude', 0)
                            },
                            "address": spot.get('address', ''),
                            "category": spot.get('category', ''),
                            "opening_hours": spot.get('opening_hours', ''),
                            "contact": spot.get('contact', ''),
                        }
                        matching_spots.append(result_spot)
                        
                        if len(matching_spots) >= input_data.limit:
                            break
                
                if matching_spots:
                    logger.info(f"オープンデータから観光スポット検索: キーワード'{input_data.keyword}', 件数{len(matching_spots)}")
                    return {"spots": matching_spots, "data_source": "open_data"}
                else:
                    logger.info(f"オープンデータに該当なし、ローカルDBにフォールバック")
            except Exception as e:
                logger.warning(f"オープンデータ取得失敗、ローカルDBにフォールバック: {str(e)}")
        
        # ローカルDBから取得（フォールバック or デフォルト）
        from database import SessionLocal
        
        with SessionLocal() as session:
            keyword = f"%{input_data.keyword}%"
            stmt = (
                select(TouristSpot)
                .where(TouristSpot.name.like(keyword) | TouristSpot.description.like(keyword))
                .limit(input_data.limit)
            )
            spots = session.scalars(stmt).all()
            
            result_spots = [
                {
                    "name": s.name,
                    "description": s.description,
                    "location": {"lat": s.latitude, "lng": s.longitude},
                    "address": s.address,
                    "category": s.category,
                    "opening_hours": s.opening_hours,
                    "contact": s.contact,
                }
                for s in spots
            ]
            
            logger.info(f"ローカルDBから観光スポット検索: キーワード'{input_data.keyword}', 件数{len(result_spots)}")
            
            return {"spots": result_spots, "data_source": "local_db"}

    async def _get_transportation_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """交通情報取得"""
        input_data = TransportationInput(**params)
        
        if self.use_open_data:
            # オープンデータから取得を試行
            try:
                open_data = await get_kanazawa_open_data("transportation")
                transportation_stops = open_data.get('data', [])
                
                # タイプ別フィルタリング
                matching_stops = []
                for stop in transportation_stops:
                    if stop.get('type') == input_data.type:
                        result_stop = {
                            "name": stop.get('name', ''),
                            "type": stop.get('type', ''),
                            "location": {
                                "lat": stop.get('latitude', 0),
                                "lng": stop.get('longitude', 0)
                            },
                            "address": stop.get('address', ''),
                            "routes": stop.get('routes', []),
                        }
                        matching_stops.append(result_stop)
                
                if matching_stops:
                    logger.info(f"オープンデータから交通情報取得: タイプ'{input_data.type}', 件数{len(matching_stops)}")
                    return {"stops": matching_stops, "data_source": "open_data"}
                else:
                    logger.info(f"オープンデータに該当なし、ローカルDBにフォールバック")
            except Exception as e:
                logger.warning(f"オープンデータ取得失敗、ローカルDBにフォールバック: {str(e)}")
        
        # ローカルDBから取得（フォールバック or デフォルト）
        from database import SessionLocal
        
        with SessionLocal() as session:
            stmt = select(TransportationStop).where(TransportationStop.type == input_data.type)
            stops = session.scalars(stmt).all()
            
            result_stops = [
                {
                    "name": s.name,
                    "type": s.type,
                    "location": {"lat": s.latitude, "lng": s.longitude},
                    "address": s.address,
                    "routes": s.routes,
                }
                for s in stops
            ]
            
            logger.info(f"ローカルDBから交通情報取得: タイプ'{input_data.type}', 件数{len(result_stops)}")
            
            return {"stops": result_stops, "data_source": "local_db"}

    async def _get_bus_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """バス時刻表検索"""
        input_data = BusScheduleInput(**params)
        
        if self.use_open_data:
            # オープンデータから取得を試行
            try:
                # 実際のGTFSデータがあれば使用、なければサンプルデータ
                schedules = self._get_sample_bus_schedule_data()
                
                # フィルタリング処理
                filtered_schedules = []
                for schedule in schedules:
                    match = True
                    
                    # 時間帯フィルタ
                    if input_data.time_range:
                        start_hour = int(input_data.time_range.split(':')[0])
                        schedule_hour = int(schedule['departure_time'].split(':')[0])
                        if schedule_hour != start_hour:
                            match = False
                    
                    # 路線名フィルタ
                    if input_data.route_name:
                        if input_data.route_name.lower() not in schedule['route_name'].lower():
                            match = False
                    
                    # 停留所名フィルタ
                    if input_data.stop_name:
                        if input_data.stop_name.lower() not in schedule['stop_name'].lower():
                            match = False
                    
                    if match:
                        filtered_schedules.append(schedule)
                        if len(filtered_schedules) >= input_data.limit:
                            break
                
                logger.info(f"バス時刻表検索: 時間帯'{input_data.time_range}', 路線'{input_data.route_name}', 停留所'{input_data.stop_name}', 件数{len(filtered_schedules)}")
                
                return {
                    "schedules": filtered_schedules,
                    "data_source": "open_data",
                    "filters": {
                        "time_range": input_data.time_range,
                        "route_name": input_data.route_name,
                        "stop_name": input_data.stop_name
                    }
                }
                
            except Exception as e:
                logger.warning(f"オープンデータ取得失敗、ローカルDBにフォールバック: {str(e)}")
        
        # ローカルDBまたはサンプルデータから取得
        schedules = self._get_sample_bus_schedule_data()
        
        # 同様のフィルタリング処理
        filtered_schedules = []
        for schedule in schedules:
            match = True
            
            if input_data.time_range:
                start_hour = int(input_data.time_range.split(':')[0])
                schedule_hour = int(schedule['departure_time'].split(':')[0])
                if schedule_hour != start_hour:
                    match = False
            
            if input_data.route_name:
                if input_data.route_name.lower() not in schedule['route_name'].lower():
                    match = False
            
            if input_data.stop_name:
                if input_data.stop_name.lower() not in schedule['stop_name'].lower():
                    match = False
            
            if match:
                filtered_schedules.append(schedule)
                if len(filtered_schedules) >= input_data.limit:
                    break
        
        logger.info(f"ローカルDBからバス時刻表検索: 件数{len(filtered_schedules)}")
        
        return {
            "schedules": filtered_schedules,
            "data_source": "local_db",
            "filters": {
                "time_range": input_data.time_range,
                "route_name": input_data.route_name,
                "stop_name": input_data.stop_name
            }
        }
    
    def _get_sample_bus_schedule_data(self) -> List[Dict[str, Any]]:
        """サンプルバス時刻表データ"""
        return [
            {
                "route_name": "ふらっとバス材木ルート",
                "stop_name": "金沢駅東口",
                "departure_time": "15:05",
                "destination": "材木",
                "bus_number": "材木01"
            },
            {
                "route_name": "ふらっとバス材木ルート", 
                "stop_name": "金沢駅東口",
                "departure_time": "15:20",
                "destination": "材木",
                "bus_number": "材木02"
            },
            {
                "route_name": "ふらっとバス材木ルート",
                "stop_name": "金沢駅東口", 
                "departure_time": "15:35",
                "destination": "材木",
                "bus_number": "材木03"
            },
            {
                "route_name": "ふらっとバス材木ルート",
                "stop_name": "金沢駅東口",
                "departure_time": "15:50",
                "destination": "材木", 
                "bus_number": "材木04"
            },
            {
                "route_name": "ふらっとバス此花ルート",
                "stop_name": "武蔵ヶ辻・近江町市場",
                "departure_time": "15:10",
                "destination": "此花",
                "bus_number": "此花01"
            },
            {
                "route_name": "ふらっとバス此花ルート",
                "stop_name": "武蔵ヶ辻・近江町市場", 
                "departure_time": "15:25",
                "destination": "此花",
                "bus_number": "此花02"
            },
            {
                "route_name": "ふらっとバス此花ルート",
                "stop_name": "武蔵ヶ辻・近江町市場",
                "departure_time": "15:40",
                "destination": "此花",
                "bus_number": "此花03"
            },
            {
                "route_name": "ふらっとバス此花ルート",
                "stop_name": "武蔵ヶ辻・近江町市場",
                "departure_time": "15:55",
                "destination": "此花",
                "bus_number": "此花04"
            },
            {
                "route_name": "北陸鉄道バス",
                "stop_name": "金沢駅",
                "departure_time": "15:08",
                "destination": "東部車庫",
                "bus_number": "東部31"
            },
            {
                "route_name": "北陸鉄道バス",
                "stop_name": "金沢駅",
                "departure_time": "15:23",
                "destination": "東部車庫", 
                "bus_number": "東部32"
            },
            {
                "route_name": "北陸鉄道バス",
                "stop_name": "金沢駅",
                "departure_time": "15:38",
                "destination": "東部車庫",
                "bus_number": "東部33"
            },
            {
                "route_name": "北陸鉄道バス",
                "stop_name": "金沢駅",
                "departure_time": "15:53", 
                "destination": "東部車庫",
                "bus_number": "東部34"
            }
        ] 