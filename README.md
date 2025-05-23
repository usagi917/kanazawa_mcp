# 🌸 金沢市なんでもチャット 💬

金沢市の観光情報、交通情報、ごみ収集情報を簡単に検索できるAIチャットボットアプリです。

## ✨ 特徴

- 🏛️ **観光スポット検索** - 金沢市内の観光地や名所を簡単検索
- 🚌 **交通情報** - バス停や駅の情報を瞬時に取得
- 🗑️ **ごみ収集スケジュール** - 地区別のごみ収集日程をチェック
- 💬 **自然な会話** - OpenAI GPTを使用した親しみやすいAI応答
- 🧠 **会話履歴機能** - 前後3つの会話を記憶して継続的な会話が可能
- 📱 **レスポンシブデザイン** - スマホ・タブレット・PCに対応
- ♿ **アクセシビリティ対応** - 誰でも使いやすいUI設計
- 🌐 **リアルタイムオープンデータ** - 金沢市公式オープンデータとの統合

## 🆕 オープンデータ統合機能

このアプリは金沢市の公式オープンデータポータルと統合され、**最新で正確な情報**を提供します！

### 📊 データソース
- **金沢市オープンデータポータル** - 319のデータセットからリアルタイム取得
- **ふらっとバス情報** - GTFS形式の公共交通データ
- **地区別ごみ収集カレンダー** - 最新の収集スケジュール
- **観光イベント情報** - 金沢市観光協会のイベントデータ
- **金沢市画像オープンデータ** - 観光地の公式写真素材

### 🔄 ハイブリッドモード
- **プライマリ**: オープンデータから最新情報を取得
- **フォールバック**: データ取得に失敗した場合はローカルDBを使用
- **キャッシュ機能**: パフォーマンス向上のため適切にキャッシュ

### 🎯 利用可能なオープンデータ
1. **交通・バス情報**
   - ふらっとバス路線・時刻表（GTFS形式）
   - バス停位置情報（GPS座標付き）
   
2. **ごみ収集情報**
   - 地区別収集カレンダー
   - ごみ分別辞典
   
3. **観光・イベント情報**
   - 観光スポット詳細データ
   - イベント・祭り情報
   - 施設営業時間・連絡先

## 🆕 会話履歴機能

このアプリでは、**前後3つの会話を自動的に記憶**して、より自然で継続的な会話体験を提供します！

### 💭 どんなことができるの？
- **「さっき聞いた観光地について、もう少し詳しく教えて」** 
- **「前に話したバスの時間、もう一度教えて」**
- **「今までの会話で出てきた場所をまとめて」**

### 🔧 技術詳細
- **セッション管理**: UUIDを使用したユニークなセッションID
- **データベース保存**: SQLiteで会話履歴を永続化
- **自動クリーンアップ**: 古い会話は自動的に削除（メモリ効率化）
- **プライバシー配慮**: セッションごとに分離された安全な会話管理

### 🧪 会話履歴テスト
```bash
cd backend
python test_chat_history.py
```

## 🛠️ 技術スタック

### バックエンド
- **FastAPI** - 高性能なPython Webフレームワーク
- **SQLAlchemy** - ORM（Object-Relational Mapping）
- **OpenAI API** - GPTモデルによるAI応答生成
- **aiohttp** - 非同期HTTPクライアント（オープンデータ取得用）
- **Redis** - キャッシュシステム（オプション）
- **SQLite/PostgreSQL** - データベース

### フロントエンド
- **Next.js 14** - React フレームワーク（App Router使用）
- **TypeScript** - 型安全なJavaScript
- **Chakra UI** - モダンなUIコンポーネントライブラリ
- **Zustand** - 軽量な状態管理
- **Framer Motion** - アニメーションライブラリ

## 🚀 セットアップ

### 前提条件
- Node.js 18.0以上
- Python 3.9以上
- OpenAI APIキー

### バックエンドのセットアップ

1. **依存関係のインストール**
```bash
cd backend
pip install -r requirements.txt
```

2. **環境変数の設定**
```bash
# .env.exampleをコピーして.envを作成
cp env_example.txt .env

# .envファイルを編集してOpenAI APIキーなどを設定
# オープンデータモードを有効にする場合：
# USE_OPEN_DATA=true
```

3. **データベースの初期化**
```bash
# データベースマイグレーション（必要に応じて）
python -c "from database import engine; from models import Base; Base.metadata.create_all(engine)"
```

4. **オープンデータ統合テスト**
```bash
# オープンデータ接続テスト
python scripts/test_open_data.py
```

5. **サーバーの起動**
```bash
python main.py
# または
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンドのセットアップ

1. **依存関係のインストール**
```bash
cd frontend
npm install
```

2. **環境変数の設定**
```bash
# .env.localファイルを作成
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

3. **開発サーバーの起動**
```bash
npm run dev
```

## ⚙️ オープンデータ設定

### 環境変数

```bash
# オープンデータモードの有効化
USE_OPEN_DATA=true

# オープンデータベースURL（通常は変更不要）
OPEN_DATA_BASE_URL=https://catalog-data.city.kanazawa.ishikawa.jp

# タイムアウト設定（秒）
OPEN_DATA_TIMEOUT=30

# キャッシュ保持時間（秒）
OPEN_DATA_CACHE_DURATION=3600
```

### モード設定

#### 📡 オープンデータモード（推奨）
```bash
USE_OPEN_DATA=true
```
- 金沢市の最新オープンデータを使用
- データ取得失敗時はローカルDBにフォールバック
- より正確で最新の情報を提供

