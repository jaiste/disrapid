from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import sys


class DisrapidDb:

    def __init__(self, *args, **kwargs):
        try:
            self.engine = create_engine('mysql+pymysql://' +
                                        f'{kwargs.pop("user")}:' +
                                        f'{kwargs.pop("passwd")}@' +
                                        f'{kwargs.pop("host")}' +
                                        ':3306/' +
                                        f'{kwargs.pop("name")}' +
                                        '?charset=utf8mb4')

            self.Session = sessionmaker(bind=self.engine)

        except Exception as e:
            logging.fatal(e)
            sys.exit(1)
