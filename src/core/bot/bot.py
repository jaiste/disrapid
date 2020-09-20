from discord.ext import commands
import sys
import logging
from interface import DisrapidDb
from helpers import YouTubeHelper
from pythonjsonlogger import jsonlogger
from datetime import datetime

ADMINISTRATOR = 0x00000008


class Disrapid(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # init database
        try:
            self.config = kwargs.pop("config")
            self.db = DisrapidDb(host=self.config.db_host,
                                 user=self.config.db_user,
                                 passwd=self.config.db_pass,
                                 name=self.config.db_name)

            if self.config.youtube:
                self.youtube = YouTubeHelper(self.config.developer_key)

            if self.config.twitch:
                pass

        except Exception as e:
            logging.fatal(e)
            sys.exit(1)

    def load_extension(self, extension):
        # logging override
        super().load_extension(extension)

    async def logout(self):
        # override logout sequence, exit db connection first
        # await self.db.close()
        await super().logout()


class DisrapidConfig:
    def __init__(self, *args, **kwargs):
        self.db_host = kwargs.pop("db_host")
        self.db_name = kwargs.pop("db_name")
        self.db_pass = kwargs.pop("db_pass")
        self.db_user = kwargs.pop("db_user")
        self.do_full_sync = False
        self.youtube = False
        self.twitch = False


class DisrapidLoggingFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(DisrapidLoggingFormatter, self).add_fields(
            log_record,
            record,
            message_dict
        )
        log_record['@timestamp'] = datetime.now().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
