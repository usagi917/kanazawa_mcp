from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class GarbageSchedule(Base):
    __tablename__ = "garbage_schedules"

    id = Column(Integer, primary_key=True, index=True)
    area_code = Column(String, index=True)
    date = Column(Date, index=True)
    garbage_type = Column(String)
    description = Column(String, nullable=True)

class TouristSpot(Base):
    __tablename__ = "tourist_spots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    category = Column(String, index=True)
    address = Column(String)
    opening_hours = Column(String, nullable=True)
    contact = Column(String, nullable=True)

class TransportationStop(Base):
    __tablename__ = "transportation_stops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String, index=True)  # bus_stop, train_station, etc.
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    routes = Column(JSON, nullable=True)  # バス路線や電車路線の情報 