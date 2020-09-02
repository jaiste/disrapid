from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    Enum,
    BigInteger,
    Boolean
)
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

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    notify_channel_id = Column(BigInteger, nullable=True)
    notify_role_id = Column(BigInteger, nullable=True)

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


class Channel(Base):
    __tablename__ = 'guilds_channels'

    id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'))
    name = Column(String(255))
    channeltype = Column(Enum(ChannelTypes))

    guild = relationship("Guild", back_populates="channels")


class Role(Base):
    __tablename__ = 'guilds_roles'

    id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'))
    name = Column(String(255))

    guild = relationship("Guild", back_populates="roles")


class YoutubeFollow(Base):
    __tablename__ = 'guilds_youtubefollow'

    id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'))
    youtube_id = Column(BigInteger, ForeignKey('youtube.id'))
    monitor_videos = Column(Boolean)
    monitor_goals = Column(Boolean)
    monitor_streams = Column(Boolean)
    remind_streams = Column(Boolean)


class Reactionrole(Base):
    __tablename__ = 'guilds_reactionroles'

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'))
    role_id = Column(BigInteger)
    name = Column(String(255))
