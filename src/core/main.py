# disrapid
# ---
#

# import necessary libraries for debugging at the earliest possible point
import os
import sys
import ptvsd

# import db handler
import schema

try:
    # check if we should run disrapid in debug mode
    if 'DEBUG' in os.environ:
        # listen for incoming debugger connection
        ptvsd.enable_attach(address=('0.0.0.0',5050))
        # in debug mode we need to wait for debugger to connect before we continue..
        ptvsd.wait_for_attach()
    else:
        # debug mode is not enabled, running in production mode...
        pass

except Exception as e:
    # any error will stop the container
    sys.exit(1)

# import all functional libaries
import logging
import discord
import asyncio
from discord.ext import commands, tasks

try:
    # if no discord token was provided we can't run the bot
    if 'DISCORD_TOKEN' not in os.environ:
        raise Exception("no token provided, exiting...")
    else:
        # set discord token for the client
        DISCORD_TOKEN = os.environ['DISCORD_TOKEN']

except Exception as e:
    logging.fatal(e)
    sys.exit(1)


# TMP bot class
class Disrapid(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # init database
        self.db = schema.DisrapidDb()

    def load_extension(self, extension):
        # logging override
        super().load_extension(extension)

    async def logout(self):
        # override logout sequence, exit db connection first
        # await self.db.close()
        await super().logout()

    class Welcomemessage(Base):
        __tablename__ = 'guilds_welcomemessage'

        guild_id = Column(Integer, primary_key=True)
        text = Column(String)
        enable = Column(Integer)
        channel_id = Column(Integer)

if __name__ == "__main__":

    # start and run our discord client
    client = Disrapid(command_prefix=".")

    # load extensions 
    # ...
    client.load_extension("cogs.welcome")
    client.load_extension("cogs.testcmd")

    client.run(DISCORD_TOKEN)

    # this happens when the bot was stopped by any systemcall, make a clean shutdown...
    logging.warning("clean shutdown invoked")
    client.logout()