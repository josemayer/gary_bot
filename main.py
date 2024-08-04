# -*- coding: utf-8 -*-

import discord
import os
import requests
import asyncio
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from time import strftime, gmtime
from discord import FFmpegPCMAudio
from pytubefix import Playlist, Search, YouTube
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import sys
sys.path.append('functions/')
from tictactoe import saveImageTTT
sys.path.append('modules/')
import spotify

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

load_dotenv()
TOKEN = os.getenv('TOKEN')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
VISUALCROSSING_API_KEY = os.getenv('VISUALCROSSING_API_KEY')

# ===== LOAD DATA FILES =====

with open('commands/data.json', encoding='utf-8') as data:
    d = json.loads(data.read())
    sounds_list = d['sounds']
    emotes_list = d['emotes']
    data.close()

with open('commands/help.json', encoding='utf-8') as data:
    d = json.loads(data.read())
    help_comms = d
    data.close()

# ===========================

# ==============================

# ===== INITIALIZE MUSIC QUEUE =====

mq = {}

# ==================================

# ===== INITIALIZE IDLE COUNTERS =====

idle_counters = []

# =================================

# ===== GENERAL FUNCTIONS =====

def get_weather_time_data(city):
    request_city = requests.get(f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup=metric&lang=pt&key={VISUALCROSSING_API_KEY}&contentType=json')
    
    if request_city.status_code != 200:
        return ""
    
    city_json = request_city.json()
    return city_json

def list_matchs(user):
    num_partidas = 5
    request_user = requests.get(f'https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{user}?api_key={RIOT_API_KEY}')
    user_json = request_user.json()

    if request_user.status_code != 200:
        return (None, None, None)

    user_puuid = user_json['puuid']
    user_icon = f"https://opgg-static.akamaized.net/images/profile_icons/profileIcon{user_json['profileIconId']}.jpg"
    user_name = user_json['name']

    request_matchs_id = requests.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{user_puuid}/ids?start=0&count={num_partidas}&api_key={RIOT_API_KEY}')
    matchs_id = request_matchs_id.json()

    games = []
    for match in matchs_id:
        request_match = requests.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match}?api_key={RIOT_API_KEY}')
        match_info = request_match.json()
        
        # Pega a informação do usuário em específico
        for participant in match_info['info']['participants']:
            if participant['puuid'] == user_puuid:
                user_info = participant

        # Pega a informação de fila
        queues_info = requests.get(f'https://static.developer.riotgames.com/docs/lol/queues.json').json() 
        for q_info in queues_info:
            if q_info['queueId'] == match_info['info']['queueId']:
                nome_fila = q_info['description'][:-6]

        # Define se foi derrota ou vitória
        game_result = "Derrota"
        if user_info['win']:
            game_result = "Vitória"

        # Prepara o resultado da duração da partida
        tempo_partida_sec = match_info['info']['gameDuration']
        tempo_partida = strftime('%H:%M:%S', gmtime(tempo_partida_sec))
        if tempo_partida_sec < 3600:
            tempo_partida = tempo_partida[3:]

        array = [nome_fila,
                 game_result,
                 tempo_partida,
                 user_info['kills'],
                 user_info['deaths'],
                 user_info['assists'],
                 user_info['championName'],
                 user_info['totalMinionsKilled'],
                 user_info['champLevel']
                 ]

        games.append(array)
    return (user_name, user_icon, games) 
    
def treat_links(url):
    if url[0:2] == "//":
        url = "https://" + url[2:]
    return url

def valid_playlist_link(url):
    if url.find("&list=") != -1 or url.find("?list=") != -1:
        return True
    return False

def format_duration(duration):
    if (duration > 3600):
        return strftime("%H:%M:%S", gmtime(duration))
    return strftime("%M:%S", gmtime(duration))

def total_queue_duration(queue):
    total_sec = 0
    for music in queue:
        total_sec += music.length;

    return str(total_sec)

# =============================

