from sqlalchemy import create_engine, Column, String, Integer, Date, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

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