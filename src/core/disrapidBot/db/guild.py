from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class Guild(Base):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    welcomemessage = relationship("Welcomemessage",
                                  uselist=False,
                                  back_populates="guilds")


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    text = Column(String)
    enable = Column(Integer)
    channel_id = Column(Integer)
    guilds = relationship("Guild", back_populates="welcomemessage")