class PageButtons(discord.ui.View):
    def __init__(self, message, embed, timeout=30):
        super().__init__(timeout=timeout)
        self.message = message
        self.embed = embed
        self.totalPages = self.embed.totalPages
        self.initialPage = self.embed.current    

        status_button = discord.ui.Button(custom_id="status",label=f"Página {self.initialPage}/{self.totalPages}", style=discord.ButtonStyle.secondary, disabled=True)
        prev_button = discord.ui.Button(custom_id="prev", label="<",style=discord.ButtonStyle.primary, disabled=True)
        if self.initialPage > 1:
            prev_button.disabled = False
        prev_button.callback = self.prev_action
        next_button = discord.ui.Button(custom_id="next", label=">", style=discord.ButtonStyle.primary, disabled=True)
        if self.initialPage < self.totalPages:
            next_button.disabled = False
        next_button.callback = self.next_action
        
        self.add_item(prev_button)
        self.add_item(status_button)
        self.add_item(next_button)

    async def prev_action(self, interaction:discord.Interaction):
        curr_page, embed_page = self.embed.prevPage()
        
        buttons = self.children
        for button in buttons:
            if button.custom_id == 'next':
                button.disabled = False
            elif button.custom_id == 'status':
                button.label = f"Página {curr_page}/{self.totalPages}"
            elif button.custom_id == 'prev':
                if curr_page == 1:
                    button.disabled = True

        await interaction.response.edit_message(embed=embed_page, view=self)

    async def next_action(self, interaction:discord.Interaction):
        curr_page, embed_page = self.embed.nextPage()
       
        buttons = self.children
        for button in buttons:
            if button.custom_id == 'prev':
                button.disabled = False
            elif button.custom_id == 'status':
                button.label = f"Página {curr_page}/{self.totalPages}"
            elif button.custom_id == 'next':
                if curr_page == self.totalPages:
                    button.disabled = True

        await interaction.response.edit_message(embed=embed_page, view=self)

    async def on_timeout(self):
        buttons = self.children
        for button in buttons:
            button.disabled = True
        await self.message.edit(view=self)

class HelpEmbed():
    def __init__(self, help_info, client):
        self.help_info = help_info
        self.totalPages = len(self.help_info)
        self.current = 1
        self.embed = discord.Embed(title=f":microscope: Gary Bot", description=f"Olá, agente! Meu nome é Gary, o pinguim inventor! Fui recrutado para executar pequenas missões cotidianas que lhe podem ser úteis. Se restarem dúvidas, não hesite em me contatar pelo celular da EPF. Estarei na minha oficina!", color=0x003366)
        self.embed.set_thumbnail(url='https://i.imgur.com/fWskrI4.png')
        self.embed.set_footer(text=f"{client.user}: Quantos pares de meia eu tenho?", icon_url=client.user.avatar.url)    
        self.updateEmbed()

    def updateEmbed(self):
        if len(self.embed.fields) > 0:
            self.embed.remove_field(0)

        i = 1
        for item in self.help_info:
            if self.current == i:
                j = 1
                valueField = f""
                for command in self.help_info[item]['content']:
                    descCommand = f""
                    if command['desc'] != "":
                        descCommand = f"> {command['desc']}\n"
                    valueField += f"`{str(j)}.` {command['header']}\n" + descCommand
                    j += 1
                self.embed.insert_field_at(0, name=help_comms[item]['title'], value=valueField, inline=False)
            i += 1
    
    def nextPage(self):
        if self.current + 1 > self.totalPages:
            return (-1, self.embed)
        else:
            self.current += 1
            self.updateEmbed()
            return (self.current, self.embed)

    def prevPage(self):
        if self.current - 1 < 1:
            return (-1, self.embed)
        else:
            self.current -= 1
            self.updateEmbed()
            return (self.current, self.embed)


