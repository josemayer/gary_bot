import discord
from discord.ext import commands
from utils.helpers import list_matches, treat_links
from dotenv import load_dotenv
import os

class Riot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='matchs')
    async def matchs_command(self, ctx, *, nickname: str):
        gameName, tagLine = "", ""
        try:
            gameName, tagLine = nickname.split('#')
        except:
            await ctx.send(":question: Formato de invocador inválido! Use o formato `Nome#Tag`")
            return

        nickname, icon, games = await list_matches(gameName, tagLine)
        if nickname is None:
            await ctx.send(":question: Invocador não encontrado!")
            return
        embed = discord.Embed(title=f"Histórico de {nickname}", description=f"Partidas recentes de League of Legends de {nickname}", color=0x7b0ec9)
        embed.set_thumbnail(url=treat_links(icon))
        for game in games:
            emoji = 'blue_circle' if game[1] == 'Derrota' else 'green_circle' if game[1] == 'Vitória' else 'red_circle'
            embed.add_field(
                name=f":{emoji}: ({game[0]}) - {game[1]}",
                value=f"**{game[6]}**\nKDA: {game[3]}/{game[4]}/{game[5]}\nNível {game[8]}, {game[7]} CS\nDuração: {game[2]}",
                inline=False
            )
        embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Riot(bot))
