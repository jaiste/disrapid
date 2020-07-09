# disrapid
# ---
#

# import necessary libraries for debugging at the earliest possible point
import os
import sys
import ptvsd
import logging

try:
    # check if we should run disrapid in debug mode
    if 'DEBUG' in os.environ:
        # listen for incoming debugger connection
        ptvsd.enable_attach(address=('0.0.0.0', 5050))
        # in debug mode we need to wait for debugger to connect
        ptvsd.wait_for_attach()
        logging.basicConfig(level=logging.DEBUG)
        # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
    else:
        # debug mode is not enabled, running in production mode...
        pass

except Exception:
    # any error will stop the container
    sys.exit(1)

# import all functional libaries
from bot import Disrapid, DisrapidConfig

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

if __name__ == "__main__":

    # start and run our discord client
    config = DisrapidConfig(db_host=os.environ["DB_HOST"],
                            db_user=os.environ["DB_USER"],
                            db_name=os.environ["DB_NAME"],
                            db_pass=os.environ["DB_PASS"],
                            schema_version=1,
                            youtube=False)

    if 'DO_FULL_SYNC' in os.environ:
        config.do_full_sync = True

    if 'YOUTUBE_DEVELOPER_KEY' in os.environ:
        config.developer_key = os.environ["YOUTUBE_DEVELOPER_KEY"]
        config.youtube = True

    client = Disrapid(command_prefix=".", config=config)

    # load extensions
    client.load_extension("cogs.welcome")
    client.load_extension("cogs.sync")
    if config.youtube is True:
        client.load_extension("cogs.notification")

    client.run(DISCORD_TOKEN)

    # this happens when the bot was stopped by any systemcall, make a clean
    # shutdown...
    logging.warning("clean shutdown invoked")
    client.logout()
