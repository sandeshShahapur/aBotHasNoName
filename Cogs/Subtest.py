from discord.ext import commands
import Test

class Subtest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @Test.test.command(invoke_without_command=False)
    async def subtest(self, ctx):
        print('Subtest command invoked.')

async def setup(bot):
    await bot.add_cog(Subtest(bot))