class QueueEmbed():
    def __init__(self, numByPages, queue):
        self.queue = queue
        self.queue_size = len(self.queue)
        self.current = 1
        self.numByPages = numByPages
        self.firstElement = (self.numByPages * (self.current - 1)) + 1
        self.totalPages = max(int(np.ceil((self.queue_size - 1) / self.numByPages)), 1)
        self.queue_info = ""
        
        i = 1
        current_track = "`" + str(i) + ".` [" + self.queue[0]['obj'].title + "](" + self.queue[0]['obj'].watch_url + ") `(" + format_duration(self.queue[0]['obj'].length) + ")`"
        
        self.embed = discord.Embed(title=f":loud_sound: Tocando agora", description=current_track, color=0x7b0ec9)
        self.embed.set_footer(text=f"{self.queue_size} músicas na fila • Duração total: {self.calculateTotalDuration()}")
        i += 1
        self.updateEmbed(i)

    def updateEmbed(self, index):
        if len(self.embed.fields) > 0:
            self.embed.remove_field(0)

        self.queue_info = ""

        for music in self.queue[self.firstElement:self.firstElement + self.numByPages]:
            self.queue_info += "`" + str(index) + ".` [" + music['obj'].title + "](" + music['obj'].watch_url + ") `(" + format_duration(music['obj'].length) + ")`\n"
            index += 1

        if self.queue_info != "":
            self.embed.insert_field_at(0, name=f":headphones: Lista de reprodução", value=self.queue_info, inline=False)

    def updateFirstElement(self):
        return (self.numByPages * (self.current - 1)) + 1

    def nextPage(self):
        if self.current + 1 > self.totalPages:
            return (-1, self.embed)
        else:
            self.current += 1
            self.firstElement = self.updateFirstElement()
            self.updateEmbed(self.firstElement + 1)
            return (self.current, self.embed)

    def prevPage(self):
        if self.current - 1 < 1:
            return (-1, self.embed)
        else:
            self.current -= 1
            self.firstElement = self.updateFirstElement()
            self.updateEmbed(self.firstElement + 1)
            return (self.current, self.embed)

    def calculateTotalDuration(self):
        music_time = timedelta(0)
        for music in self.queue:
            music_time += timedelta(seconds=music['obj'].length)
        return str(music_time)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name=">help"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('>help'):
        help_embed = HelpEmbed(help_comms, client)
        mainMsg = await message.channel.send(content=f":clock9: Carregando...")
        help_view = PageButtons(mainMsg, help_embed)
        await mainMsg.edit(content="", embed=help_embed.embed, view=help_view)

    for emote in emotes_list:
        if message.content == '>' + emote['command']:
            for msg in emote['messages']:
                await message.channel.send(msg)

    if message.content.startswith('>hentai '):
        msg = message.content[8:]
        if len(msg) > 0:
            await message.channel.send(":mag: Procurando por " + msg)
            await message.author.send("Devidamente printado e enviado às autoridades!!!!")
    
    if message.content.startswith('>report '):
        city = message.content[8:]
        if len(city) > 0:
            city_data = get_weather_time_data(city)

            if city_data == "":
                await message.channel.send(":question: Cidade não encontrada")
                return

            hora = datetime.now(timezone(timedelta(hours=city_data['tzoffset']))).strftime("%d/%m/%Y, %H:%M")
            await message.channel.send(f":bar_chart: **Relatório de {city_data['resolvedAddress']}**:\n\n:alarm_clock: {hora}\n:thermometer: {city_data['currentConditions']['temp']} °C, {city_data['currentConditions']['humidity']}% de umidade, {city_data['currentConditions']['conditions']}")

    if message.content.startswith('>matchs '):
        nickname = message.content[8:]
        if len(nickname) > 0:
            nickname, icon, games = list_matchs(nickname)

            if nickname == None:
                await message.channel.send(f":question: Invocador não encontrado!")
                return

            embed = discord.Embed(title=f"Histórico de {nickname}", description=f"Partidas recentes de League of Legends de {nickname}", color=0x7b0ec9)
            embed.set_thumbnail(url=treat_links(icon))
            for j in range(len(games)):
                
                emoji = 'blue_circle'
                if games[j][1] == 'Derrota':
                    emoji = 'red_circle'
                elif games[j][1] == 'Vitória':
                    emoji = 'green_circle'

                embed.add_field(name=f":{emoji}: ({games[j][0]}) - {games[j][1]}", value=f"\t**{games[j][6]}**\n~~- -~~\tKDA: {games[j][3]}/{games[j][4]}/{games[j][5]}\n~~- -~~\t Nível {games[j][8]}, {games[j][7]} CS\n~~- -~~\tDuração: {games[j][2]}", inline=False)
            embed.set_footer(text=f"Solicitado por {message.author}", icon_url=message.author.avatar.url)
            
            await message.channel.send(embed=embed)

    if message.content.startswith('>ttt '):
        msg_content = message.content[5:]
        saveImageTTT(msg_content)
        await message.channel.send(file=discord.File('assets/imgs/msg.png'))
        os.remove('assets/imgs/msg.png')

    if message.content == '>join':
        join_audio = YouTube("https://www.youtube.com/watch?v=EVVp0J1-aU8")
        author = message.author
        channel = author.voice.channel

        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice != None:
            await message.channel.send(":exclamation: O bot já está conectado!")
            return

        vc = await channel.connect()
        audio = join_audio.streams.get_audio_only().url
        mq[vc.token] = []
        vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
        await idle_disconnect(vc, message.channel)

    for sound in sounds_list:
        if message.content == '>' + sound['command']:
            join_audio = YouTube(sound['link'])
            author = message.author
            channel = author.voice.channel

            voice = discord.utils.get(client.voice_clients, guild=message.guild)
            if voice == None:
                vc = await channel.connect()
            else:
                vc = voice

            if vc.is_playing() or vc.is_paused():
                await message.channel.send(":exclamation: O bot já está reproduzindo no momento!")
                return

            audio = join_audio.streams.get_audio_only().url
            vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
           
            await asyncio.sleep(sound['time'])

            await idle_disconnect(vc, message.channel) 

    if message.content.startswith(">play "):
        link = message.content[6:]
        author = message.author
        channel = author.voice.channel
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        fromSpotify = 'https://open.spotify.com/' in link
        if fromSpotify:
            name_playlist, playlist = spotify.playlist_musics(link)
            if voice == None:
                vc = await channel.connect()
                await message.channel.send("> :musical_note: **Gary na área** :musical_note:\n> no canal `" + channel.name + "`")
                mq[vc.token] = []
            else:
                vc = voice
            curr_q = mq[vc.token]

            if len(playlist) == 0:
                await message.channel.send(":question: Ocorreu um erro inesperado com a playlist!")
                return

            for music in playlist:
                music_obj = spotify.dict_to_object(music)
                curr_q.append({'from': 'spotify', 'obj': music_obj})
            await message.channel.send("> :arrow_double_down: **Adicionado à fila** : " + str(len(playlist)) + " músicas de `" + name_playlist + "`")


            if curr_q[0]['from'] == 'spotify':
                formato_spotify = curr_q.pop(0)

                query_first = formato_spotify['obj'].title + " - "
                for artist in formato_spotify['obj'].artists:
                    query_first += artist + ", "
                query_first += "(lyrics)"

                first_result = Search(query_first).results[0]
                join_audio = first_result
            
                curr_q.insert(0, {'from': 'youtube', 'obj': join_audio})
        else:
            playlist = valid_playlist_link(link)
            if voice == None:
                vc = await channel.connect()
                await message.channel.send("> :musical_note: **Gary na área** :musical_note:\n> no canal `" + channel.name + "`")
                mq[vc.token] = []
            else:
                vc = voice
            curr_q = mq[vc.token]

            if not playlist:
                primeiro_result = Search(link).results[0]
                join_audio = primeiro_result
            else:
                playlist_info = Playlist(link)
                playlist_musics = playlist_info.videos

                if len(playlist_info) == 0:
                    await message.channel.send(":question: Ocorreu um erro inesperado com a playlist!")
                    return

                join_audio = playlist_musics[0]


            if len(curr_q) > 0:
                if not playlist:
                    curr_q.append({'from': 'youtube', 'obj': join_audio})
                    await message.channel.send("> :arrow_double_down: **Adicionado à fila** [" + str(len(curr_q)) + "] : `" + join_audio.title + "`")
                else:
                    for music in playlist_musics:
                        curr_q.append({'from': 'youtube', 'obj': music})
                    await message.channel.send("> :arrow_double_down: **Adicionado à fila** : " + str(len(playlist_info)) + " músicas de `" + playlist_info.title + "`")
            else:
                if not playlist:
                    curr_q.append({'from': 'youtube', 'obj': join_audio})
                    await message.channel.send("> :notes: **Tocando** :notes: : `" + join_audio.title + "`")
                else:
                    for music in playlist_musics:
                        curr_q.append({'from': 'youtube', 'obj': music})
                    await message.channel.send("> :arrow_double_down: **Adicionado à fila** : " + str(len(playlist_info)) + " músicas de `" + playlist_info.title + "`")
                
        while len(curr_q) > 0:
            audio = curr_q[0]['obj'].streams.get_audio_only().url
            vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
        
            while vc.is_playing() or vc.is_paused():
                await asyncio.sleep(1)
            
            if len(curr_q) > 0:
                curr_q.pop(0)
                
                if len(curr_q) > 0 and curr_q[0]['from'] == 'spotify':
                    formato_spotify = curr_q.pop(0)

                    query_first = formato_spotify['obj'].title + " - "
                    for artist in formato_spotify['obj'].artists:
                        query_first += artist + ", "
                    query_first += "(lyrics)"

                    first_result = Search(query_first).results[0]
                    join_audio = first_result
                
                    curr_q.insert(0, {'from': 'youtube', 'obj': join_audio})

        for vc in client.voice_clients:
            if vc.guild == message.guild:
                await idle_disconnect(vc, message.channel)
                mq.pop(vc.token)

    if message.content == '>queue':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if (voice == None or len(mq[voice.token]) == 0):
            await message.channel.send("A fila de reprodução está vazia!")
            return

        queue_embed = QueueEmbed(7, mq[voice.token])
        mainMsg = await message.channel.send(content=f":clock9: Carregando...")
        queue_view = PageButtons(mainMsg, queue_embed)
        await mainMsg.edit(content="", embed=queue_embed.embed, view=queue_view)

    if message.content == '>skip':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        
        if len(mq[voice.token]) > 1:
            await message.channel.send(":fast_forward: **Pulando para**: `" + mq[voice.token][1]['obj'].title + "`")
        else:
            await message.channel.send(":arrow_down_small: A fila de reprodução chegou ao fim!")
        voice.stop()

    if message.content == '>pause':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        
        voice.pause()
        await message.channel.send(":pause_button: Música pausada")

    if message.content == '>resume':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        
        voice.resume()
        await message.channel.send(":arrow_forward: Música despausada")
    
    if message.content == '>shuffle':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return

        if (len(mq[voice.token]) > 1):
            mq_slice = mq[voice.token][1:]
            np.random.shuffle(mq_slice)
            mq[voice.token][1:] = mq_slice

            await message.channel.send(":twisted_rightwards_arrows: A fila de reprodução foi embaralhada!")
        else:
            await message.channel.send(":exclamation: A fila é pequena demais para ser embaralhada!")

    if message.content.startswith(">move "):
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return

        par = message.content[6:]
        num_at, num_to = par.split()

        if (num_at.isdigit() and num_to.isdigit()):
            num_at = int(num_at)
            num_to = int(num_to)
            if (1 < num_at <= len(mq[voice.token]) and 1 < num_to <= len(mq[voice.token])):
                music_at = mq[voice.token][num_at - 1]
                temp = mq[voice.token].pop(num_at - 1)
                mq[voice.token].insert(num_to - 1, temp)
                await message.channel.send(":left_right_arrow: **Movendo** `" + music_at['obj'].title + "` **para** `" + str(num_to) + "`")
                return
            else:
                await message.channel.send(":exclamation: Há números de posição maiores que a fila ou menores que 2")
                return
        else:
            await message.channel.send(":exclamation: Os pares não são adequados!")
            return
    if message.content == '>leave':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        
        if voice != None:
            voice.stop()

            if len(mq[voice.token]) > 0:
                mq[voice.token].clear()
                mq.pop(voice.token)

            for vc in client.voice_clients:
                if vc.guild == message.guild:
                    await vc.disconnect()
        else:
            await message.channel.send("O bot não está conectado!")

    if message.content.startswith('>remove '):
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        
        position = message.content[8:]
        position = position.replace(" ", "")
        
        if position.isdigit():
            position = int(position)
            if (1 < position <= len(mq[voice.token])):
                music = mq[voice.token].pop(position - 1)
                await message.channel.send(":hash: **Removendo** `" + music['obj'].title + "` da lista de reprodução!")
            else:
                await message.channel.send(":exclamation: O número da posição é maior que a fila ou menor que 2!")
                return
        else:
            await message.channel.send(":exclamation: A posição não é adequada!")
            return

    if message.content.startswith('>teste '):
        url = message.content[7:]
        playlist_spotify = spotify.playlist_musics(url)

        message_bot = ""
        for music in playlist_spotify:
            message_bot += music.title + ', '

        await message.channel.send(message_bot)

async def idle_disconnect(vc, channel):
    if vc.channel.id not in idle_counters:
        idle_counters.append(vc.channel.id)
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
        idle_counters.remove(vc.channel.id)

@client.event
async def on_connect():
    print("Executando")

client.run(TOKEN)
