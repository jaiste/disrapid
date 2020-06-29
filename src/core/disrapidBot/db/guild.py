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
    notify_channel_id = Column(Integer, nullable=True)

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
    youtubes = relationship("Youtube", secondary='guilds_youtubefollow')


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    text = Column(String)
    enable = Column(Integer)
    channel_id = Column(Integer, ForeignKey('guilds_channels.id'))

    guild = relationship("Guild", back_populates="welcomemessage")
    channel = relationship("Channel")


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


class YoutubeFollow(Base):
    __tablename__ = 'guilds_youtubefollow'

    guild_id = Column(Integer, ForeignKey('guilds.id'), primary_key=True)
    youtube_id = Column(Integer, ForeignKey('youtube.id'), primary_key=True)
    monitor_videos = Column(Integer, default=0)
    monitor_goals = Column(Integer, default=0)
    monitor_streams = Column(Integer, default=0)
    remind_streams = Column(Integer, default=0)
