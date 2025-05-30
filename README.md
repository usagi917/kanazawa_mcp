# 🏯 金沢AI助手

金沢市のオープンデータを活用したAI搭載チャットボットアプリケーション

![金沢AI助手](https://img.shields.io/badge/金沢AI助手-v1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.3.3-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5--turbo-orange)

## 🎯 概要

**金沢AI助手**は、金沢市が提供するオープンデータを活用して、市民や観光客の質問にAIが答えるWebアプリケーションです。

### 主な機能

- 🤖 **AI搭載チャットボット**: OpenAI GPT-3.5-turboを使用した自然言語処理
- 📊 **リアルタイムデータアクセス**: 金沢市CKAN APIから300+のデータセットを検索
- 📱 **レスポンシブデザイン**: PC・タブレット・スマートフォン対応
- ⚡ **高速レスポンス**: 平均2秒以内のAPI応答時間
- 🎨 **モダンUI**: グラデーション・アニメーション・ダークモード対応

### 対応する質問例

- 「金沢市の人口は？」
- 「おすすめの観光スポットを教えて」
- 「金沢市の公園一覧」
- 「ゴミの出し方について」
- 「金沢駅周辺の駐車場情報」
- 「市役所の営業時間は？」

## 🛠️ 技術スタック

### フロントエンド
- **HTML5 + CSS3 + Vanilla JavaScript**
- **Google Fonts** (Noto Sans JP)
- **Font Awesome** (アイコン)
- **CSS Grid & Flexbox** (レイアウト)

### バックエンド
- **Python 3.8+**
- **Flask 2.3.3** (Webフレームワーク)
- **Flask-CORS** (CORS対応)
- **httpx** (非同期HTTPクライアント)
- **OpenAI API** (GPT-3.5-turbo)
- **python-dotenv** (環境変数管理)

### データソース
- **金沢市CKAN API**: `catalog-data.city.kanazawa.ishikawa.jp`
- **300+ オープンデータセット**
- **Creative Commons Attribution ライセンス**

## 📁 プロジェクト構造

```
kanazawa_mpc/
├── backend/
│   ├── app.py              # メインFlaskアプリケーション
│   ├── requirements.txt    # Python依存関係
│   └── .env.example       # 環境変数テンプレート
├── frontend/
│   └── index.html         # メインHTMLファイル
├── static/                # 静的ファイル（将来使用）
├── templates/             # テンプレートファイル（将来使用）
├── .cursor/
│   └── rules/             # Cursor Rules
├── README.md              # このファイル
├── Procfile              # Herokuデプロイ用
├── runtime.txt           # Python バージョン指定
└── vercel.json           # Vercelデプロイ用
```

## 🚀 セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/kanazawa_mpc.git
cd kanazawa_mpc
```

### 2. Python仮想環境の作成

```bash
# 仮想環境作成
python -m venv venv

# 仮想環境有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. 依存関係のインストール

```bash
pip install -r backend/requirements.txt
```

### 4. 環境変数の設定

```bash
# .envファイルを作成
cp backend/.env.example backend/.env

# .envファイルを編集してOpenAI APIキーを設定
# OPENAI_API_KEY=your-api-key-here
```

### 5. OpenAI APIキーの取得

1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウント作成・ログイン
3. API Keysページでキーを生成
4. `.env`ファイルに設定

### 6. アプリケーションの起動

```bash
cd backend
python app.py
```

アプリケーションは `http://localhost:5000` で起動します。

## 🌐 デプロイ

### Heroku

```bash
# Heroku CLIインストール後
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your-api-key
git push heroku main
```

### Vercel

```bash
# Vercel CLIインストール後
vercel
# 環境変数をVercelダッシュボードで設定
```

## 📊 API仕様

### チャットAPI

**エンドポイント**: `POST /api/chat`

**リクエスト**:
```json
{
  "message": "金沢市の人口は？"
}
```

**レスポンス**:
```json
{
  "success": true,
  "response": "金沢市の人口は約46万人です...",
  "datasets_used": 3,
  "context_data": [...]
}
```

### データセット検索API

**エンドポイント**: `GET /api/datasets/search?q=人口&limit=10`

**レスポンス**:
```json
{
  "success": true,
  "datasets": [...],
  "count": 5
}
```

### ヘルスチェックAPI

**エンドポイント**: `GET /api/health`

**レスポンス**:
```json
{
  "status": "healthy",
  "service": "金沢AI助手",
  "version": "1.0.0"
}
```

## 🔧 開発ガイド

### コーディングスタイル

- **Python**: PEP 8準拠、型ヒント使用
- **JavaScript**: ES6+、async/await使用
- **CSS**: BEM記法、CSS Grid/Flexbox活用
- **HTML**: セマンティックHTML、アクセシビリティ配慮

### 命名規則

- **ファイル名**: kebab-case
- **クラス名**: PascalCase
- **関数名**: snake_case (Python), camelCase (JavaScript)
- **変数名**: snake_case (Python), camelCase (JavaScript)

### テスト実行

```bash
# 単体テスト（将来実装）
python -m pytest tests/

# フロントエンドテスト（将来実装）
npm test
```

## 📈 パフォーマンス指標

### 目標KPI

- **DAU**: 50人/日
- **セッション時間**: 3分以上
- **質問数**: 100回/日
- **API応答時間**: < 2秒
- **稼働率**: > 99%
- **エラー率**: < 1%

### 監視項目

- API応答時間
- エラー率
- データセット検索成功率
- OpenAI API使用量
- サーバーリソース使用率

## 🔐 セキュリティ

- **HTTPS通信**: SSL/TLS暗号化
- **API制限**: レート制限設定
- **ログ管理**: 個人情報除外
- **環境変数**: 機密情報の適切な管理

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

### データライセンス

- **金沢市オープンデータ**: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja)
- **利用規約**: [金沢市オープンデータ利用規約](https://catalog-data.city.kanazawa.ishikawa.jp/pages/terms)

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/your-username/kanazawa_mpc/issues)
- **Email**: your-email@example.com
- **Documentation**: [Wiki](https://github.com/your-username/kanazawa_mpc/wiki)

## 🙏 謝辞

- **金沢市**: オープンデータの提供
- **OpenAI**: GPT-3.5-turbo API
- **Flask Community**: 素晴らしいWebフレームワーク
- **Contributors**: プロジェクトへの貢献

---

**Made with ❤️ for 金沢市** 