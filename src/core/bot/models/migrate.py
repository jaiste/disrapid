from sqlalchemy import Column, Integer
from . import Base


class Schema(Base):
    __tablename__ = 'schema'

    id = Column(Integer, primary_key=True)