#### 💾 ローカルモード
```bash
USE_OPEN_DATA=false
```
- ローカルSQLiteデータベースのみ使用
- インターネット接続不要
- デモ・開発用途に最適

## 📁 プロジェクト構造

```
kanazawa_mcp/
├── backend/                 # FastAPI バックエンド
│   ├── main.py             # メインAPIファイル
│   ├── database.py         # データベース設定
│   ├── models.py           # SQLAlchemy モデル
│   ├── cache.py            # キャッシュ機能
│   ├── services/           # 🆕 オープンデータサービス
│   │   └── open_data_service.py # 金沢市オープンデータ統合
│   ├── mcp/                # MCPサービス
│   │   ├── service.py      # MCP サービスロジック
│   │   └── tools.py        # MCP ツール定義
│   ├── scripts/            # 管理スクリプト
│   │   └── test_open_data.py # 🆕 オープンデータテスト
│   ├── requirements.txt    # Python 依存関係
│   └── env_example.txt     # 環境変数サンプル
├── frontend/               # Next.js フロントエンド
│   ├── app/                # App Router
│   │   ├── components/     # Reactコンポーネント
│   │   ├── store/          # Zustand ストア
│   │   ├── types/          # TypeScript 型定義
│   │   ├── layout.tsx      # ルートレイアウト
│   │   ├── page.tsx        # メインページ
│   │   ├── loading.tsx     # ローディングページ
│   │   └── error.tsx       # エラーページ
│   ├── package.json        # Node.js 依存関係
│   └── tsconfig.json       # TypeScript 設定
└── README.md               # このファイル
```

## 🔧 API エンドポイント

### チャット API
- `POST /api/chat` - AIチャットメッセージの送信
- `GET /health` - ヘルスチェック

### MCP API
- `GET /mcp/tools` - 利用可能なツール一覧
- `POST /mcp/execute` - MCPツールの実行

開発時には `backend/scripts/mcp_cli.py` を使うと、コマンドラインから簡単に
MCP API を試せます。

```bash
# ツール一覧取得
python scripts/mcp_cli.py tools

# ツール実行例
python scripts/mcp_cli.py execute get_garbage_schedule '{"area_code":"A01","date":"2024-05-01"}'
```

### レスポンス形式

オープンデータ統合により、レスポンスに`data_source`フィールドが追加されました：

```json
{
  "spots": [...],
  "data_source": "open_data"  // "open_data" または "local_db"
}
```

## 🎨 主な改善点

### バックエンド
- ✅ **モダンなセッション管理** - yield を使った依存性注入
- ✅ **エラーハンドリング強化** - 詳細なログとエラー処理
- ✅ **OpenAI API更新** - 最新のAPIクライアント使用
- ✅ **環境変数対応** - 設定の外部化
- ✅ **キャッシュ機能** - パフォーマンス向上
- ✅ **🆕 オープンデータ統合** - 金沢市公式データとの連携
- ✅ **🆕 ハイブリッドモード** - リアルタイム＋フォールバック

### フロントエンド
- ✅ **App Router対応** - Next.js 14の最新機能
- ✅ **アクセシビリティ向上** - ARIA属性、セマンティックHTML
- ✅ **レスポンシブデザイン** - モバイルファースト設計
- ✅ **エラー・ローディング状態** - より良いユーザー体験
- ✅ **タイムスタンプ表示** - メッセージの時刻表示
- ✅ **メッセージコピー機能** - ワンクリックでコピー
- ✅ **文字数制限** - 入力バリデーション強化

## 🌟 使い方

1. **アプリケーションを起動**
   - バックエンド: `http://localhost:8000`
   - フロントエンド: `http://localhost:3000`

2. **チャットで質問**
   - 「兼六園について教えて」
   - 「近くのバス停はどこ？」
   - 「今日のごみ収集は何ですか？」

3. **AIが金沢市の情報を提供**
   - 観光スポットの詳細情報
   - 交通機関のアクセス情報
   - ごみ収集スケジュール

## 🧪 テストとデバッグ

### オープンデータ統合テスト
```bash
# 統合テストの実行
cd backend
python scripts/test_open_data.py
```

### データソース確認
レスポンスの`data_source`フィールドで確認：
- `"open_data"` - 金沢市オープンデータから取得
- `"local_db"` - ローカルデータベースから取得

## 🐛 トラブルシューティング

### よくある問題

1. **OpenAI APIエラー**
   - `.env`ファイルのAPIキーを確認
   - APIクォータと課金状況をチェック

2. **データベース接続エラー**
   - データベースファイルのパスを確認
   - PostgreSQLの場合は接続情報を確認

3. **CORS エラー**
   - `ALLOWED_ORIGINS`環境変数を確認
   - フロントエンドのURLが正しく設定されているか確認

4. **🆕 オープンデータ接続エラー**
   - インターネット接続を確認
   - `USE_OPEN_DATA=false`でローカルモードに切り替え
   - `python scripts/test_open_data.py`でテスト実行

## 📚 参考リンク

- [金沢市オープンデータポータル](https://portal-data.city.kanazawa.ishikawa.jp/)
- [金沢市オープンデータカタログ](https://catalog-data.city.kanazawa.ishikawa.jp/dataset/)
- [GTFS（標準的なバス情報フォーマット）](https://www.mlit.go.jp/common/001283244.pdf)

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストや Issue の報告を歓迎します！

## 📧 お問い合わせ

何かご質問がございましたら、Issue を作成してください。 