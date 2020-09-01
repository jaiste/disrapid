import discord
import logging
from discord.ext import commands
import models
from sqlalchemy import exists


class Sync(commands.Cog, name="Sync Function"):
    # This class is used to syncronize all guilds and objects
    # with the database
    #
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    @commands.Cog.listener()
    async def on_ready(self):
        # sync all existing guilds, channels with database
        try:

            # skip full sync if not set in config
            if not self.bot.config.do_full_sync:
                return

            session = self.db.Session()

            guilds = self.bot.guilds

            for guild in guilds:
                # perform a full guild sync, this will sync all guild objects
                # with the database, if they have changed during down-time
                # this may take some time on large shards
                await Sync._full_guild_sync(session, guild)

            # bot is done with sync
            await self.bot.change_presence(
                activity=discord.Game(
                    name="disrapid.com"
                )
            )

        except Exception as e:
            logging.error(f"couldn't perform full sync check reason: {e}")
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # A new guild is created or joined, we need to add the guild
        # to the database
        try:
            session = self.db.Session()

            self._full_guild_add(session, guild)

            session.close()
        except Exception as e:
            logging.error(f"couldn't perform add guild check reason: {e}")
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # The bot has left a guild, delte guild object on db
        # All other objects are deleted due to cascade
        try:
            session = self.db.Session()

            guild = session.query(models.Guild).get(guild.id)
            session.delete(guild)
            session.commit()

            session.close()

        except Exception as e:
            logging.error(f"couldn't perform del guild check reason: {e}")
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        try:
            # init new session
            session = self.db.Session()

            new_channel = models.Channel(
                id=channel.id,
                guild_id=channel.guild.id,
                name=channel.name,
                channeltype=channel.type.name
            )
            session.add(new_channel)

        except Exception as e:
            logging.error(e)
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            # init new session
            session = self.db.Session()

            db_channel = session.query(models.Channel).get(channel.id)
            session.delete(db_channel)
            session.commit()

        except Exception as e:
            logging.error(e)
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, old_channel, new_channel):
        try:
            session = self.db.Session()

            session.query(
                models.Channel
            ).filter(
                models.Channel.id == new_channel.id,
                models.Channel.name != new_channel.name
            ).update(
                {models.Channel.name: new_channel.name}
            )

            session.commit()
            session.close()
        except Exception as e:
            session.rollback()
            logging.error(e)
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        try:
            # init new session
            session = self.db.Session()

            new_role = models.Role(
                id=role.id,
                guild_id=role.guild.id,
                name=role.name
            )
            session.add(new_role)

        except Exception as e:
            logging.error(e)
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        try:
            # init new session
            session = self.db.Session()

            db_role = session.query(models.Role).get(role.id)
            session.delete(db_role)
            session.commit()

            # delete all reaction roles
            obj = session.query(
                models.Reactionrole
            ).filter(
                models.Reactionrole.role_id == role.id
            )

            obj.delete()
            session.commit()

        except Exception as e:
            logging.error(e)
        finally:
            session.close()

    @commands.Cog.listener()
    async def on_guild_role_update(self, old_role, new_role):
        try:
            session = self.db.Session()

            session.query(
                models.Channel
            ).filter(
                models.Channel.id == new_role.id,
                models.Channel.name != new_role.name
            ).update(
                {models.Channel.name: new_role.name}
            )

            session.commit()
            session.close()
        except Exception as e:
            session.rollback()
            logging.error(e)
        finally:
            session.close()

    # SYNC UTILITY FUNCTIONS
    # ---
    #
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def isadmin(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        await member.send("yes you are admin!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def isowner(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        owner = (await self.bot.application_info()).owner
        if member.id == owner.id:
            await member.send("yes you are bot owner!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def resetconfig(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        try:
            # init new session
            session = self.db.Session()

            # delete guilds config
            guild = session.query(models.Guild).get(member.guild.id)
            session.delete(guild)
            session.commit()

            # perform full guild sync
            await Sync._full_guild_sync(session, member.guild)

            session.commit()

            # send response to channel
            await member.send("guild configuration was resetted")

        except Exception as e:
            logging.error(e)
            await member.send("an error occurred, please contact support")
        finally:
            session.close()

    # CLASS STATIC METHODS
    # ---
    #
    @staticmethod
    async def _full_guild_sync(session, guild):
        # sync guild to database
        try:
            if session.query(exists()
                             .where(models.Guild.id == guild.id)).scalar():
                session.query(models.Guild) \
                       .filter(models.Guild.id == guild.id,
                               models.Guild.name != guild.name) \
                       .update({models.Guild.name: guild.name})
            else:
                new_guild = models.Guild(
                    id=guild.id,
                    name=guild.name
                )
                session.add(new_guild)

            # we need to sync all channels
            for channel in guild.channels:
                # sync channel to database
                if session.query(
                    exists()
                    .where(
                        models.Channel.id == channel.id
                        )).scalar():
                    session.query(
                        models.Channel
                    ).filter(
                        models.Channel.id == channel.id,
                        models.Channel.name != channel.name
                    ).update(
                        {models.Channel.name: channel.name}
                    )
                else:
                    new_channel = models.Channel(
                        id=channel.id,
                        guild_id=guild.id,
                        name=channel.name,
                        channeltype=channel.type.name
                    )
                    session.add(new_channel)

            # we need to sync all roles
            for role in guild.roles:
                # sync role to database
                if session.query(exists()
                                 .where(models.Role.id == role.id)).scalar():
                    session.query(models.Role) \
                        .filter(models.Role.id == role.id,
                                models.Role.name != role.name) \
                        .update({models.Role.name: role.name})
                else:
                    new_role = models.Role(
                        id=role.id,
                        guild_id=guild.id,
                        name=role.name
                    )
                    session.add(new_role)

            session.commit()

        except Exception as e:
            session.rollback()
            logging.error(e)
        finally:
            session.close()

    @staticmethod
    async def _full_guild_add(session, guild):
        # add guild to database
        try:
            new_guild = models.Guild(
                id=guild.id,
                name=guild.name
            )
            session.add(new_guild)

            # we need to add all channels
            for channel in guild.channels:
                # add channel to database
                new_channel = models.Channel(
                    id=channel.id,
                    guild_id=guild.id,
                    name=channel.name,
                    channeltype=channel.type.name
                )
                session.add(new_channel)

            # we need to add all roles
            for role in guild.roles:
                # add role to database
                new_role = models.Role(
                    id=role.id,
                    guild_id=guild.id,
                    name=role.name,
                )
                session.add(new_role)

            session.commit()

        except Exception as e:
            session.rollback()
            logging.error(e)
        finally:
            session.close()


def setup(bot):
    bot.add_cog(Sync(bot))
