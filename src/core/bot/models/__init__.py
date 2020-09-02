from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from .guild import *  # noqa: 401
from .youtube import *  # noqa: 401
from .welcome import *  # noqa: 401
