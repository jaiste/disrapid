import logging
from discord.ext import commands
from db.guild import Guild


class Welcome(commands.Cog, name="Welcome Message Extension"):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # send a welcomemessage to new member if activated
        try:
            s = self.db.Session()

            guild = s.query(Guild).get(member.guild.id)
            message = guild.welcomemessage

            if message is None:
                logging.debug(
                    "cogs.welcome.on_member_join: no message " +
                    f"found for guild-{member.guild.id}"
                )
            else:
                logging.debug(
                    "cogs.welcome.on_member_join: format message " +
                    f"for guild-{member.guild.id}"
                )
                # format message, replace wars
                msg = message.text.replace(
                    "$username",
                    member.mention
                )
                msg = msg.replace(
                    "\\n",
                    "\n"
                )

                # check if channel_id is set -> send this message to a channel
                # if not -> send this to a user via DM
                if message.channel_id is not None:
                    logging.debug(
                        "cogs.welcome.on_member_join: send message " +
                        f"for guild-{member.guild.id} to channel-" +
                        f"{message.channel_id}"
                    )

                    await self.bot.channel(
                        message.channel_id
                    ).send(msg)
                else:
                    logging.debug(
                        "cogs.welcome.on_member_join: send message " +
                        f"for guild-{member.guild.id} to user via DM"
                    )

                    await member.send(msg)

            s.close()

        except Exception as e:
            logging.error(e)


def setup(bot):
    bot.add_cog(Welcome(bot))
