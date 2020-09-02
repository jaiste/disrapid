from sqlalchemy import Column, String, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from . import Base


class Welcomemessage(Base):
    __tablename__ = 'guilds_welcomemessage'

    guild_id = Column(BigInteger, ForeignKey('guilds.id'), primary_key=True)
    text = Column(String(2000))
    enable = Column(Boolean)
    channel_id = Column(
        BigInteger,
        ForeignKey('guilds_channels.id'),
        nullable=True
    )

    guild = relationship("Guild", back_populates="welcomemessage")
    channel = relationship("Channel")
