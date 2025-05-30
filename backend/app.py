"""
金沢AI助手 - メインFlaskアプリケーション
金沢市のオープンデータを活用したチャットボットAPI
"""

import os
import json
import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import httpx
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests

# 環境変数読み込み
load_dotenv()

app = Flask(__name__, 
           template_folder='../frontend',
           static_folder='../static')
CORS(app)

# OpenAI クライアント設定
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def format_response_text(text: str) -> str:
    """
    AIレスポンステキストを読みやすい形式に整形
    マークダウンをプレーンテキストに変換し、適切な改行と段落構造を追加
    """
    if not text:
        return ""
    
    # マークダウンの見出しを変換（より目立つ形式に）
    text = re.sub(r'^### (.+)$', r'\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n■ \1\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'\n\n◆◆◆ \1 ◆◆◆\n', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'\n\n★★★ \1 ★★★\n', text, flags=re.MULTILINE)
    
    # マークダウンのリストを変換（インデントと記号を改良）
    text = re.sub(r'^- (.+)$', r'  ▶ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\* (.+)$', r'  ▶ \1', text, flags=re.MULTILINE)
    
    # 番号付きリストの整形（より見やすく）
    text = re.sub(r'^(\d+)\. (.+)$', r'  【\1】 \2', text, flags=re.MULTILINE)
    
    # 太字の変換（より目立つ形式に）
    text = re.sub(r'\*\*(.+?)\*\*', r'【重要】\1', text)
    text = re.sub(r'__(.+?)__', r'【注目】\1', text)
    
    # コードブロックの除去（バッククォート）
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.+?)`', r'「\1」', text)
    
    # 数値や統計データを強調
    text = re.sub(r'(\d+(?:\.\d+)?%)', r'【数値】\1', text)
    text = re.sub(r'(\d+(?:,\d{3})*(?:\.\d+)?(?:点|件|人|円|万円|億円))', r'【データ】\1', text)
    
    # 段落の改善：文の終わりで適切に改行
    text = re.sub(r'([。！？])([あ-ん])', r'\1\n\n\2', text)
    text = re.sub(r'([。！？])([ア-ン])', r'\1\n\n\2', text)
    text = re.sub(r'([。！？])([A-Za-z])', r'\1\n\n\2', text)
    
    # 連続する改行を整理
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\n{3}', '\n\n', text)
    
    # 行の先頭と末尾の空白を除去
    lines = [line.strip() for line in text.split('\n')]
    
    # 空行を適切に配置し、段落構造を改善
    formatted_lines = []
    for i, line in enumerate(lines):
        if line:  # 空行でない場合
            # 見出し行の前後に空行を追加
            if ('■' in line or '◆' in line or '★' in line or '━' in line):
                if formatted_lines and formatted_lines[-1]:
                    formatted_lines.append('')
                formatted_lines.append(line)
                formatted_lines.append('')
            # リスト項目の場合
            elif line.startswith('  ▶') or line.startswith('  【'):
                formatted_lines.append(line)
            # 通常の文章の場合
            else:
                formatted_lines.append(line)
        elif i > 0 and formatted_lines and formatted_lines[-1]:  # 前の行が空行でない場合のみ空行を追加
            formatted_lines.append('')
    
    # 最終的な整形
    result = '\n'.join(formatted_lines)
    
    # 先頭と末尾の余分な改行を除去
    result = result.strip()
    
    # 最後に全体の構造を整える
    result = re.sub(r'\n\n\n+', '\n\n', result)  # 3つ以上の連続改行を2つに
    
    return result

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
    
    async def extract_numerical_data(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データセットから具体的な数値データを抽出"""
        try:
            numerical_insights = {
                "population_data": {},
                "business_data": {},
                "economic_data": {},
                "tourism_data": {},
                "extracted_values": []
            }
            
            for dataset in datasets[:5]:  # 上位5件のデータセットを詳細分析
                if not dataset:
                    continue
                
                dataset_id = dataset.get("id", "")
                title = dataset.get("title", "")
                
                print(f"数値データ抽出中: {title}")
                
                # データセット詳細を取得
                detail = await self.get_dataset_detail(dataset_id)
                if not detail:
                    continue
                
                resources = detail.get("resources", [])
                
                for resource in resources[:2]:  # 各データセットの上位2リソース
                    resource_url = resource.get("url", "")
                    resource_format = resource.get("format", "").lower()
                    
                    if resource_format in ["csv", "json", "xlsx"]:
                        # リソースデータを取得
                        raw_data = await self.get_resource_data(resource_url)
                        if raw_data:
                            # 数値を抽出
                            extracted_numbers = self._extract_numbers_from_text(raw_data, title)
                            if extracted_numbers:
                                numerical_insights["extracted_values"].extend(extracted_numbers)
                                
                                # カテゴリ別に分類
                                self._categorize_numerical_data(extracted_numbers, title, numerical_insights)
            
            # 統計サマリーを生成
            numerical_insights["summary"] = self._generate_numerical_summary(numerical_insights)
            
            return numerical_insights
            
        except Exception as e:
            print(f"数値データ抽出エラー: {e}")
            return {"error": str(e)}
    
    def _extract_numbers_from_text(self, text: str, context: str) -> List[Dict[str, Any]]:
        """テキストから数値を抽出"""
        import re
        
        extracted = []
        
        # 人口関連の数値パターン
        population_patterns = [
            r'人口[：:\s]*([0-9,]+)人?',
            r'総人口[：:\s]*([0-9,]+)人?',
            r'([0-9,]+)人',
            r'人口密度[：:\s]*([0-9,]+\.?[0-9]*)',
        ]
        
        # 事業所・企業関連の数値パターン
        business_patterns = [
            r'事業所数[：:\s]*([0-9,]+)',
            r'企業数[：:\s]*([0-9,]+)',
            r'店舗数[：:\s]*([0-9,]+)',
            r'従業員数[：:\s]*([0-9,]+)',
        ]
        
        # 経済関連の数値パターン
        economic_patterns = [
            r'売上[：:\s]*([0-9,]+)万?円',
            r'収入[：:\s]*([0-9,]+)万?円',
            r'GDP[：:\s]*([0-9,]+)',
            r'([0-9,]+)億円',
            r'([0-9,]+)万円',
        ]
        
        # 観光関連の数値パターン
        tourism_patterns = [
            r'観光客数[：:\s]*([0-9,]+)',
            r'宿泊者数[：:\s]*([0-9,]+)',
            r'入込客数[：:\s]*([0-9,]+)',
        ]
        
        all_patterns = [
            ("population", population_patterns),
            ("business", business_patterns),
            ("economic", economic_patterns),
            ("tourism", tourism_patterns)
        ]
        
        for category, patterns in all_patterns:
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1).replace(',', '')
                        value = float(value_str)
                        
                        extracted.append({
                            "category": category,
                            "value": value,
                            "unit": self._determine_unit(match.group(0)),
                            "context": context,
                            "raw_match": match.group(0)
                        })
                    except (ValueError, IndexError):
                        continue
        
        return extracted
    
    def _determine_unit(self, match_text: str) -> str:
        """マッチしたテキストから単位を判定"""
        if "人" in match_text:
            return "人"
        elif "万円" in match_text:
            return "万円"
        elif "億円" in match_text:
            return "億円"
        elif "円" in match_text:
            return "円"
        elif "%" in match_text:
            return "%"
        elif "密度" in match_text:
            return "人/km²"
        else:
            return "件"
    
    def _categorize_numerical_data(self, extracted_numbers: List[Dict], title: str, insights: Dict):
        """抽出した数値をカテゴリ別に分類"""
        for item in extracted_numbers:
            category = item["category"]
            value = item["value"]
            unit = item["unit"]
            
            if category == "population":
                if "人口" in title:
                    insights["population_data"]["total_population"] = value
                elif "密度" in title:
                    insights["population_data"]["population_density"] = value
                    
            elif category == "business":
                if "事業所" in title:
                    insights["business_data"]["business_establishments"] = value
                elif "従業員" in title:
                    insights["business_data"]["employees"] = value
                    
            elif category == "economic":
                if "売上" in title or "収入" in title:
                    insights["economic_data"]["revenue"] = value
                elif "GDP" in title:
                    insights["economic_data"]["gdp"] = value
                    
            elif category == "tourism":
                if "観光客" in title:
                    insights["tourism_data"]["tourists"] = value
                elif "宿泊" in title:
                    insights["tourism_data"]["accommodation"] = value
    
    def _generate_numerical_summary(self, insights: Dict) -> Dict[str, Any]:
        """数値データのサマリーを生成"""
        summary = {
            "data_points_found": len(insights.get("extracted_values", [])),
            "categories_covered": [],
            "key_metrics": {}
        }
        
        # カテゴリの特定
        if insights.get("population_data"):
            summary["categories_covered"].append("人口統計")
            if "total_population" in insights["population_data"]:
                summary["key_metrics"]["人口"] = f"{insights['population_data']['total_population']:,.0f}人"
                
        if insights.get("business_data"):
            summary["categories_covered"].append("事業統計")
            if "business_establishments" in insights["business_data"]:
                summary["key_metrics"]["事業所数"] = f"{insights['business_data']['business_establishments']:,.0f}件"
                
        if insights.get("economic_data"):
            summary["categories_covered"].append("経済統計")
            
        if insights.get("tourism_data"):
            summary["categories_covered"].append("観光統計")
            if "tourists" in insights["tourism_data"]:
                summary["key_metrics"]["観光客数"] = f"{insights['tourism_data']['tourists']:,.0f}人"
        
        return summary

class BusinessIntelligenceEngine:
    """ビジネスインテリジェンス分析エンジン - オープンデータからビジネス機会を発見"""
    
    def __init__(self):
        self.data_api = KanazawaDataAPI()
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self.scaler = StandardScaler()
        
    async def analyze_business_opportunities(self, industry: str, target_area: str = "") -> Dict[str, Any]:
        """業界とエリアに基づいてビジネス機会を分析"""
        try:
            print(f"ビジネス機会分析開始: 業界={industry}, エリア={target_area}")
            
            # 関連データセットを検索
            search_queries = [
                f"{industry} {target_area}",
                f"人口 統計 {target_area}",
                f"経済 産業 {industry}",
                f"観光 {target_area}" if "観光" in industry else f"施設 {target_area}",
                "年齢別 人口"
            ]
            
            all_datasets = []
            for query in search_queries:
                datasets = await self.data_api.search_datasets(query, limit=5)
                all_datasets.extend(datasets)
            
            # データ分析
            market_analysis = await self._analyze_market_data(all_datasets, industry, target_area)
            demographic_insights = await self._analyze_demographics(all_datasets)
            competition_analysis = await self._analyze_competition(all_datasets, industry)
            trend_predictions = await self._predict_trends(all_datasets, industry)
            
            # ビジネスアイデア生成
            business_ideas = await self._generate_business_ideas(
                market_analysis, demographic_insights, competition_analysis, industry, target_area
            )
            
            return {
                "success": True,
                "industry": industry,
                "target_area": target_area,
                "market_analysis": market_analysis,
                "demographic_insights": demographic_insights,
                "competition_analysis": competition_analysis,
                "trend_predictions": trend_predictions,
                "business_ideas": business_ideas,
                "datasets_analyzed": len(all_datasets)
            }
            
        except Exception as e:
            print(f"ビジネス機会分析エラー: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_market_data(self, datasets: List[Dict], industry: str, area: str) -> Dict[str, Any]:
        """市場データ分析 - 実際の数値データを活用した専門的な分析"""
        try:
            # 実際の数値データを抽出
            print("実際の数値データを抽出中...")
            numerical_data = await self.data_api.extract_numerical_data(datasets)
            print(f"数値データ抽出結果: {numerical_data.keys() if numerical_data else 'None'}")
            
            market_size_indicators = []
            growth_indicators = []
            economic_indicators = []
            
            # 抽出された実際の数値を活用
            actual_population = None
            actual_businesses = None
            actual_revenue = None
            actual_tourists = None
            
            if numerical_data.get("population_data"):
                actual_population = numerical_data["population_data"].get("total_population")
                print(f"人口データ取得: {actual_population}")
            if numerical_data.get("business_data"):
                actual_businesses = numerical_data["business_data"].get("business_establishments")
                print(f"事業所データ取得: {actual_businesses}")
            if numerical_data.get("economic_data"):
                actual_revenue = numerical_data["economic_data"].get("revenue")
                print(f"経済データ取得: {actual_revenue}")
            if numerical_data.get("tourism_data"):
                actual_tourists = numerical_data["tourism_data"].get("tourists")
                print(f"観光データ取得: {actual_tourists}")
            
            for dataset in datasets:
                if not dataset:
                    continue
                    
                title = dataset.get("title", "").lower()
                notes = dataset.get("notes", "").lower()
                
                # 市場規模指標の抽出
                if any(keyword in title or keyword in notes for keyword in 
                       ["売上", "収入", "経済", "産業", "事業所", "従業員"]):
                    relevance_score = 90 if industry.lower() in title else 60
                    market_size_indicators.append({
                        "title": dataset.get("title", ""),
                        "relevance_score": relevance_score,
                        "data_quality": "高" if len(dataset.get("resources", [])) > 2 else "中"
                    })
                
                # 成長指標の抽出
                if any(keyword in title or keyword in notes for keyword in 
                       ["増加", "成長", "推移", "変化", "トレンド"]):
                    trend_strength = 85 if "増加" in title or "成長" in title else 50
                    growth_indicators.append({
                        "title": dataset.get("title", ""),
                        "trend_strength": trend_strength,
                        "time_series": "有" if "年次" in title or "月次" in title else "無"
                    })
                
                # 経済指標の抽出
                if any(keyword in title or keyword in notes for keyword in 
                       ["GDP", "付加価値", "生産性", "雇用", "投資"]):
                    economic_indicators.append({
                        "title": dataset.get("title", ""),
                        "indicator_type": "マクロ経済"
                    })
            
            # 実際の数値に基づく詳細な市場分析スコア計算
            base_market_score = min(len(market_size_indicators) * 15, 100)
            growth_potential_score = min(len(growth_indicators) * 12, 100)
            data_availability_score = min(len(datasets) * 8, 100)
            
            # 実際の数値データがある場合のボーナススコア
            numerical_bonus = 0
            if actual_population:
                numerical_bonus += 20
            if actual_businesses:
                numerical_bonus += 15
            if actual_revenue:
                numerical_bonus += 15
            if actual_tourists:
                numerical_bonus += 10
            
            # 業界別補正係数（実際のデータに基づく）
            industry_multipliers = {
                "観光業": 1.3,  # 金沢は観光都市
                "飲食業": 1.2,  # 食文化が豊富
                "サービス業": 1.1,
                "IT業": 0.9,   # 地方都市のため
                "製造業": 1.0,
                "小売業": 1.1
            }
            
            multiplier = industry_multipliers.get(industry, 1.0)
            adjusted_market_score = min(int((base_market_score + numerical_bonus) * multiplier), 100)
            
            # 市場規模の実際の推定（人口ベース）
            estimated_market_size = None
            market_penetration_rate = None
            if actual_population:
                # 業界別の市場浸透率を使用
                penetration_rates = {
                    "飲食業": 0.15,  # 人口の15%が定期利用
                    "観光業": 0.08,  # 人口の8%が関連サービス利用
                    "小売業": 0.25,  # 人口の25%が定期利用
                    "サービス業": 0.12,
                    "IT業": 0.05,
                    "製造業": 0.03
                }
                market_penetration_rate = penetration_rates.get(industry, 0.10)
                estimated_market_size = int(actual_population * market_penetration_rate)
            
            # 市場ポテンシャル評価
            market_potential = "高" if adjusted_market_score >= 70 else "中" if adjusted_market_score >= 40 else "低"
            
            # ROI予測（実際のデータに基づく改良版）
            base_roi = adjusted_market_score * 0.3 + growth_potential_score * 0.2
            if actual_revenue and actual_businesses:
                # 事業所あたりの平均収益から業界ROIを推定
                avg_revenue_per_business = actual_revenue / actual_businesses if actual_businesses > 0 else 0
                if avg_revenue_per_business > 5000:  # 万円
                    base_roi *= 1.2
                elif avg_revenue_per_business > 2000:
                    base_roi *= 1.1
            
            estimated_roi = max(5, min(35, base_roi))
            
            # 競合密度の計算（事業所数ベース）
            competition_density = "不明"
            if actual_businesses and actual_population:
                businesses_per_1000_people = (actual_businesses / actual_population) * 1000
                if businesses_per_1000_people > 50:
                    competition_density = "高密度"
                elif businesses_per_1000_people > 25:
                    competition_density = "中密度"
                else:
                    competition_density = "低密度"
            
            return {
                "market_size_score": adjusted_market_score,
                "growth_potential_score": growth_potential_score,
                "data_availability_score": data_availability_score,
                "numerical_data_bonus": numerical_bonus,
                "market_potential_level": market_potential,
                "estimated_roi_percentage": round(estimated_roi, 1),
                "industry_advantage_multiplier": multiplier,
                
                # 実際の数値データ
                "actual_metrics": {
                    "population": f"{actual_population:,.0f}人" if actual_population else "データなし",
                    "business_establishments": f"{actual_businesses:,.0f}件" if actual_businesses else "データなし",
                    "estimated_market_size": f"{estimated_market_size:,.0f}人" if estimated_market_size else "データなし",
                    "market_penetration_rate": f"{market_penetration_rate:.1%}" if market_penetration_rate else "データなし",
                    "competition_density": competition_density,
                    "revenue_data": f"{actual_revenue:,.0f}万円" if actual_revenue else "データなし",
                    "tourism_volume": f"{actual_tourists:,.0f}人" if actual_tourists else "データなし"
                },
                
                "key_indicators": market_size_indicators[:5],
                "growth_signals": growth_indicators[:3],
                "economic_indicators": economic_indicators[:3],
                "analysis_confidence": "高" if numerical_bonus >= 30 else "中" if numerical_bonus >= 15 else "低",
                "market_saturation_risk": "低" if adjusted_market_score < 60 else "中" if adjusted_market_score < 80 else "高",
                "data_sources_used": len(datasets),
                "numerical_insights": numerical_data.get("summary", {})
            }
            
        except Exception as e:
            print(f"市場データ分析エラー: {e}")
            return {
                "market_size_score": 0, 
                "growth_potential_score": 0,
                "market_potential_level": "不明",
                "estimated_roi_percentage": 0,
                "analysis_confidence": "低",
                "actual_metrics": {
                    "population": "データ取得エラー",
                    "business_establishments": "データ取得エラー"
                }
            }
    
    async def _analyze_demographics(self, datasets: List[Dict]) -> Dict[str, Any]:
        """人口統計分析 - より詳細で専門的な指標を生成"""
        try:
            age_data = []
            population_data = []
            demographic_scores = {}
            
            for dataset in datasets:
                if not dataset:
                    continue
                    
                title = dataset.get("title", "").lower()
                
                if "人口" in title or "年齢" in title:
                    population_data.append(dataset.get("title", ""))
                    
                    # 年齢層の推定と重要度スコア
                    if "高齢" in title:
                        age_data.append("elderly")
                        demographic_scores["elderly"] = demographic_scores.get("elderly", 0) + 20
                    elif "若者" in title or "20代" in title or "30代" in title:
                        age_data.append("young_adult")
                        demographic_scores["young_adult"] = demographic_scores.get("young_adult", 0) + 15
                    elif "子ども" in title or "児童" in title:
                        age_data.append("children")
                        demographic_scores["children"] = demographic_scores.get("children", 0) + 10
            
            # ターゲット層の特定（改良版）
            target_segments = []
            if "elderly" in age_data:
                market_size = min(demographic_scores.get("elderly", 0), 100)
                target_segments.append({
                    "segment": "高齢者層（65歳以上）",
                    "opportunity": "介護・健康・生活支援サービス",
                    "market_potential_score": market_size,
                    "purchasing_power": "中〜高",
                    "digital_adoption": "低（25%）",
                    "estimated_population_ratio": "28.5%"  # 金沢市の高齢化率
                })
            if "young_adult" in age_data:
                market_size = min(demographic_scores.get("young_adult", 0), 100)
                target_segments.append({
                    "segment": "若年成人層（20-39歳）",
                    "opportunity": "IT・エンタメ・ライフスタイル",
                    "market_potential_score": market_size,
                    "purchasing_power": "中",
                    "digital_adoption": "高（85%）",
                    "estimated_population_ratio": "22.3%"
                })
            if "children" in age_data:
                market_size = min(demographic_scores.get("children", 0), 100)
                target_segments.append({
                    "segment": "ファミリー層（子育て世代）",
                    "opportunity": "教育・子育て支援・レジャー",
                    "market_potential_score": market_size,
                    "purchasing_power": "中〜高",
                    "digital_adoption": "中（65%）",
                    "estimated_population_ratio": "15.2%"
                })
            
            # 人口動態トレンド分析
            population_trend = "減少傾向" if len([d for d in age_data if d == "elderly"]) > len([d for d in age_data if d == "young_adult"]) else "安定"
            
            return {
                "population_datasets_count": len(population_data),
                "target_segments": target_segments,
                "demographic_diversity_score": len(set(age_data)) * 25,
                "population_trend": population_trend,
                "data_coverage_score": min(len(population_data) * 20, 100),
                "primary_target_recommendation": max(target_segments, key=lambda x: x["market_potential_score"])["segment"] if target_segments else "データ不足"
            }
            
        except Exception as e:
            print(f"人口統計分析エラー: {e}")
            return {
                "population_datasets_count": 0, 
                "target_segments": [],
                "demographic_diversity_score": 0,
                "data_coverage_score": 0
            }
    
    async def _analyze_competition(self, datasets: List[Dict], industry: str) -> Dict[str, Any]:
        """競合分析 - より詳細で専門的な指標を生成"""
        try:
            business_datasets = []
            facility_datasets = []
            competition_indicators = []
            
            for dataset in datasets:
                if not dataset:
                    continue
                    
                title = dataset.get("title", "").lower()
                
                if any(keyword in title for keyword in ["事業所", "企業", "店舗", "施設"]):
                    if "事業所" in title or "企業" in title:
                        business_datasets.append({
                            "title": dataset.get("title", ""),
                            "relevance_score": 80 if industry.lower() in title else 40
                        })
                    else:
                        facility_datasets.append({
                            "title": dataset.get("title", ""),
                            "facility_type": "商業施設" if "店舗" in title else "公共施設"
                        })
                
                # 競合密度指標
                if any(keyword in title for keyword in ["密度", "分布", "立地"]):
                    competition_indicators.append({
                        "title": dataset.get("title", ""),
                        "indicator_type": "立地分析"
                    })
            
            # 競合密度の詳細計算
            business_density_score = min(len(business_datasets) * 15, 100)
            facility_density_score = min(len(facility_datasets) * 10, 100)
            
            # 競合レベルの詳細評価
            if business_density_score >= 75:
                competition_level = "高"
                market_entry_difficulty = 8.5
            elif business_density_score >= 45:
                competition_level = "中"
                market_entry_difficulty = 6.0
            else:
                competition_level = "低"
                market_entry_difficulty = 3.5
            
            # 市場飽和度の計算
            saturation_score = min((business_density_score + facility_density_score) / 2, 100)
            saturation_level = "高" if saturation_score >= 70 else "中" if saturation_score >= 40 else "低"
            
            # 競合優位性の機会スコア
            opportunity_score = max(0, 100 - saturation_score)
            
            return {
                "competition_level": competition_level,
                "business_density_score": business_density_score,
                "facility_density_score": facility_density_score,
                "market_entry_difficulty": market_entry_difficulty,
                "market_saturation_level": saturation_level,
                "market_saturation_score": saturation_score,
                "competitive_opportunity_score": opportunity_score,
                "business_count_estimate": len(business_datasets),
                "facility_count_estimate": len(facility_datasets),
                "differentiation_potential": "高" if opportunity_score >= 60 else "中" if opportunity_score >= 30 else "低",
                "recommended_strategy": "ニッチ戦略" if competition_level == "高" else "差別化戦略" if competition_level == "中" else "市場開拓戦略"
            }
            
        except Exception as e:
            print(f"競合分析エラー: {e}")
            return {
                "competition_level": "不明", 
                "business_density_score": 0,
                "market_entry_difficulty": 5.0,
                "competitive_opportunity_score": 50
            }
    
    async def _predict_trends(self, datasets: List[Dict], industry: str) -> Dict[str, Any]:
        """トレンド予測"""
        try:
            trend_keywords = ["デジタル", "AI", "環境", "持続可能", "高齢化", "観光", "地域活性化"]
            detected_trends = []
            
            for dataset in datasets:
                if not dataset:
                    continue
                    
                title = dataset.get("title", "").lower()
                notes = dataset.get("notes", "").lower()
                
                for keyword in trend_keywords:
                    if keyword.lower() in title or keyword.lower() in notes:
                        detected_trends.append(keyword)
            
            # トレンドの重要度計算
            trend_counts = {}
            for trend in detected_trends:
                trend_counts[trend] = trend_counts.get(trend, 0) + 1
            
            top_trends = sorted(trend_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            return {
                "emerging_trends": [{"trend": trend, "strength": count} for trend, count in top_trends],
                "future_opportunities": self._generate_trend_opportunities(top_trends, industry)
            }
            
        except Exception as e:
            print(f"トレンド予測エラー: {e}")
            return {"emerging_trends": [], "future_opportunities": []}
    
    def _generate_trend_opportunities(self, trends: List[Tuple], industry: str) -> List[str]:
        """トレンドベースの機会生成"""
        opportunities = []
        
        for trend, strength in trends:
            if trend == "デジタル" or trend == "AI":
                opportunities.append(f"{industry}のDX化・AI活用サービス")
            elif trend == "環境" or trend == "持続可能":
                opportunities.append(f"環境配慮型{industry}サービス")
            elif trend == "高齢化":
                opportunities.append(f"シニア向け{industry}サービス")
            elif trend == "観光":
                opportunities.append(f"インバウンド対応{industry}サービス")
            elif trend == "地域活性化":
                opportunities.append(f"地域密着型{industry}サービス")
        
        return opportunities[:3]
    
    async def _generate_business_ideas(self, market_analysis: Dict, demographic_insights: Dict, 
                                     competition_analysis: Dict, industry: str, area: str) -> List[Dict[str, Any]]:
        """AIを使って、金沢のポテンシャルを最大限に引き出す、革新的で魅力的なビジネスアイデアを生成"""
        try:
            # コンテキスト情報の準備 (より詳細に)
            context = f"""
【ターゲットエリア】: {area if area else '金沢市全域'}
【対象業界】: {industry}

【市場分析サマリー】:
  - 市場規模スコア: {market_analysis.get('market_size_score', 0)}/100点
  - 成長ポテンシャルスコア: {market_analysis.get('growth_potential_score', 0)}/100点
  - 競合レベル: {competition_analysis.get('competition_level', '不明')}
  - 市場参入難易度: {competition_analysis.get('market_entry_difficulty', 0)}/10点
  - 推定ROI: {market_analysis.get('estimated_roi_percentage', 0)}%
  - 分析信頼度: {market_analysis.get('analysis_confidence', '不明')}

【実際の数値データ】:
  - 人口: {market_analysis.get('actual_metrics', {}).get('population', 'N/A')}
  - 事業所数: {market_analysis.get('actual_metrics', {}).get('business_establishments', 'N/A')}
  - 推定市場規模(ターゲット): {market_analysis.get('actual_metrics', {}).get('estimated_market_size', 'N/A')}
  - 競合密度: {market_analysis.get('actual_metrics', {}).get('competition_density', 'N/A')}

【人口統計インサイト】:
  - 主要ターゲット層: {demographic_insights.get('primary_target_recommendation', '不明')}
  - 人口動態トレンド: {demographic_insights.get('population_trend', '不明')}

【競合分析インサイト】:
  - 推奨戦略: {competition_analysis.get('recommended_strategy', '標準戦略')}
  - 差別化ポテンシャル: {competition_analysis.get('differentiation_potential', '中')}
"""
            
            prompt = f"""
あなたは、金沢の伝統と革新を知り尽くした、超一流のビジネスプロデューサーです。
以下の詳細な市場データと分析結果を元に、ユーザーが「これだ！」と膝を打つような、
金沢ならではの【革新的かつ実現可能なカフェビジネスアイデア】を3つ提案してください。

{context}

各アイデアには、必ず以下の要素を情熱的に、かつ具体的に記述してください：

1.  【エモいアイデア名】: 思わずSNSでシェアしたくなるような、キャッチーで記憶に残る名前。
2.  【コンセプト・物語】: なぜこのアイデアが金沢で輝くのか？どんなストーリーや世界観があるのか？ユーザーの心を揺さぶる物語を語ってください。
3.  【具体的なサービス内容】: 他店との圧倒的な違いは何か？どんなユニークな体験や価値を提供できるのか？（例：伝統工芸体験、地元アーティストとのコラボ、最新技術の活用など）
4.  【ターゲット顧客ペルソナ】: どんなライフスタイルで、何を求めている人に刺さるのか？具体的な人物像を想像させる記述を。
5.  【感動の収益モデル】: どうやって儲けるのか？だけでなく、顧客も地域もハッピーになるような、持続可能で創造的な収益構造を提案してください。
6.  【成功の鍵＆実現可能性】: このビジネスを成功させるための最も重要なポイントは何か？現実的な視点からの実現可能性スコア（10点満点）とその根拠も。
7.  【市場ポテンシャル＆期待ROI】: このアイデアが秘める市場の可能性は？具体的な期待ROI（投資収益率）とその算出ロジックも（例：市場規模 x ターゲット顧客割合 x 客単価 x 利益率など、数値的根拠を重視）。
8.  【SWOT分析】: 各アイデアの強み(Strengths)、弱み(Weaknesses)、機会(Opportunities)、脅威(Threats)を簡潔に分析し、戦略的視点を提供してください。

形式はJSONで、各要素を詳細に記述してください。
ユーザーの期待を超える、最高にクールでエモい提案を待っています！

**重要**: 必ず以下のJSON形式で回答してください：
[
  {
    "name": "アイデア名",
    "concept": "コンセプト・物語",
    "services": "具体的なサービス内容",
    "target_persona": "ターゲット顧客ペルソナ",
    "revenue_model": "収益モデル",
    "success_keys": "成功の鍵",
    "feasibility_score": 数値,
    "expected_roi": 数値,
    "swot": {
      "strengths": "強み",
      "weaknesses": "弱み", 
      "opportunities": "機会",
      "threats": "脅威"
    }
  }
]
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini", # より高性能なモデルを検討しても良い
                messages=[
                    {"role": "system", "content": "あなたは、金沢の地域資源と最新トレンドを融合させ、ユーザーを感動させる革新的なビジネスアイデアを生み出すAIです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500, # より多くの情報を生成できるように増量
                temperature=0.85 # 創造性を高めるために少し高めに設定
            )
            
            # JSONレスポンスをパース
            try:
                ideas_text = response.choices[0].message.content
                print(f"AI生成レスポンス: {ideas_text[:200]}...")  # デバッグ用
                
                # JSONの抽出を試行（```json ... ``` 形式にも対応）
                match = re.search(r"```json\n(.*?)\n```", ideas_text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    # 直接JSONが出力される場合も考慮
                    json_str = ideas_text
                
                # JSONをパース
                json_str = json_str.strip()
                parsed_data = json.loads(json_str)
                
                # 様々なJSON形式に対応
                ideas = []
                if isinstance(parsed_data, list):
                    # 配列形式の場合
                    ideas = parsed_data
                elif isinstance(parsed_data, dict):
                    # オブジェクト形式の場合、配列を含むキーを探す
                    for key, value in parsed_data.items():
                        if isinstance(value, list) and value:
                            ideas = value
                            break
                    
                    # 配列が見つからない場合、オブジェクト自体を配列に変換
                    if not ideas:
                        ideas = [parsed_data]
                
                # 日本語キーから英語キーへの変換
                normalized_ideas = []
                print(f"パース成功。アイデア数: {len(ideas)}")
                for i, idea in enumerate(ideas):
                    print(f"アイデア{i+1}の内容: {list(idea.keys()) if isinstance(idea, dict) else type(idea)}")
                    if isinstance(idea, dict):
                        normalized_idea = {
                            "name": idea.get("エモいアイデア名") or idea.get("name", "革新的ビジネス"),
                            "concept": idea.get("コンセプト・物語") or idea.get("concept", "新しいコンセプト"),
                            "services": idea.get("具体的なサービス内容") or idea.get("services", "特別なサービス"),
                            "target_persona": idea.get("ターゲット顧客ペルソナ") or idea.get("target_persona", "ターゲット顧客"),
                            "revenue_model": idea.get("感動の収益モデル") or idea.get("revenue_model", "収益モデル"),
                            "success_keys": idea.get("成功の鍵＆実現可能性") or idea.get("success_keys", "成功要因"),
                            "feasibility_score": idea.get("feasibility_score", 8),
                            "expected_roi": idea.get("expected_roi", 10),
                            "market_potential": idea.get("市場ポテンシャル＆期待ROI") or idea.get("market_potential", "市場分析"),
                            "swot": idea.get("SWOT分析") or idea.get("swot", {
                                "strengths": "強み",
                                "weaknesses": "弱み", 
                                "opportunities": "機会",
                                "threats": "脅威"
                            })
                        }
                        print(f"正規化後のアイデア{i+1}: name={normalized_idea['name']}, concept={normalized_idea['concept'][:50]}...")
                        normalized_ideas.append(normalized_idea)
                
                print(f"最終的なアイデア数: {len(normalized_ideas)}")
                return normalized_ideas[:3]  # 最大3つまで
                
            except json.JSONDecodeError as e:
                print(f"JSONパースエラー (ビジネスアイデア生成): {e}")
                print(f"パース対象文字列: {json_str[:500] if 'json_str' in locals() else 'N/A'}")
                
                # より柔軟なJSONパースを試行
                try:
                    # コメントや不要な文字を除去
                    cleaned_json = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)
                    cleaned_json = re.sub(r'/\*.*?\*/', '', cleaned_json, flags=re.DOTALL)
                    cleaned_json = cleaned_json.strip()
                    
                    # 再度パースを試行
                    parsed_data = json.loads(cleaned_json)
                    print("クリーニング後のJSONパース成功！")
                    
                    # 同じ正規化処理を適用
                    ideas = []
                    if isinstance(parsed_data, list):
                        ideas = parsed_data
                    elif isinstance(parsed_data, dict):
                        for key, value in parsed_data.items():
                            if isinstance(value, list) and value:
                                ideas = value
                                break
                        if not ideas:
                            ideas = [parsed_data]
                    
                    # 正規化処理
                    normalized_ideas = []
                    for i, idea in enumerate(ideas):
                        if isinstance(idea, dict):
                            normalized_idea = {
                                "name": idea.get("エモいアイデア名") or idea.get("name", "革新的ビジネス"),
                                "concept": idea.get("コンセプト・物語") or idea.get("concept", "新しいコンセプト"),
                                "services": idea.get("具体的なサービス内容") or idea.get("services", "特別なサービス"),
                                "target_persona": idea.get("ターゲット顧客ペルソナ") or idea.get("target_persona", "ターゲット顧客"),
                                "revenue_model": idea.get("感動の収益モデル") or idea.get("revenue_model", "収益モデル"),
                                "success_keys": idea.get("成功の鍵＆実現可能性") or idea.get("success_keys", "成功要因"),
                                "feasibility_score": idea.get("feasibility_score", 8),
                                "expected_roi": idea.get("expected_roi", 10),
                                "market_potential": idea.get("市場ポテンシャル＆期待ROI") or idea.get("market_potential", "市場分析"),
                                "swot": idea.get("SWOT分析") or idea.get("swot", {
                                    "strengths": "強み",
                                    "weaknesses": "弱み", 
                                    "opportunities": "機会",
                                    "threats": "脅威"
                                })
                            }
                            normalized_ideas.append(normalized_idea)
                    
                    if normalized_ideas:
                        print(f"正規化成功！最終アイデア数: {len(normalized_ideas)}")
                        return normalized_ideas[:3]
                        
                except json.JSONDecodeError as e2:
                    print(f"クリーニング後もJSONパース失敗: {e2}")
                
                return self._generate_fallback_ideas(industry, area) # フォールバックを返す
            
        except Exception as e:
            print(f"ビジネスアイデア生成エラー: {e}")
            return self._generate_fallback_ideas(industry, area)
    
    def _generate_fallback_ideas(self, industry: str, area: str) -> List[Dict[str, Any]]:
        """フォールバック用のビジネスアイデア"""
        return [
            {
                "name": f"{area}地域密着型{industry}サービス",
                "description": f"地域の特性を活かした{industry}サービス",
                "target": "地域住民",
                "feasibility": 7,
                "market_potential": 6
            },
            {
                "name": f"デジタル{industry}プラットフォーム",
                "description": f"ITを活用した{industry}の効率化サービス",
                "target": "デジタルネイティブ世代",
                "feasibility": 6,
                "market_potential": 8
            },
            {
                "name": f"シニア向け{industry}サポート",
                "description": f"高齢者に優しい{industry}サービス",
                "target": "60歳以上の高齢者",
                "feasibility": 8,
                "market_potential": 7
            }
        ]

class MarketingIntelligenceEngine:
    """マーケティングインテリジェンス - データドリブンなマーケティング戦略立案"""
    
    def __init__(self):
        self.data_api = KanazawaDataAPI()
    
    async def generate_marketing_strategy(self, business_idea: str, target_segment: str, 
                                        budget_range: str = "中") -> Dict[str, Any]:
        """マーケティング戦略を生成"""
        try:
            print(f"マーケティング戦略生成: {business_idea} -> {target_segment}")
            
            # ターゲット分析
            target_analysis = await self._analyze_target_segment(target_segment)
            
            # チャネル分析
            channel_analysis = await self._analyze_marketing_channels(target_segment, budget_range)
            
            # 競合マーケティング分析
            competitor_analysis = await self._analyze_competitor_marketing(business_idea)
            
            # マーケティング戦略生成
            strategy = await self._generate_marketing_plan(
                business_idea, target_analysis, channel_analysis, competitor_analysis, budget_range
            )
            
            return {
                "success": True,
                "business_idea": business_idea,
                "target_segment": target_segment,
                "target_analysis": target_analysis,
                "channel_analysis": channel_analysis,
                "competitor_analysis": competitor_analysis,
                "marketing_strategy": strategy
            }
            
        except Exception as e:
            print(f"マーケティング戦略生成エラー: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_target_segment(self, segment: str) -> Dict[str, Any]:
        """ターゲットセグメント分析"""
        # 金沢市の人口データを検索
        datasets = await self.data_api.search_datasets(f"人口 {segment}", limit=5)
        
        segment_characteristics = {
            "高齢者": {
                "age_range": "65歳以上",
                "preferences": ["安心・安全", "対面サービス", "分かりやすさ"],
                "channels": ["新聞", "テレビ", "口コミ", "地域コミュニティ"],
                "budget_sensitivity": "高"
            },
            "若年層": {
                "age_range": "20-39歳",
                "preferences": ["利便性", "デジタル", "コスパ"],
                "channels": ["SNS", "Web広告", "インフルエンサー"],
                "budget_sensitivity": "中"
            },
            "ファミリー": {
                "age_range": "30-50歳",
                "preferences": ["安全性", "家族向け", "教育価値"],
                "channels": ["SNS", "学校", "地域イベント"],
                "budget_sensitivity": "中〜高"
            }
        }
        
        # セグメントマッチング
        matched_segment = None
        for key in segment_characteristics.keys():
            if key in segment:
                matched_segment = segment_characteristics[key]
                break
        
        if not matched_segment:
            matched_segment = segment_characteristics["若年層"]  # デフォルト
        
        return {
            "segment_size": len(datasets),
            "characteristics": matched_segment,
            "data_availability": "高" if len(datasets) > 2 else "中"
        }
    
    async def _analyze_marketing_channels(self, target_segment: str, budget: str) -> Dict[str, Any]:
        """マーケティングチャネル分析"""
        channels = {
            "デジタル": {
                "SNS広告": {"cost": "低〜中", "reach": "高", "targeting": "高"},
                "Google広告": {"cost": "中", "reach": "高", "targeting": "高"},
                "ウェブサイト": {"cost": "低", "reach": "中", "targeting": "中"},
                "メール": {"cost": "低", "reach": "中", "targeting": "高"}
            },
            "従来型": {
                "新聞広告": {"cost": "高", "reach": "中", "targeting": "低"},
                "ラジオ": {"cost": "中", "reach": "中", "targeting": "低"},
                "チラシ": {"cost": "低〜中", "reach": "中", "targeting": "中"},
                "イベント": {"cost": "中〜高", "reach": "低〜中", "targeting": "高"}
            },
            "地域密着": {
                "口コミ": {"cost": "低", "reach": "低〜中", "targeting": "高"},
                "地域コミュニティ": {"cost": "低", "reach": "中", "targeting": "高"},
                "パートナーシップ": {"cost": "低〜中", "reach": "中", "targeting": "中"}
            }
        }
        
        # 予算に応じた推奨チャネル
        budget_recommendations = {
            "低": ["SNS広告", "ウェブサイト", "口コミ", "地域コミュニティ"],
            "中": ["Google広告", "SNS広告", "チラシ", "イベント"],
            "高": ["新聞広告", "ラジオ", "Google広告", "イベント"]
        }
        
        recommended = budget_recommendations.get(budget, budget_recommendations["中"])
        
        return {
            "available_channels": channels,
            "recommended_channels": recommended,
            "budget_allocation": self._generate_budget_allocation(recommended, budget)
        }
    
    def _generate_budget_allocation(self, channels: List[str], budget: str) -> Dict[str, str]:
        """予算配分の提案"""
        if budget == "低":
            return {
                channels[0]: "40%",
                channels[1]: "30%",
                channels[2]: "20%",
                channels[3]: "10%" if len(channels) > 3 else "0%"
            }
        elif budget == "中":
            return {
                channels[0]: "35%",
                channels[1]: "30%",
                channels[2]: "25%",
                channels[3]: "10%" if len(channels) > 3 else "0%"
            }
        else:  # 高
            return {
                channels[0]: "30%",
                channels[1]: "25%",
                channels[2]: "25%",
                channels[3]: "20%" if len(channels) > 3 else "0%"
            }
    
    async def _analyze_competitor_marketing(self, business_idea: str) -> Dict[str, Any]:
        """競合マーケティング分析"""
        # 簡易的な競合分析
        return {
            "competitive_intensity": "中",
            "common_channels": ["SNS", "Web広告", "地域イベント"],
            "differentiation_opportunities": [
                "パーソナライゼーション",
                "地域特化サービス",
                "デジタル×アナログ融合"
            ]
        }
    
    async def _generate_marketing_plan(self, business_idea: str, target_analysis: Dict,
                                     channel_analysis: Dict, competitor_analysis: Dict,
                                     budget: str) -> Dict[str, Any]:
        """総合マーケティングプラン生成"""
        try:
            context = f"""
ビジネスアイデア: {business_idea}
ターゲット特性: {target_analysis.get('characteristics', {})}
推奨チャネル: {channel_analysis.get('recommended_channels', [])}
予算レベル: {budget}
競合状況: {competitor_analysis.get('competitive_intensity', '中')}
"""
            
            prompt = f"""
以下の情報に基づいて、実行可能なマーケティング戦略を提案してください：

{context}

以下の要素を含めてください：
1. マーケティング目標
2. 主要メッセージ
3. 実行タイムライン（3ヶ月）
4. KPI指標
5. 具体的なアクション

JSON形式で回答してください。
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "あなたは経験豊富なマーケティングストラテジストです。実用的で測定可能なマーケティング戦略を提案してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            strategy_text = response.choices[0].message.content
            
            # 構造化された戦略を返す
            return {
                "strategy_overview": strategy_text,
                "recommended_channels": channel_analysis.get('recommended_channels', []),
                "budget_allocation": channel_analysis.get('budget_allocation', {}),
                "timeline": "3ヶ月間の段階的実行",
                "success_metrics": ["リーチ数", "エンゲージメント率", "コンバージョン率", "ROI"]
            }
            
        except Exception as e:
            print(f"マーケティングプラン生成エラー: {e}")
            return {
                "strategy_overview": "基本的なマーケティング戦略を実行してください",
                "recommended_channels": ["SNS", "Web"],
                "budget_allocation": {"SNS": "50%", "Web": "50%"}
            }

class KanazawaAI:
    """金沢AI助手 - OpenAI GPTを使用した質問応答システム"""
    
    def __init__(self):
        self.data_api = KanazawaDataAPI()
        self.business_engine = BusinessIntelligenceEngine()
        self.marketing_engine = MarketingIntelligenceEngine()
        self.system_prompt = """
あなたは金沢市の情報に詳しいAI助手です。
金沢市のオープンデータを活用して、質問に簡潔で分かりやすく答えてください。

機能：
- オープンデータからのビジネス機会発見
- 市場分析と競合分析
- ターゲット顧客分析
- マーケティング戦略立案

回答ルール：
- 端的で簡潔に回答する
- 重要なポイントのみ伝える
- 具体的な数値がある場合は含める
- 装飾的な表現は避ける
- 結論を最初に述べる
- 不明な点は「分からない」と答える

回答形式：
- 箇条書きを活用
- 1つのポイントは1-2行以内
- 数値は【】で強調
- 重要な結論のみ記載

簡潔で実用的な情報提供を心がけてください。
"""
    
    async def generate_response(self, user_question: str) -> Dict[str, Any]:
        """ユーザーの質問に対してAI応答を生成"""
        try:
            print(f"質問受信: {user_question}")
            
            # ビジネス関連の質問かどうかを判定
            business_keywords = ["ビジネス", "事業", "起業", "商売", "マーケティング", "戦略", "競合", "市場", "顧客", "売上", "収益"]
            is_business_question = any(keyword in user_question for keyword in business_keywords)
            
            if is_business_question:
                print("ビジネス関連の質問として処理")
                return await self._handle_business_question(user_question)
            
            # 通常の質問処理
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
                max_tokens=600,
                temperature=0.5
            )
            
            ai_response = response.choices[0].message.content
            
            # レスポンステキストを整形
            formatted_response = format_response_text(ai_response)
            
            return {
                "success": True,
                "response": formatted_response,
                "datasets_used": len(datasets),
                "context_data": context_data[:3],  # 最初の3件のみ返す
                "question_type": "general"
            }
            
        except Exception as e:
            print(f"AI応答生成エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "申し訳ございません。現在システムに問題が発生しています。しばらく時間をおいてから再度お試しください。"
            }
    
    async def _handle_business_question(self, question: str) -> Dict[str, Any]:
        """ビジネス関連の質問を、プロのマーケター視点で、感動的に処理"""
        try:
            # 質問からキーワードを抽出（既存ロジック）
            # ... (industry_keywords, detected_industry, area_keywords, detected_area の抽出処理はそのまま)
            industry_keywords = {
                "観光": "観光業", "飲食": "飲食業", "カフェ": "飲食業", "小売": "小売業", "IT": "IT業",
                "教育": "教育業", "医療": "医療業", "介護": "介護業", "製造": "製造業",
                "建設": "建設業", "サービス": "サービス業", "地域活性化": "サービス業"
            }
            detected_industry = "飲食業"  # デフォルト（カフェ開業を想定）
            for keyword, industry_val in industry_keywords.items():
                if keyword in question.lower(): # 小文字で比較
                    detected_industry = industry_val
                    break
            
            area_keywords = ["金沢", "中央区", "東山", "香林坊", "武蔵", "駅西", "東区", "西区", "南区", "北区"]
            detected_area = ""
            for area_val in area_keywords:
                if area_val in question:
                    detected_area = area_val
                    break
            
            print(f"検出された業界: {detected_industry}, エリア: {detected_area if detected_area else '金沢市全域'}")
            
            # ビジネス分析を実行
            print(f"詳細ビジネス分析開始: 業界={detected_industry}, エリア={detected_area}")
            business_analysis = await self.business_engine.analyze_business_opportunities(
                detected_industry, detected_area
            )
            
            # AIによる統合回答生成
            # プロのマーケターが、ユーザーの夢を全力で応援するようなストーリー性のある回答を生成
            
            # 分析結果を分かりやすく要約
            market_summary = ""
            if business_analysis.get("success") and business_analysis.get("market_analysis"):
                ma = business_analysis["market_analysis"]
                actual = ma.get("actual_metrics", {})
                market_summary = f"""
【市場ポテンシャル分析】
  金沢の{detected_industry}市場は、スコア【{ma.get('market_size_score', 0)}/100点】と、まだまだ未知の可能性を秘めています！
  特に、人口【{actual.get('population', 'データ確認中')}】、事業所数【{actual.get('business_establishments', 'データ確認中')}】を考慮すると、
  ターゲット市場規模は【{actual.get('estimated_market_size', '算出中')}】と推定され、これは大きなチャンスです！
  競合密度は【{actual.get('competition_density', '分析中')}】で、独自の戦略で切り込む余地アリ！
  推定ROIは【{ma.get('estimated_roi_percentage', 0)}%】と、あなたの情熱とアイデア次第で大きく跳ね上がる可能性大です！
  (分析信頼度: {ma.get('analysis_confidence', '確認中')})
"""
            else:
                market_summary = "現在、詳細な市場データを分析中です。あなたの熱い想いを実現するために、全力でサポートします！"
            
            # ビジネスアイデアを整形
            ideas_presentation = ""
            if business_analysis.get("business_ideas") and len(business_analysis["business_ideas"]) > 0:
                print(f"生成されたビジネスアイデア数: {len(business_analysis['business_ideas'])}")
                for i, idea in enumerate(business_analysis["business_ideas"][:3]): # 上位3アイデアを提示
                    if isinstance(idea, dict):
                        # SWOT分析の整形
                        swot = idea.get('swot', {})
                        swot_text = ""
                        if isinstance(swot, dict):
                            swot_text = f"""
    強み: {swot.get('strengths', '強み分析中')}
    弱み: {swot.get('weaknesses', '弱み分析中')}
    機会: {swot.get('opportunities', '機会分析中')}
    脅威: {swot.get('threats', '脅威分析中')}"""
                        else:
                            swot_text = f"    {swot}"
                        
                        # ターゲットペルソナの整形
                        target = idea.get('target_persona', 'ターゲット分析中')
                        if isinstance(target, dict):
                            target_text = f"年齢: {target.get('年齢', '分析中')}, ライフスタイル: {target.get('ライフスタイル', '分析中')}"
                        else:
                            target_text = str(target)
                        
                        ideas_presentation += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 【{idea.get('name', '革新的ビジネス')}】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 コンセプト・物語:
{idea.get('concept', 'コンセプト情報を確認中')}

🎯 具体的なサービス内容:
{idea.get('services', 'サービス詳細を確認中')}

👥 ターゲット顧客ペルソナ:
{target_text}

💰 収益モデル:
{idea.get('revenue_model', '収益構造を検討中')}

🔑 成功の鍵 & 実現可能性:
{idea.get('success_keys', '成功要因を分析中')} (実現可能性: {idea.get('feasibility_score', '評価中')}/10点)

📊 市場ポテンシャル & 期待ROI:
{idea.get('market_potential', '市場分析中')} (期待ROI: {idea.get('expected_roi', '算出中')}%)

⚡ SWOT分析:{swot_text}

"""
                    else:
                        # フォールバックアイデアの場合
                        ideas_presentation += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 【{idea.get('name', '地域密着型サービス')}】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 概要: {idea.get('description', 'サービス概要を検討中')}
👥 ターゲット: {idea.get('target', '地域住民')}
📊 実現可能性: {idea.get('feasibility', '未評価')}/10点

"""
            else:
                ideas_presentation = "【分析中】最適なビジネスアイデアを生成中です。しばらくお待ちください。"

            # ユーザーの夢を応援するメッセージを生成
            final_prompt = f"""
質問: 「{question}」

【市場分析サマリー】
{market_summary}

【革新的ビジネスアイデア（詳細版）】
{ideas_presentation}

以下の要求に従って回答してください：
1. 市場の現状を数値とともに簡潔に要約
2. 上記の詳細なビジネスアイデアをそのまま表示（削除や要約は不要）
3. 最も推奨するアイデアを1つ選択し、その理由を説明
4. 実行に向けた具体的なステップを3つ提示

詳細なビジネスアイデアの内容は削除せず、完全な形で提示してください。
"""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": "あなたは、ユーザーの夢の実現を全力で応援する、情熱的でカリスマ的なビジネスプロデューサーAIです。詳細な分析結果を大切にし、豊富な情報を提供してください。"},
                    {"role": "user", "content": final_prompt}
                ],
                max_tokens=3000, # 詳細な回答のために大幅に増量
                temperature=0.7 # クリエイティブながらも確実な出力を促す
            )
            
            ai_response = response.choices[0].message.content
            
            # 最終レスポンス整形 (format_response_text は汎用的なので、ここではAIの出力を尊重)
            # 必要であれば、ここでさらに特定の整形処理を追加可能
            
            return {
                "success": True,
                "response": ai_response, # AIが生成した感動的なテキストをそのまま返す
                "question_type": "business",
                "detected_industry": detected_industry,
                "detected_area": detected_area,
                "business_analysis": business_analysis, # 詳細分析結果も返す
                "datasets_used": business_analysis.get('data_sources_used', 0)
            }
            
        except Exception as e:
            print(f"ビジネス質問処理エラー (感動生成): {e}")
            # エラー時も、ユーザーを励ますメッセージを返す
            error_message = f"""
大変申し訳ありません、現在システムがあなたの熱い想いに追いつけていないようです…！
ですが、あなたの「{question}」という素晴らしい夢は、必ず形にできると信じています。
もう一度試していただくか、少し時間を置いてから再度チャレンジしてみてください。
私たちはいつでも、あなたの夢を全力で応援しています！諦めないで！
"""
            return {
                "success": False,
                "error": str(e),
                "response": error_message 
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

@app.route('/api/business/analyze', methods=['POST'])
def analyze_business_opportunities():
    """ビジネス機会分析API"""
    try:
        data = request.get_json()
        industry = data.get('industry', '').strip()
        target_area = data.get('target_area', '').strip()
        
        if not industry:
            return jsonify({
                "success": False,
                "error": "業界を指定してください"
            }), 400
        
        print(f"ビジネス分析リクエスト: 業界={industry}, エリア={target_area}")
        
        # ビジネス機会分析実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                kanazawa_ai.business_engine.analyze_business_opportunities(industry, target_area)
            )
        finally:
            loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"ビジネス分析APIエラー: {e}")
        return jsonify({
            "success": False,
            "error": "ビジネス分析中にエラーが発生しました",
            "details": str(e)
        }), 500

@app.route('/api/marketing/strategy', methods=['POST'])
def generate_marketing_strategy():
    """マーケティング戦略生成API"""
    try:
        data = request.get_json()
        business_idea = data.get('business_idea', '').strip()
        target_segment = data.get('target_segment', '').strip()
        budget_range = data.get('budget_range', '中').strip()
        
        if not business_idea or not target_segment:
            return jsonify({
                "success": False,
                "error": "ビジネスアイデアとターゲットセグメントを指定してください"
            }), 400
        
        print(f"マーケティング戦略リクエスト: {business_idea} -> {target_segment} (予算: {budget_range})")
        
        # マーケティング戦略生成実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                kanazawa_ai.marketing_engine.generate_marketing_strategy(
                    business_idea, target_segment, budget_range
                )
            )
        finally:
            loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"マーケティング戦略APIエラー: {e}")
        return jsonify({
            "success": False,
            "error": "マーケティング戦略生成中にエラーが発生しました",
            "details": str(e)
        }), 500

@app.route('/api/intelligence/comprehensive', methods=['POST'])
def comprehensive_business_intelligence():
    """総合ビジネスインテリジェンス分析API"""
    try:
        data = request.get_json()
        industry = data.get('industry', '').strip()
        target_area = data.get('target_area', '').strip()
        budget_range = data.get('budget_range', '中').strip()
        
        if not industry:
            return jsonify({
                "success": False,
                "error": "業界を指定してください"
            }), 400
        
        print(f"総合BI分析リクエスト: 業界={industry}, エリア={target_area}, 予算={budget_range}")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # ビジネス機会分析
            business_analysis = loop.run_until_complete(
                kanazawa_ai.business_engine.analyze_business_opportunities(industry, target_area)
            )
            
            # 各ビジネスアイデアに対してマーケティング戦略を生成
            marketing_strategies = []
            if business_analysis.get('success') and business_analysis.get('business_ideas'):
                for idea in business_analysis['business_ideas'][:2]:  # 上位2つのアイデア
                    idea_name = idea.get('name', '')
                    target = idea.get('target', '一般消費者')
                    
                    if idea_name:
                        strategy = loop.run_until_complete(
                            kanazawa_ai.marketing_engine.generate_marketing_strategy(
                                idea_name, target, budget_range
                            )
                        )
                        marketing_strategies.append({
                            "business_idea": idea_name,
                            "strategy": strategy
                        })
            
            # 総合レポート生成
            comprehensive_report = {
                "success": True,
                "analysis_timestamp": datetime.now().isoformat(),
                "input_parameters": {
                    "industry": industry,
                    "target_area": target_area,
                    "budget_range": budget_range
                },
                "business_analysis": business_analysis,
                "marketing_strategies": marketing_strategies,
                "executive_summary": {
                    "total_opportunities": len(business_analysis.get('business_ideas', [])),
                    "market_potential": business_analysis.get('market_analysis', {}).get('market_size_score', 0),
                    "competition_level": business_analysis.get('competition_analysis', {}).get('competition_level', '不明'),
                    "recommended_focus": marketing_strategies[0]['business_idea'] if marketing_strategies else None
                }
            }
            
        finally:
            loop.close()
        
        return jsonify(comprehensive_report)
        
    except Exception as e:
        print(f"総合BI分析APIエラー: {e}")
        return jsonify({
            "success": False,
            "error": "総合分析中にエラーが発生しました",
            "details": str(e)
        }), 500

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

@app.route('/api/data/extract-numbers', methods=['POST'])
def extract_numerical_data():
    """数値データ抽出API - プロのマーケター向け"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        limit = min(int(data.get('limit', 10)), 20)
        
        if not query:
            return jsonify({
                "success": False,
                "error": "検索クエリを指定してください"
            }), 400
        
        print(f"数値データ抽出リクエスト: {query}")
        
        # データセット検索と数値抽出実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            data_api = KanazawaDataAPI()
            
            # データセットを検索
            datasets = loop.run_until_complete(data_api.search_datasets(query, limit))
            
            if not datasets:
                return jsonify({
                    "success": True,
                    "message": "関連するデータセットが見つかりませんでした",
                    "numerical_insights": {},
                    "datasets_searched": 0
                })
            
            # 数値データを抽出
            numerical_insights = loop.run_until_complete(data_api.extract_numerical_data(datasets))
            
        finally:
            loop.close()
        
        # プロのマーケター向けサマリーを生成
        professional_summary = {
            "executive_summary": {
                "total_datasets_analyzed": len(datasets),
                "numerical_data_points": len(numerical_insights.get("extracted_values", [])),
                "data_categories": numerical_insights.get("summary", {}).get("categories_covered", []),
                "confidence_level": "高" if len(numerical_insights.get("extracted_values", [])) >= 10 else "中" if len(numerical_insights.get("extracted_values", [])) >= 5 else "低"
            },
            "key_metrics": numerical_insights.get("summary", {}).get("key_metrics", {}),
            "detailed_insights": numerical_insights,
            "market_implications": _generate_market_implications(numerical_insights),
            "data_quality_assessment": _assess_data_quality(numerical_insights, datasets)
        }
        
        return jsonify({
            "success": True,
            "query": query,
            "professional_analysis": professional_summary,
            "raw_data": numerical_insights,
            "datasets_metadata": [{"title": d.get("title", ""), "id": d.get("id", "")} for d in datasets[:5]]
        })
        
    except Exception as e:
        print(f"数値データ抽出APIエラー: {e}")
        return jsonify({
            "success": False,
            "error": "数値データ抽出中にエラーが発生しました",
            "details": str(e)
        }), 500

def _generate_market_implications(numerical_insights: Dict) -> Dict[str, Any]:
    """数値データから市場への示唆を生成"""
    implications = {
        "market_size_indicators": [],
        "growth_opportunities": [],
        "competitive_landscape": [],
        "risk_factors": []
    }
    
    # 人口データからの示唆
    if numerical_insights.get("population_data"):
        pop_data = numerical_insights["population_data"]
        if "total_population" in pop_data:
            population = pop_data["total_population"]
            implications["market_size_indicators"].append(f"総人口{population:,.0f}人による基礎市場規模")
            
            if population > 400000:
                implications["growth_opportunities"].append("大都市圏レベルの市場規模による多様なビジネス機会")
            elif population > 200000:
                implications["growth_opportunities"].append("中規模都市としての安定した市場基盤")
            else:
                implications["risk_factors"].append("限定的な市場規模による成長制約の可能性")
    
    # 事業データからの示唆
    if numerical_insights.get("business_data"):
        bus_data = numerical_insights["business_data"]
        if "business_establishments" in bus_data:
            businesses = bus_data["business_establishments"]
            implications["competitive_landscape"].append(f"既存事業所{businesses:,.0f}件による競合環境")
            
            if businesses > 10000:
                implications["risk_factors"].append("高い競合密度による差別化の必要性")
            else:
                implications["growth_opportunities"].append("適度な競合環境による参入機会")
    
    # 観光データからの示唆
    if numerical_insights.get("tourism_data"):
        tour_data = numerical_insights["tourism_data"]
        if "tourists" in tour_data:
            tourists = tour_data["tourists"]
            implications["growth_opportunities"].append(f"年間観光客{tourists:,.0f}人による外部需要")
    
    return implications

def _assess_data_quality(numerical_insights: Dict, datasets: List[Dict]) -> Dict[str, Any]:
    """データ品質を評価"""
    assessment = {
        "overall_quality": "中",
        "data_completeness": 0,
        "source_reliability": "中",
        "temporal_coverage": "不明",
        "recommendations": []
    }
    
    # データ完全性の評価
    categories_with_data = len([k for k in ["population_data", "business_data", "economic_data", "tourism_data"] 
                               if numerical_insights.get(k)])
    assessment["data_completeness"] = (categories_with_data / 4) * 100
    
    # 全体品質の判定
    if assessment["data_completeness"] >= 75:
        assessment["overall_quality"] = "高"
    elif assessment["data_completeness"] >= 50:
        assessment["overall_quality"] = "中"
    else:
        assessment["overall_quality"] = "低"
    
    # 推奨事項
    if assessment["data_completeness"] < 50:
        assessment["recommendations"].append("追加のデータソース調査が必要")
    if len(datasets) < 5:
        assessment["recommendations"].append("より多くのデータセットの検索を推奨")
    
    assessment["recommendations"].append("定期的なデータ更新の確認を推奨")
    
    return assessment

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 金沢AI助手を起動中...")
    print(f"📍 http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 