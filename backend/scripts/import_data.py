import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
from ..database import SessionLocal, engine
from ..models import Base, GarbageSchedule, TouristSpot, TransportationStop

def import_garbage_schedules(db: Session, csv_path: str):
    """ごみ収集スケジュールのCSVをインポート"""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        schedule = GarbageSchedule(
            area_code=row['area_code'],
            date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
            garbage_type=row['garbage_type'],
            description=row.get('description')
        )
        db.add(schedule)
    db.commit()

def import_tourist_spots(db: Session, csv_path: str):
    """観光スポットのCSVをインポート"""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        spot = TouristSpot(
            name=row['name'],
            description=row['description'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            category=row['category'],
            address=row['address'],
            opening_hours=row.get('opening_hours'),
            contact=row.get('contact')
        )
        db.add(spot)
    db.commit()

def import_transportation_stops(db: Session, csv_path: str):
    """交通情報のCSVをインポート"""
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        stop = TransportationStop(
            name=row['name'],
            type=row['type'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            address=row['address'],
            routes=json.loads(row['routes']) if 'routes' in row else None
        )
        db.add(stop)
    db.commit()

def main():
    # データベースの作成
    Base.metadata.create_all(bind=engine)
    
    # データのインポート
    db = SessionLocal()
    try:
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        
        # 各CSVファイルのインポート
        import_garbage_schedules(db, os.path.join(data_dir, 'garbage_calendar.csv'))
        import_tourist_spots(db, os.path.join(data_dir, 'tourist_spots.csv'))
        import_transportation_stops(db, os.path.join(data_dir, 'transportation_stops.csv'))
        
        print("データのインポートが完了しました！")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 