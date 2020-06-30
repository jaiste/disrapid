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
    name = Column(String(255))
    welcomemessage = relationship("Welcomemessage",
                                  uselist=False,
                                  back_populates="guild",
                                  cascade="all, delete, delete-orphan")
    channels = relationship("Channel",
                            back_populates="guild",
                            cascade="all, delete, delete-orphan")
    roles = relationship("Role",
                         back_populates="guild",
                         cascade="all, delete, delete-orphan")


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    text = Column(String(2000))
    enable = Column(Integer)
    channel_id = Column(Integer, ForeignKey('guilds_channels.id'))
    guild = relationship("Guild", back_populates="welcomemessage")
    channel = relationship("Channel", back_populates="welcomemessage")


class Channel(Base):
    __tablename__ = 'guilds_channels'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    name = Column(String(255))
    channeltype = Column(Enum(ChannelTypes))
    guild = relationship("Guild", back_populates="channels")
    welcomemessage = relationship("Channel",
                                  back_populates="channel"
                                  )


class Role(Base):
    __tablename__ = 'guilds_roles'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    name = Column(String(255))
    guild = relationship("Guild", back_populates="roles")
