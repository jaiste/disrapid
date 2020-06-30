from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
    null,
    BigInteger
)
from sqlalchemy.orm import relationship
from . import Base


class Youtube(Base):
    __tablename__ = 'youtube'

    id = Column(BigInteger, primary_key=True)
    valid = Column(Boolean)
    ytchannel_id = Column(String(255))
    last_seen = Column(DateTime, nullable=True, default=null)
    last_goal = Column(Integer)

    activities = relationship("Activity",
                              back_populates="youtube",
                              cascade="all, delete, delete-orphan")
    guilds = relationship("Guild", secondary='guilds_youtubefollow')


class Activity(Base):
    __tablename__ = 'youtube_activities'

    id = Column(String(255), primary_key=True)
    youtube_id = Column(BigInteger, ForeignKey('youtube.id'))
    last_sequence = Column(String(255))

    youtube = relationship("Youtube", back_populates="activities")


class Goals(Base):
    __tablename__ = 'youtube_goals'

    id = Column(Integer, primary_key=True)
    min = Column(Integer)
    max = Column(Integer)
    image = Column(String(255))
    text = Column(String(2000))
