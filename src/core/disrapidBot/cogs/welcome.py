import discord
import logging
from discord.ext import commands

# TMP test cog class
class Welcome(commands.Cog, name="Welcome Message Extension"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send('Welcome {0.mention}.'.format(member))

    @commands.command()
    async def welcometest(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author

        # get welcomemessage for current server
        try:
            # init new session
            session = self.bot.db.Session()

            message = self.bot.db.get_active_welcomemessage(session, member.guild.id)

            if message == None:
                raise Exception("no active welcomemessage for this server")
            else:
                # check if channel_id is set -> send this message to a channel
                # if not -> send this to a user via DM
                if message.channel_id != None:
                    await self.bot.channel(message.channel_id).send(message.text)
                else:
                    await member.send(message.text)

            session.close()

        except Exception as e:
            logging.warning(e)

def setup(bot):
	bot.add_cog(Welcome(bot))