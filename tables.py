from sqlalchemy import Column, DateTime, String, create_engine, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('postgresql://postgres:pass123@localhost/House_advertisements')
Base = declarative_base()
Session = sessionmaker(bind=engine)


class House(Base):
    __tablename__ = 'houses'
    id = Column(Integer, primary_key=True)
    link = Column(String, unique=True)
    cost = Column(Float)
    area = Column(Float)
    location = Column(String)
    parse_date = Column(DateTime, default=datetime.now())


Base.metadata.create_all(engine)
