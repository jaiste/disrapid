from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
import logging
import sys
from models import Base


class DisrapidDb:

    def __init__(self, *args, **kwargs):
        try:
            self.engine = create_engine(
                'mysql+pymysql://' +
                f'{kwargs.pop("user")}:' +
                f'{kwargs.pop("passwd")}@' +
                f'{kwargs.pop("host")}' +
                ':3306/' +
                f'{kwargs.pop("name")}' +
                '?charset=utf8mb4'  # utf8mb4 needed for emoji support
            )

            Base.metadata.create_all(self.engine)

            self.Session = sessionmaker(bind=self.engine)
        except exc.SQLAlchemyError as e:
            logging.fatal(
                f"sqlalchemy-error={e}"
            )
            sys.exit(1)
        except Exception as e:
            logging.fatal(e)
            sys.exit(1)
