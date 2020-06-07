import discord
import logging
from discord.ext import commands

# TMP test cog class
class Welcome(commands.Cog, name="Welcome Message Extension"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send('Welcome {0.mention}.'.format(member))

    @commands.command()
    async def test(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send('Hello {0.name}~'.format(member))
        else:
            await ctx.send('Hello {0.name}... This feels familiar.'.format(member))
        self._last_member = member

    @commands.command()
    async def welcometest(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author

        # get welcomemessage for current server
        try:
            # init new session
            session = self.bot.db.Session()

            welcomemessage = session.query(schema.Welcomemessage).filter(schema.Welcomemessage.guild_id == member.guild.id, schema.Welcomemessage.enable == 1).one()
            
            
            #welcomemessage = self.bot.session.query(self.bot.Welcomemessage).filter(self.bot.Welcomemessage.guild_id == member.guild.id, self.bot.Welcomemessage.enable == 1).one()
            
            # check if channel_id is set -> send this message to a channel
            # if not -> send this to a user via DM
            # if welcomemessage.channel_id != None:
            #     await self.bot.channel(welcomemessage.channel_id).send(welcomemessage.text)
            # else:
            #     await member.send(welcomemessage.text)

        except Exception as e:
            logging.warning(e)

def setup(bot):
	bot.add_cog(Welcome(bot))
	# logging