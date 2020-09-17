import logging
from discord.ext import commands
# from datetime import datetime
# import random
import models
from sqlalchemy import exists, and_
from helpers import (
    is_role,
    is_string,
    get_role_id_from_string
)
# import os
import emoji  # emoji conversion
import re  # regex


class Reactionrole(commands.Cog, name="Reactionrole"):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    # EVENTS
    # ---
    #
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # this happens when a reaction was added to any message
        try:
            s = self.db.Session()

            user = payload.member
            guild = payload.member.guild
            role_n = self._convert_emoji_to_string(payload.emoji.name)

            # check if bot is the message owner or the reaction initiator
            # this is needed because we don't want to react the bot to other
            # peoples messages, only if this is a reactionrole message

            # ignore message if we're the initiator
            if user.id == self.bot.user.id:
                return

            # ignore if message is not ours
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id != self.bot.user.id:
                return

            # get role_id by name
            role_id = self._get_reactionrole_id(s, role_n, guild.id)

            if role_id is not None:
                # assign role to user
                await user.add_roles(user.guild.get_role(int(role_id)))

        except Exception as e:
            logging.error(
                f"Error in reactionrole event: {e}"
            )
        finally:
            s.close()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            s = self.db.Session()

            user_id = payload.user_id
            guild_id = payload.guild_id
            guild = self.bot.get_guild(guild_id)
            user = guild.get_member(user_id)
            role_n = self._convert_emoji_to_string(payload.emoji.name)

            # check if bot is the message owner or the reaction initiator
            # this is needed because we don't want to react the bot to other
            # peoples messages, only if this is a reactionrole message

            # ignore message if we're the initiator
            if user_id == self.bot.user.id:
                return

            # ignore if message is not ours
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if message.author.id != self.bot.user.id:
                return

            # get role_id by name
            role_id = self._get_reactionrole_id(s, role_n, guild.id)

            if role_id is not None:
                # assign role to user
                await user.remove_roles(user.guild.get_role(int(role_id)))

        except Exception as e:
            logging.error(
                f"Error in reactionrole event: {e}"
            )
        finally:
            s.close()

    # ADMIN CONFIG COMMANDS
    # ---
    #
    @commands.has_permissions(administrator=True)
    @commands.group()
    async def reactionrole(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        try:
            s = self.db.Session()

            msg = "This is a list of all configured" \
                "Reactionroles on this guild.\n" \
                "for more details check the help.\n\n" \
                "```css\n" \
                "/* Syntax= .name : (role) */\n\n"

            # get all reactionroles
            for result in s.query(
                    models.Reactionrole
                ) \
                .filter(
                    models.Reactionrole.guild_id == ctx.guild.id,
                    ).all():

                role_n = ctx.guild.get_role(result.role_id).name

                msg += f".{result.name} : " \
                    f"{role_n}\n"

            msg += "```"

            await ctx.send(msg)

        except Exception as e:
            logging.error(
                f"Error in reactionrole command: {e}"
            )
        finally:
            s.close()

    @reactionrole.command()
    async def message(self, ctx):
        # this will write a reactionrole message where people can react to
        # --
        try:
            s = self.db.Session()

            msg = "Pick a role:\n"
            message = await ctx.send(msg)

            # get all reactionroles
            for result in s.query(
                    models.Reactionrole
                ) \
                .filter(
                    models.Reactionrole.guild_id == ctx.guild.id,
                    ).all():

                # get the emoji object of the reaction
                for e in ctx.guild.emojis:
                    if result.name == e.name:
                        await message.add_reaction(e)
                        break
                else:
                    # no emoji found for this command...
                    logging.error(f"emoji not found for result-{result.name}")
                    continue

        except Exception as e:
            logging.error(
                f"Error in reactionrole command: {e}"
            )
        finally:
            s.close()

    @reactionrole.command()
    async def add(self, ctx, msg: str, role: str):
        try:
            s = self.db.Session()

            # demojize the string
            role_n = self._convert_emoji_to_string(msg)

            if not is_string(role_n):
                return

            if is_role(role):
                # extract role id
                role_id = get_role_id_from_string(role)

                # skip if this role is not existing on the server
                if ctx.guild.get_role(int(role_id)) is None:
                    return

            else:
                return

            # check if this is already existing in database
            if self._exists_reactionrole(s, role_n, ctx.guild.id):
                await ctx.channel.send("Reactionrole is already existing.")
                return

            # reactionrole is not existing, add to list
            new_rr = models.Reactionrole(
                guild_id=ctx.guild.id,
                name=role_n,
                role_id=role_id
            )
            s.add(new_rr)
            s.commit()

            await ctx.channel.send("Reactionrole was added to list")

        except Exception as e:
            logging.error(
                f"Error in reactionrole command: {e}"
            )
            s.rollback()
        finally:
            s.close()

    @reactionrole.command()
    async def rm(self, ctx, msg: str, role: str):
        try:
            s = self.db.Session()

            # demojize the string
            role_n = self._convert_emoji_to_string(msg)

            if not is_string(role_n):
                return

            if is_role(role):
                # extract role id
                role_id = get_role_id_from_string(role)

                # skip if this role is not existing on the server
                if ctx.guild.get_role(int(role_id)) is None:
                    return

            else:
                return

            # check if this is already existing in database
            if self._exists_reactionrole(s, role_n, ctx.guild.id):
                # delete reactionrole
                obj = s.query(
                    models.Reactionrole
                ).filter(
                    models.Reactionrole.guild_id == ctx.guild.id,
                    models.Reactionrole.name == role_n,
                    models.Reactionrole.role_id == role_id
                )
                obj.delete()
                s.commit()

                await ctx.channel.send("Reactionrole was deleted from list.")

            else:
                await ctx.channel.send("Reactionrole is not existing.")

        except Exception as e:
            logging.error(
                f"Error in reactionrole command: {e}"
            )
            s.rollback()
        finally:
            s.close()

    def _exists_reactionrole(self, s, name, guild_id):
        # this return true when yt channel is followed for guild
        # ---
        #
        try:
            if s.query(
                exists().
                where(
                    and_(
                        models.Reactionrole.guild_id == guild_id,
                        models.Reactionrole.name == name
                    )
                )
            ).scalar():
                return True
        except Exception as e:
            logging.error(
                f"error in _exists_ytfollow: {e}"
            )
            return False

    def _get_reactionrole_id(self, s, name, guild_id):
        if self._exists_reactionrole(s, name, guild_id):
            role_id = s.query(
                    models.Reactionrole
            ).filter(
                models.Reactionrole.guild_id == guild_id,
                models.Reactionrole.name == name
            ).one()

            return role_id.role_id
        else:
            return None

    def _convert_emoji_to_string(self, inputstring):
        try:
            emojistr = emoji.demojize(inputstring)
            string = re.findall("[a-zA-Z_]+", emojistr)

            return string[0]

        except Exception as e:
            logging.error(
                f"error in _convert_emoji_to_string: {e}"
            )
            return None


def setup(bot):
    bot.add_cog(Reactionrole(bot))
