#!/usr/bin/env python3
"""
金沢ビジネスインテリジェンス機能テストスクリプト
新しく追加されたビジネス分析とマーケティング機能をテストします
"""

import requests
import json
import time
from typing import Dict, Any

class BusinessIntelligenceTester:
    """ビジネスインテリジェンス機能のテスター"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        
    def test_business_analysis(self) -> None:
        """ビジネス機会分析のテスト"""
        print("🔍 ビジネス機会分析テスト開始...")
        
        test_cases = [
            {"industry": "観光業", "target_area": "金沢"},
            {"industry": "飲食業", "target_area": "中央区"},
            {"industry": "IT業", "target_area": ""},
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📊 テストケース {i}: {case}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/business/analyze",
                    json=case,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 成功: {result.get('datasets_analyzed', 0)}件のデータセット分析")
                    print(f"   市場スコア: {result.get('market_analysis', {}).get('market_size_score', 0)}")
                    print(f"   ビジネスアイデア数: {len(result.get('business_ideas', []))}")
                else:
                    print(f"❌ エラー: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ 例外エラー: {e}")
            
            time.sleep(2)  # API負荷軽減
    
    def test_marketing_strategy(self) -> None:
        """マーケティング戦略生成のテスト"""
        print("\n🎯 マーケティング戦略生成テスト開始...")
        
        test_cases = [
            {
                "business_idea": "金沢観光ガイドアプリ",
                "target_segment": "若年層",
                "budget_range": "中"
            },
            {
                "business_idea": "地域密着型カフェ",
                "target_segment": "ファミリー層",
                "budget_range": "低"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📈 テストケース {i}: {case['business_idea']}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/marketing/strategy",
                    json=case,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 成功: マーケティング戦略生成完了")
                    strategy = result.get('marketing_strategy', {})
                    print(f"   推奨チャネル: {strategy.get('recommended_channels', [])}")
                    print(f"   予算配分: {strategy.get('budget_allocation', {})}")
                else:
                    print(f"❌ エラー: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ 例外エラー: {e}")
            
            time.sleep(2)
    
    def test_comprehensive_analysis(self) -> None:
        """総合ビジネスインテリジェンス分析のテスト"""
        print("\n🚀 総合BI分析テスト開始...")
        
        test_case = {
            "industry": "観光業",
            "target_area": "金沢",
            "budget_range": "中"
        }
        
        print(f"📋 テストケース: {test_case}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/intelligence/comprehensive",
                json=test_case,
                timeout=60  # 総合分析は時間がかかる
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功: 総合分析完了")
                
                summary = result.get('executive_summary', {})
                print(f"   総機会数: {summary.get('total_opportunities', 0)}")
                print(f"   市場ポテンシャル: {summary.get('market_potential', 0)}")
                print(f"   競合レベル: {summary.get('competition_level', '不明')}")
                print(f"   推奨フォーカス: {summary.get('recommended_focus', 'なし')}")
                
                # 詳細結果をファイルに保存
                with open('comprehensive_analysis_result.json', 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print("   📄 詳細結果を comprehensive_analysis_result.json に保存")
                
            else:
                print(f"❌ エラー: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 例外エラー: {e}")
    
    def test_business_chat(self) -> None:
        """ビジネス関連チャット機能のテスト"""
        print("\n💬 ビジネスチャット機能テスト開始...")
        
        test_questions = [
            "金沢でカフェを開業したいのですが、どんなビジネス機会がありますか？",
            "観光業でマーケティング戦略を考えています",
            "IT企業を金沢で起業する際の市場状況を教えて"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n💭 質問 {i}: {question}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={"message": question},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 成功: {result.get('question_type', 'general')}タイプとして処理")
                    print(f"   回答: {result.get('response', '')[:100]}...")
                    
                    if result.get('question_type') == 'business':
                        print(f"   検出業界: {result.get('detected_industry', '不明')}")
                        print(f"   検出エリア: {result.get('detected_area', '不明')}")
                else:
                    print(f"❌ エラー: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ 例外エラー: {e}")
            
            time.sleep(2)
    
    def run_all_tests(self) -> None:
        """全テストを実行"""
        print("🎉 金沢ビジネスインテリジェンス機能テスト開始！")
        print("=" * 60)
        
        # サーバーの生存確認
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ サーバー接続確認完了")
            else:
                print("❌ サーバーに接続できません")
                return
        except Exception as e:
            print(f"❌ サーバー接続エラー: {e}")
            return
        
        # 各テストを実行
        self.test_business_analysis()
        self.test_marketing_strategy()
        self.test_comprehensive_analysis()
        self.test_business_chat()
        
        print("\n" + "=" * 60)
        print("🎊 全テスト完了！結果を確認してください。")

def main():
    """メイン関数"""
    print("金沢ビジネスインテリジェンス機能テスター")
    print("使用方法: python test_business_intelligence.py")
    print("注意: サーバーが http://localhost:5000 で起動している必要があります\n")
    
    tester = BusinessIntelligenceTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 