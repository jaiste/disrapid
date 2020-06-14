from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from . import Base
import enum


class ChannelTypes(enum.Enum):
    text = 1
    voice = 2
    private = 3
    group = 4
    category = 5
    news = 6
    store = 7


class Guild(Base):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    welcomemessage = relationship("Welcomemessage",
                                  uselist=False,
                                  back_populates="guild")
    channels = relationship("Channel",
                            back_populates="guild")
    roles = relationship("Role",
                         back_populates="guild")


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    text = Column(String)
    enable = Column(Integer)
    channel_id = Column(Integer)
    guild = relationship("Guild", back_populates="welcomemessage")


class Channel(Base):
    __tablename__ = 'guilds_channels'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    name = Column(String)
    channeltype = Column(Enum(ChannelTypes))
    guild = relationship("Guild", back_populates="channels")


class Role(Base):
    __tablename__ = 'guilds_roles'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    name = Column(String)
    guild = relationship("Guild", back_populates="roles")
