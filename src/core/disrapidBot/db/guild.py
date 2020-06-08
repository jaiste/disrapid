from sqlalchemy import Column, String, Integer
from . import Base


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    guild_id = Column(Integer, primary_key=True)
    text = Column(String)
    enable = Column(Integer)
    channel_id = Column(Integer)
