from discord.ext import commands
import sys
import logging
from interface import DisrapidDb
from db.migrate import Schema
from helpers import YouTubeHelper

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

            if not self.db.engine.dialect.has_table(self.db.engine, "schema"):
                raise Exception("database schema is not existing!")

            if self._db_sanity_check(self.config.schema_version) is not True:
                # db santiy check failed, need to repair database
                raise Exception("database sanity check failed!")

            if self.config.youtube:
                self.youtube = YouTubeHelper(self.config.developer_key)

        except Exception as e:
            logging.fatal(e)
            sys.exit(1)

    def _db_sanity_check(self, schema_version):
        # do db sanity check + update schema when needed
        try:
            s = self.db.Session()

            db_schema_version = s.query(Schema).one()

            logging.debug(f"db_schema_version={db_schema_version}")
            if db_schema_version.id < schema_version:
                # db schema needs to be updated
                raise Exception("schema needs to be updated first!")

            # check if db is healthy
            pass

            s.close()
            return True

        except Exception as e:
            logging.fatal(f"couldn't perform santiy check reason: {e}")
            s.close()
            return False

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
        self.schema_version = kwargs.pop("schema_version")
        self.do_full_sync = False
