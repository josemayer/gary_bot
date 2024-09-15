import discord
from discord.ext import commands
from pytubefix import YouTube, Playlist, Search
from discord import FFmpegPCMAudio
import numpy as np
from utils.helpers import format_duration, valid_playlist_link
from utils.embeds import QueueEmbed, PageButtons
import asyncio
import os
import modules.spotify as spotify

ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = {}
        self.idle_counters = set()

    @commands.command(name='join')
    async def join_command(self, ctx):
        author = ctx.author
        channel = author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            await ctx.send(":exclamation: O bot já está conectado!")
            return
        vc = await channel.connect()
        join_audio = YouTube("https://www.youtube.com/watch?v=EVVp0J1-aU8")
        audio = join_audio.streams.get_audio_only().url
        self.music_queue[vc.token] = []
        vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
        await self.idle_disconnect(vc, ctx.channel)

    @commands.command(name='play')
    async def play_command(self, ctx, *, link: str):
        author = ctx.author
        channel = author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        fromSpotify = 'https://open.spotify.com/' in link

        if fromSpotify:
            await self.handle_spotify_link(ctx, link, voice, channel)
        else:
            await self.handle_youtube_link(ctx, link, voice, channel)

    async def handle_spotify_link(self, ctx, link, voice, channel):
        name_playlist, playlist = spotify.playlist_musics(link)
        if voice is None:
            vc = await channel.connect()
            await ctx.send(f"> :musical_note: **Gary na área** :musical_note:\n> no canal `{channel.name}`")
            self.music_queue[vc.token] = []
        else:
            vc = voice

        curr_q = self.music_queue[vc.token]
        if not playlist:
            await ctx.send(":question: Ocorreu um erro inesperado com a playlist!")
            return

        for music in playlist:
            music_obj = spotify.dict_to_object(music)
            curr_q.append({'from': 'spotify', 'obj': music_obj})

        await ctx.send(f"> :arrow_double_down: **Adicionado à fila** : {len(playlist)} músicas de `{name_playlist}`")

        if curr_q and curr_q[0]['from'] == 'spotify':
            await self.play_first_spotify_song(ctx, curr_q)

        await self.play_queue(ctx, vc, curr_q)

    async def handle_youtube_link(self, ctx, link, voice, channel):
        playlist = valid_playlist_link(link)
        if voice is None:
            vc = await channel.connect()
            await ctx.send(f"> :musical_note: **Gary na área** :musical_note:\n> no canal `{channel.name}`")
            self.music_queue[vc.token] = []
        else:
            vc = voice

        curr_q = self.music_queue[vc.token]
        if not playlist:
            join_audio = Search(link).videos[0]
        else:
            playlist_info = Playlist(link)
            playlist_musics = playlist_info.videos
            if not playlist_info:
                await ctx.send(":question: Ocorreu um erro inesperado com a playlist!")
                return
            join_audio = playlist_musics[0]

        if curr_q:
            if not playlist:
                curr_q.append({'from': 'youtube', 'obj': join_audio})
                await ctx.send(f"> :arrow_double_down: **Adicionado à fila** [{len(curr_q)}] : `{join_audio.title}`")
            else:
                for music in playlist_musics:
                    curr_q.append({'from': 'youtube', 'obj': music})
                await ctx.send(f"> :arrow_double_down: **Adicionado à fila** : {len(playlist_info)} músicas de `{playlist_info.title}`")
        else:
            if not playlist:
                curr_q.append({'from': 'youtube', 'obj': join_audio})
                await ctx.send(f"> :notes: **Tocando** :notes: : `{join_audio.title}`")
            else:
                for music in playlist_musics:
                    curr_q.append({'from': 'youtube', 'obj': music})
                await ctx.send(f"> :arrow_double_down: **Adicionado à fila** : {len(playlist_info)} músicas de `{playlist_info.title}`")

        await self.play_queue(ctx, vc, curr_q)

    async def play_first_spotify_song(self, ctx, curr_q):
        formato_spotify = curr_q.pop(0)
        query_first = f"{formato_spotify['obj'].title} - " + ", ".join(formato_spotify['obj'].artists) + " (lyrics)"
        first_result = Search(query_first).videos[0]
        curr_q.insert(0, {'from': 'youtube', 'obj': first_result})

    async def play_queue(self, ctx, vc, curr_q):
        if vc.is_playing() or vc.is_paused():
            return

        while curr_q:
            audio = curr_q[0]['obj'].streams.get_audio_only().url
            vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))

            while vc.is_playing() or vc.is_paused():
                await asyncio.sleep(1)

            if curr_q:
                curr_q.pop(0)
                if curr_q and curr_q[0]['from'] == 'spotify':
                    await self.play_first_spotify_song(ctx, curr_q)

        await self.idle_disconnect(vc, ctx.channel)
        self.music_queue.pop(vc.token)

    @commands.command(name='queue')
    async def queue_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None or not self.music_queue[voice.token]:
            await ctx.send("A fila de reprodução está vazia!")
            return
        queue_embed = QueueEmbed(7, self.music_queue[voice.token])
        main_msg = await ctx.send(content=":clock9: Carregando...")
        queue_view = PageButtons(main_msg, queue_embed)
        await main_msg.edit(content="", embed=queue_embed.embed, view=queue_view)

    @commands.command(name='skip')
    async def skip_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        if len(self.music_queue[voice.token]) > 1:
            await ctx.send(f":fast_forward: **Pulando para**: `{self.music_queue[voice.token][1]['obj'].title}`")
        else:
            await ctx.send(":arrow_down_small: A fila de reprodução chegou ao fim!")
        voice.stop()

    @commands.command(name='pause')
    async def pause_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        voice.pause()
        await ctx.send(":pause_button: Música pausada")

    @commands.command(name='resume')
    async def resume_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        voice.resume()
        await ctx.send(":arrow_forward: Música despausada")

    @commands.command(name='shuffle')
    async def shuffle_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        if len(self.music_queue[voice.token]) > 1:
            mq_slice = self.music_queue[voice.token][1:]
            np.random.shuffle(mq_slice)
            self.music_queue[voice.token][1:] = mq_slice
            await ctx.send(":twisted_rightwards_arrows: A fila de reprodução foi embaralhada!")
        else:
            await ctx.send(":exclamation: A fila é pequena demais para ser embaralhada!")

    @commands.command(name='move')
    async def move_command(self, ctx, num_at: int, num_to: int):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        if 1 < num_at <= len(self.music_queue[voice.token]) and 1 < num_to <= len(self.music_queue[voice.token]):
            music_at = self.music_queue[voice.token].pop(num_at - 1)
            self.music_queue[voice.token].insert(num_to - 1, music_at)
            await ctx.send(f":left_right_arrow: **Movendo** `{music_at['obj'].title}` **para** `{num_to}`")
        else:
            await ctx.send(":exclamation: Há números de posição maiores que a fila ou menores que 2")

    @commands.command(name='leave')
    async def leave_command(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice:
            voice.stop()
            if self.music_queue[voice.token]:
                self.music_queue[voice.token].clear()
                self.music_queue.pop(voice.token)
            await voice.disconnect()
        else:
            await ctx.send("O bot não está conectado!")

    @commands.command(name='remove')
    async def remove_command(self, ctx, position: int):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice is None:
            await ctx.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        if 1 < position <= len(self.music_queue[voice.token]):
            music = self.music_queue[voice.token].pop(position - 1)
            await ctx.send(f":hash: **Removendo** `{music['obj'].title}` da lista de reprodução!")
        else:
            await ctx.send(":exclamation: O número da posição é maior que a fila ou menor que 2!")

    async def idle_disconnect(self, vc, channel):
        if vc.channel.id not in self.idle_counters:
            self.idle_counters.add(vc.channel.id)
            counter = 0
            while counter < 150:
                await asyncio.sleep(1)
                if not vc.is_connected():
                    break
                if not vc.is_playing() and not vc.is_paused():
                    counter += 1
                else:
                    counter = 0
            if vc.is_connected():
                await channel.send(":zzz: Você ainda está aí, agente? Vou me retirar da missão por enquanto. É só me chamar, caso precise!")
                await vc.disconnect()
            self.idle_counters.remove(vc.channel.id)

def setup(bot):
    bot.add_cog(Music(bot))

