from sqlalchemy import create_engine, Column, String, Integer, Date, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class DisrapidDb:

    def __init__(self):
        
        self.engine = create_engine(f'mysql+pymysql://{os.environ["DB_USER"]}:{os.environ["DB_PASS"]}@{os.environ["DB_HOST"]}:3306/{os.environ["DB_NAME"]}')

        self.Session = sessionmaker(bind=self.engine)

        Base.metadata.create_all(self.engine)


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    guild_id = Column(Integer, primary_key=True)
    text = Column(String)
    enable = Column(Integer)
    channel_id = Column(Integer)

    # def __init__(self, id, name, ext):
    #     self.id = id
    #     self.name = name
    #     self.ext = ext