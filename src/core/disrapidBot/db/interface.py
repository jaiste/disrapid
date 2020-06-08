from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from . import guild
from . import Base


class DisrapidDb:

    def __init__(self, *args, **kwargs):
        try:
            self.engine = create_engine('mysql+pymysql://',
                                        f'{kwargs.pop("user")}:',
                                        f'{kwargs.pop("passwd")}@',
                                        f'{kwargs.pop("host")}',
                                        ':3306/',
                                        f'{kwargs.pop("name")}')

            self.Session = sessionmaker(bind=self.engine)

            Base.metadata.create_all(self.engine)
        except Exception as e:
            logging.fatal(e)

    def get_active_welcomemessage(self, session, guild_id):
        # this will just load the active welcome message
        try:
            return session.query(guild.Welcomemessage) \
                                .filter(guild.Welcomemessage.guild_id ==
                                        guild_id, guild.Welcomemessage.enable
                                        == 1) \
                                .one()
        except Exception as e:
            logging.warning(e)
            return None
