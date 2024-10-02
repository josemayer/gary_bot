import discord
from discord.ext import commands
from pytubefix import YouTube
from discord import FFmpegPCMAudio
import json
import asyncio
import os

ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Emotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('data/emotes.json', encoding='utf-8') as data:
            d = json.load(data)
            self.emotes_list = d['emotes']
            self.sounds_list = d['sounds']

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith('>'):
            command = message.content[1:]
            await self.handle_emote_command(message, command)
            await self.handle_sound_command(message, command)

    async def handle_emote_command(self, message, command):
        for emote in self.emotes_list:
            if command == emote['command']:
                for msg in emote['messages']:
                    await message.channel.send(msg)
                break

    async def handle_sound_command(self, message, command):
        for sound in self.sounds_list:
            if command == sound['command']:
                join_audio = YouTube(sound['link'])
                author = message.author
                channel = author.voice.channel

                voice = discord.utils.get(self.bot.voice_clients, guild=message.guild)
                if voice is None:
                    vc = await channel.connect()
                else:
                    vc = voice

                if vc.is_playing() or vc.is_paused():
                    await message.channel.send(":exclamation: O bot já está reproduzindo no momento!")
                    return

                audio = join_audio.streams.get_audio_only().url
                vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))

                await asyncio.sleep(sound['time'])

                await self.idle_disconnect(vc, message.channel)
                break

def setup(bot):
    bot.add_cog(Emotes(bot))
