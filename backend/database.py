from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Annotated
from fastapi import Depends
import os
from dotenv import load_dotenv

load_dotenv()

# データベースURL（環境変数から取得、デフォルトはSQLite）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanazawa_mcp.db")

# SQLiteの場合はcheck_same_thread=Falseを設定
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 依存性注入用のセッション取得関数（yieldを使用）
def get_session():
    """
    データベースセッションを取得する依存性注入関数
    リクエストごとに新しいセッションを作成し、レスポンス後に自動でクローズ
    """
    with Session(engine) as session:
        yield session

# 型注釈付きの依存性
SessionDep = Annotated[Session, Depends(get_session)]

# テーブル作成関数
def create_tables():
    """全てのテーブルを作成する"""
    Base.metadata.create_all(bind=engine)

# この部分は既存の内容を維持するための確認用
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base  
# from sqlalchemy.orm import sessionmaker
# import os
# from dotenv import load_dotenv
# 
# load_dotenv()
# 
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanazawa_mcp.db")
# 
# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
# )
# 
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
# 
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# 
# SessionDep = Annotated[Session, Depends(get_db)] 