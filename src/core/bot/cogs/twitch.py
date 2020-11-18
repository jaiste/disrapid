from twitchAPI.twitch import Twitch as TwitchAPI
from twitchAPI.webhook import TwitchWebHook
import logging
from discord.ext import commands
# from datetime import datetime
# import random
# import models
# from sqlalchemy import exists, and_


class Twitch(commands.Cog, name="Twitch"):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

        logging.debug(
            "twitch module initializing..."
        )

        # start twitch API
        twitch = TwitchAPI(
            self.bot.config.client_id,  # client_id
            self.bot.config.client_secret  # client_secret
        )
        logging.debug(
            "twitch module authenticating..."
        )
        twitch.authenticate_app([])

        logging.debug(
            "twitch module starting webhook"
        )
        # start twitch webhook
        hook = TwitchWebHook(
            f"https://{self.bot.config.webhook_addr}:443",
            self.bot.config.client_id,
            80
        )

        hook.authenticate(twitch.get_app_token())
        hook.start()

        logging.debug(
            "twitch webhook started, checking user_id"
        )
        user_info = twitch.get_users(logins=['clcreative'])
        user_id = user_info['data'][0]['id']

        logging.debug(
            f"twitch user_id-{user_id}"
        )

        success, uuid_stream = hook.subscribe_stream_changed(
            user_id,
            self.callback_stream_changed
        )
        logging.debug(f'was subscription successfull?: {success}')

        success, uuid_user = hook.subscribe_user_changed(
            user_id,
            self.callback_user_changed
        )
        logging.debug(f'was subscription successfull?: {success}')
        # success = hook.unsubscribe_user_changed(uuid_user)
        # logging.debug(f'was unsubscription successfull?: {success}')
        # success = hook.unsubscribe_stream_changed(uuid_stream)
        # logging.debug(f'was unsubscription successfull?: {success}')

    def callback_stream_changed(uuid, data):
        logging.debug('Callback Stream changed for UUID ' + str(uuid))
        logging.debug(data)

    def callback_user_changed(uuid, data):
        logging.debug('Callback User changed for UUID ' + str(uuid))
        logging.debug(data)


def setup(bot):
    bot.add_cog(Twitch(bot))
