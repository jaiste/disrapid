import discord
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
                # perform a full guild sync, this will sync all guild objects
                # with the database
                await self._full_guild_sync(session, guild)

            session.close()
            return True
        except Exception as e:
            logging.error(f"couldn't perform full sync check reason: {e}")
            # close session
            return False

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # A new guild is created or joined, perform a full db sync
        try:
            session = self.bot.db.Session()

            self._full_guild_sync(session, guild)
        except Exception as e:
            logging.error(f"couldn't perform full sync check reason: {e}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # The bot has left a guild, delte guild object on db
        try:
            session = self.bot.db.Session()

            self._full_guild_sync(session, guild)
        except Exception as e:
            logging.error(f"couldn't perform full sync check reason: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, old_channel, new_channel):

        pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):

        pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        pass

    @commands.Cog.listener()
    async def on_guild_role_update(self, old_role, new_role):

        pass

    async def _full_guild_sync(self, session, guild):
        # sync guild to database

        logging.info(f"TRACE: SYNCING GUILD: {guild.id}")

        self.bot.db.sync_guild(session, guild.id, guild.name)

        for channel in guild.channels:
            # sync channel to database
            logging.info("TRACE: SYNCING CHANNEL FOR GUILD: " +
                         f"{guild.id} - CHANNEL_ID: {channel.id}")
            self.bot.db.sync_channel(session,
                                     guild.id,
                                     channel.id,
                                     channel.name,
                                     channel.type)
        for role in guild.roles:
            # sync role to database
            logging.info("TRACE: SYNCING role FOR GUILD: " +
                         f"{guild.id} - role_ID: {role.id}")
            self.bot.db.sync_role(session,
                                  guild.id,
                                  role.id,
                                  role.name)

    @commands.command()
    async def delguild(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        try:
            # init new session
            session = self.bot.db.Session()

            self.bot.db.del_guild(session, member.guild.id)
            session.close()
        except Exception as e:
            logging.debug(e)


def setup(bot):
    bot.add_cog(Sync(bot))
