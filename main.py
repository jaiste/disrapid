# disrapid
# ---
#

import os
import sys
import logging
import discord


# INIT
try:

    # if 'DEBUG' in os.environ:
    #     logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    # else:
    #     logging.basicConfig(format=FORMAT, level=logging.INFO)

    if 'DISCORD_TOKEN' not in os.environ:
        raise Exception("no token provided, exiting...")
    else:
        DISCORD_TOKEN = os.environ['DISCORD_TOKEN']

except Exception as e:
    logging.fatal(e)
    sys.exit(1)

# RUN BOT
client = discord.Client()

client.run(DISCORD_TOKEN)

logging.warning("clean shutdown invoked")
client.close()