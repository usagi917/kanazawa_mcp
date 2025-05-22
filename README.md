# 金沢市 MCP チャットアプリ 🚀

金沢市のごみ収集情報、観光スポット、交通情報をチャットで簡単に検索できるアプリです。

## 機能 ✨

- ごみ収集スケジュール検索
- 観光スポット検索
- 交通情報検索
- モダンなチャットUI
- リアルタイムレスポンス

## 技術スタック 🛠

- Frontend: Next.js 14, Chakra UI, Framer Motion
- Backend: FastAPI, SQLite, Redis
- Infrastructure: Docker Compose

## セットアップ手順 📝

1. リポジトリをクローン
```bash
git clone [repository-url]
cd kanazawa_mpc
```

2. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して必要な環境変数を設定
```

3. Docker Composeで起動
```bash
docker-compose up --build
```

4. ブラウザでアクセス
```
http://localhost:3000
```

## 開発者向け情報 👩‍💻

- フロントエンド: `http://localhost:3000`
- バックエンドAPI: `http://localhost:8000`
- API仕様書: `http://localhost:8000/docs`

## ライセンス 📄

MIT License 