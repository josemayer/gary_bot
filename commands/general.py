import discord
from discord.ext import commands
from modules.tictactoe import saveImageTTT
from utils.embeds import HelpEmbed, PageButtons
import json
import os

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('data/help.json', encoding='utf-8') as data:
            self.help_comms = json.load(data)

    @commands.command(name='help')
    async def help_command(self, ctx):
        help_embed = HelpEmbed(self.help_comms, self.bot)
        main_msg = await ctx.send(content=":clock9: Carregando...")
        help_view = PageButtons(main_msg, help_embed)
        await main_msg.edit(content="", embed=help_embed.embed, view=help_view)

    @commands.command(name='ttt')
    async def ttt_command(self, ctx, *, msg_content: str):
        saveImageTTT(msg_content)
        await ctx.send(file=discord.File('assets/imgs/msg.png'))
        os.remove('assets/imgs/msg.png')

    @commands.command(name='hentai')
    async def hentai_command(self, ctx, *, character: str):
        if character is None:
            await ctx.send(f":exclamation: Você precisa especificar um personagem!")
            return

        await ctx.send(f":mag: Pesquisando por {character}...")
        await ctx.author.send(f"Devidamente printado e enviado às autoridades!!!!")

def setup(bot):
    bot.add_cog(General(bot))
