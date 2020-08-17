from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from . import Base


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    text = Column(String(2000))
    enable = Column(Boolean)
    channel_id = Column(
        Integer,
        ForeignKey('guilds_channels.id'),
        nullable=True
    )

    guild = relationship("Guild", back_populates="welcomemessage")
    channel = relationship("Channel")
