# import discord
import logging
from discord.ext import commands


class Sync(commands.Cog, name="Sync Function"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # sync all existing guilds, channels with database
        try:
            session = self.bot.db.Session()

            guilds = self.bot.guilds

            for guild in guilds:
                # sync guild to database
                logging.info(f"TRACE: SYNCING GUILD: {guild.id}")
                self.bot.db.sync_guild(session, guild.id)
                for channel in guild.channels:
                    # sync channel to database
                    logging.info("TRACE: SYNCING CHANNEL FOR GUILD: " +
                                 f"{guild.id} - CHANNEL_ID: {channel.id}")

            session.close()
            return True
        except Exception as e:
            logging.error(f"couldn't perform full sync check reason: {e}")
            # close session
            return False


def setup(bot):
    bot.add_cog(Sync(bot))
