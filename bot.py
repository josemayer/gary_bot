# -*- coding: utf-8 -*-

import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
from commands import general, music, riot, emotes

intents = discord.Intents.default()
intents.message_content = True

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.add_cog(general.General(bot))
    await bot.add_cog(music.Music(bot))
    await bot.add_cog(riot.Riot(bot))
    await bot.add_cog(emotes.Emotes(bot))

    await bot.change_presence(activity=discord.Game(name=">help"))
    print(f'Logged in as {bot.user}')

if __name__ == "__main__":
    bot.run(TOKEN)
