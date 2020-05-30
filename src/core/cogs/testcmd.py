import discord
from discord.ext import commands

# TEST COMMAND CLASS
class Testcmd(commands.Cog, name="Testcommand Class"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sendtestmessage(self, ctx, *, member: discord.Member = None):
        member = member or ctx.author
        # send test message from db
        guild_id = member.guild.id

        dbresult = self.bot.db.gettestmessage(guild_id)

        text = dbresult['testmessage']

        await ctx.send(text)
        pass

def setup(bot):
	bot.add_cog(Testcmd(bot))