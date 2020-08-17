import logging
from discord.ext import commands
# from datetime import datetime
# import random
import models
from sqlalchemy import exists, and_
from helpers import is_extended_string
# import os


def wmodf(intvalue):
    if intvalue == 0:
        return "[OFF]"
    else:
        return "ON"


class Welcome(commands.Cog, name="Welcome"):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    # EVENTS
    # ---
    #
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # check if this guild has an active welcome message
        try:
            s = self.db.Session()

            if not self._welcome_enabled(s, member.guild.id):
                s.close()
                return

            # send welcomemessage to user
            msg = s.query(
                models.Welcomemessage
            ).filter(
                models.Welcomemessage.guild_id ==
                member.guild.id
            ).one()

            await member.send(msg.text)

            s.close()

        except Exception as e:
            logging.error(
                f"Error in welcome event: {e}"
            )
            s.close()

    # ADMIN CONFIG COMMANDS
    # ---
    #
    @commands.has_permissions(administrator=True)
    @commands.group()
    async def welcome(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        try:
            s = self.db.Session()

            if not self._welcome_exists(s, ctx.guild.id):
                await ctx.send("No welcomemessage for server configured.")
                s.close()
                return

            msg = "This is your current welcome message configuration" \
                "setting.\n```css\n" \
                "/* Syntax= .settings : (enabled)" \
                "*/\n\n"

            # get config settings
            settings = s.query(
                models.Welcomemessage
            ).filter(
                models.Welcomemessage.guild_id ==
                ctx.guild.id
            ).one()

            msg += f".settings : {wmodf(settings.enable)}\n```"

            await ctx.send(msg)

            s.close()

        except Exception as e:
            logging.error(
                f"Error in welcome command: {e}"
            )
            s.close()

    @welcome.command()
    async def update(self, ctx, msg: str):
        # this will change the welcomemessage
        try:
            if not is_extended_string(msg):
                return

            s = self.db.Session()

            # check if welcome is already existing
            if self._welcome_exists(s, ctx.guild.id):
                # change the current message
                s.query(models.Welcomemessage) \
                    .filter(
                        models.Welcomemessage.guild_id ==
                        ctx.guild.id
                    ) \
                    .update({
                        models.Welcomemessage.text: msg
                    })

                s.commit()

                await ctx.send(
                    "Welcomemessage was updated correctly."
                )

            else:
                # add a new message
                new_welcome = models.Welcomemessage(
                    guild_id=ctx.guild.id,
                    text=msg,
                    enable=True
                )

                s.add(new_welcome)

                s.commit()

                await ctx.send(
                    "Welcomemessage was updated correctly."
                )

            s.close()

        except Exception as e:
            logging.error(
                f"Error in youtube.add command: {e}"
            )
            s.rollback()
            s.close()

    @welcome.command()
    async def enable(self, ctx):
        # this will change the welcomemessage
        try:
            s = self.db.Session()

            # check if welcome is already existing
            if not self._welcome_exists(s, ctx.guild.id):
                await ctx.send(
                    "Welcomemessage is not configured."
                )
                s.close()
                return

            s.query(models.Welcomemessage) \
                .filter(
                    models.Welcomemessage.guild_id ==
                    ctx.guild.id
                ) \
                .update({
                    models.Welcomemessage.enable: True
                })

            s.commit()

            await ctx.send(
                "Welcomemessage was enabled."
            )

            s.close()

        except Exception as e:
            logging.error(
                f"Error in youtube.add command: {e}"
            )
            s.rollback()
            s.close()

    @welcome.command()
    async def disable(self, ctx):
        # this will change the welcomemessage
        try:
            s = self.db.Session()

            # check if welcome is already existing
            if not self._welcome_exists(s, ctx.guild.id):
                await ctx.send(
                    "Welcomemessage is not configured."
                )
                s.close()
                return

            s.query(models.Welcomemessage) \
                .filter(
                    models.Welcomemessage.guild_id ==
                    ctx.guild.id
                ) \
                .update({
                    models.Welcomemessage.enable: False
                })

            s.commit()

            await ctx.send(
                "Welcomemessage was disabled."
            )

            s.close()

        except Exception as e:
            logging.error(
                f"Error in youtube.add command: {e}"
            )
            s.rollback()
            s.close()

    def _welcome_exists(self, s, guild_id):
        try:
            if not s.query(
                exists()
                .where(
                    models.Welcomemessage.guild_id ==
                    guild_id
                    )).scalar():
                return False
            else:
                return True
        except Exception as e:
            logging.error(
                f"Error in _welcome_exists: {e}"
            )
            return False

    def _welcome_enabled(self, s, guild_id):
        try:
            if not s.query(
                exists()
                .where(
                    and_(
                        models.Welcomemessage.guild_id == guild_id,
                        models.Welcomemessage.enable == 1
                    )
                    )).scalar():
                return False
            else:
                return True
        except Exception as e:
            logging.error(
                f"Error in _welcome_exists: {e}"
            )
            return False


def setup(bot):
    bot.add_cog(Welcome(bot))
