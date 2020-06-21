from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, null
from sqlalchemy.orm import relationship
from . import Base


class Youtube(Base):
    __tablename__ = 'youtube'

    id = Column(Integer, primary_key=True)
    valid = Column(Integer)
    ytchannel_id = Column(String)
    last_seen = Column(DateTime, nullable=True, default=null)
    last_goal = Column(Integer)
    
    activities = relationship("Activity",
                              back_populates="youtube",
                              cascade="all, delete, delete-orphan")
    guilds = relationship("Guild", secondary='guilds_youtubefollow')


class Activity(Base):
    __tablename__ = 'youtube_activities'

    id = Column(String, primary_key=True)
    youtube_id = Column(Integer, ForeignKey('youtube.id'))
    last_sequence = Column(String)

    youtube = relationship("Youtube", back_populates="activities")


class Goals(Base):
    __tablename__ = 'youtube_goals'

    id = Column(Integer, primary_key=True)
    min = Column(Integer)
    max = Column(Integer)
    image = Column(String)
    text = Column(String)
