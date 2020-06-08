from discord.ext import commands
import sys
import logging
from db.interface import DisrapidDb


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
