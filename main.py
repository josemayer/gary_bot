# -*- coding: utf-8 -*-

import discord
from discord_components import DiscordComponents, Button, ButtonStyle
import os
import requests
import asyncio
import json
import numpy as np
from datetime import datetime, timezone, timedelta
from time import strftime, gmtime
from discord import FFmpegPCMAudio
from pytube import Playlist, Search, YouTube
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import sys
sys.path.append('functions/')
from tictactoe import saveImageTTT

client = discord.Client()
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
        
        # Pega a informa????o do usu??rio em espec??fico
        for participant in match_info['info']['participants']:
            if participant['puuid'] == user_puuid:
                user_info = participant

        # Pega a informa????o de fila
        queues_info = requests.get(f'https://static.developer.riotgames.com/docs/lol/queues.json').json() 
        for q_info in queues_info:
            if q_info['queueId'] == match_info['info']['queueId']:
                nome_fila = q_info['description'][:-6]

        # Define se foi derrota ou vit??ria
        game_result = "Derrota"
        if user_info['win']:
            game_result = "Vit??ria"

        # Prepara o resultado da dura????o da partida
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

@client.event
async def on_ready():
    DiscordComponents(client)
    await client.change_presence(activity=discord.Game(name=">help"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('>help'):
        totalPages = len(help_comms)
        embed = discord.Embed(title=f":microscope: Gary Bot", description=f"Ol??, agente! Meu nome ?? Gary, o pinguim inventor! Fui recrutado para executar pequenas miss??es cotidianas que lhe podem ser ??teis. Se restarem d??vidas, n??o hesite em me contatar pelo celular da EPF. Estarei na minha oficina!", color=0x003366)
        embed.set_thumbnail(url='https://i.imgur.com/fWskrI4.png')
        
        current = 1
    
        i = 1
        for item in help_comms:
            if current == i:
                j = 1
                valueField = f""
                for command in help_comms[item]['content']:
                    descCommand = f""
                    if command['desc'] != "":
                        descCommand = f"> {command['desc']}\n"
                    valueField += f"`{str(j)}.` {command['header']}\n" + descCommand
                    j += 1
                embed.add_field(name=help_comms[item]['title'], value=valueField, inline=False)
            i += 1

        embed.set_footer(text=f"{client.user}: Quantos pares de meia eu tenho?", icon_url=client.user.avatar_url)    
        mainMsg = await message.channel.send(embed=embed,
                                    components = [
                                                [
                                                Button(
                                                    label = "<",
                                                    id = "back",
                                                    style = ButtonStyle.blue,
                                                    disabled = True
                                                ),
                                                Button(
                                                    label = f"P??gina {current}/{totalPages}",
                                                    id = "cur",
                                                    style = ButtonStyle.grey,
                                                    disabled = True
                                                ),
                                                Button(
                                                    label = ">",
                                                    id = "front",
                                                    style = ButtonStyle.blue
                                                )
                                                ]
                                            ]
                                        )

        while True:
            try:
                interaction = await client.wait_for(
                    "button_click",
                    check = lambda i: i.component.id in ["back", "front"], 
                    timeout = 10.0 
                )
                buttonNext = False
                buttonPrev = False
                if interaction.component.id == "back":
                    current -= 1
                elif interaction.component.id == "front":
                    current += 1

                if current >= totalPages:
                    buttonNext = True
                elif current <= 1:
                    buttonPrev = True

                embed.remove_field(0)

                i = 1
                for item in help_comms:
                    if current == i:
                        j = 1
                        valueField = f""
                        for command in help_comms[item]['content']:
                            descCommand = f""
                            if command['desc'] != "":
                                descCommand = f"> {command['desc']}\n"
                            valueField += f"`{str(j)}.` {command['header']}\n" + descCommand
                            j += 1
                        embed.insert_field_at(0, name=help_comms[item]['title'], value=valueField, inline=False)
                    i += 1

                await interaction.respond(
                    type = 7,
                    embed = embed,
                    components = [
                        [
                            Button(
                                label = "<",
                                id = "back",
                                style = ButtonStyle.blue,
                                disabled = buttonPrev
                            ),
                            Button(
                                label = f"P??gina {current}/{totalPages}",
                                id = "cur",
                                style = ButtonStyle.grey,
                                disabled = True
                            ),
                            Button(
                                label = ">",
                                id = "front",
                                style = ButtonStyle.blue,
                                disabled = buttonNext
                            )
                        ]
                    ]
                )
            except asyncio.TimeoutError:
                await mainMsg.edit(
                    components = [
                        [
                            Button(
                                label = "<",
                                id = "back",
                                style = ButtonStyle.blue,
                                disabled = True
                            ),
                            Button(
                                label = f"P??gina {current}/{totalPages}",
                                id = "cur",
                                style = ButtonStyle.grey,
                                disabled = True
                            ),
                            Button(
                                label = ">",
                                id = "front",
                                style = ButtonStyle.blue,
                                disabled = True
                            )
                        ]
                    ]
                )
                break



    for emote in emotes_list:
        if message.content == '>' + emote['command']:
            for msg in emote['messages']:
                await message.channel.send(msg)

    if message.content.startswith('>hentai '):
        msg = message.content[8:]
        if len(msg) > 0:
            await message.channel.send(":mag: Procurando por " + msg)
            await message.author.send("Devidamente printado e enviado ??s autoridades!!!!")
    
    if message.content.startswith('>report '):
        city = message.content[8:]
        if len(city) > 0:
            city_data = get_weather_time_data(city)

            if city_data == "":
                await message.channel.send(":question: Cidade n??o encontrada")
                return

            hora = datetime.now(timezone(timedelta(hours=city_data['tzoffset']))).strftime("%d/%m/%Y, %H:%M")
            await message.channel.send(f":bar_chart: **Relat??rio de {city_data['resolvedAddress']}**:\n\n:alarm_clock: {hora}\n:thermometer: {city_data['currentConditions']['temp']} ??C, {city_data['currentConditions']['humidity']}% de umidade, {city_data['currentConditions']['conditions']}")

    if message.content.startswith('>matchs '):
        nickname = message.content[8:]
        if len(nickname) > 0:
            nickname, icon, games = list_matchs(nickname)

            if nickname == None:
                await message.channel.send(f":question: Invocador n??o encontrado!")
                return

            embed = discord.Embed(title=f"Hist??rico de {nickname}", description=f"Partidas recentes de League of Legends de {nickname}", color=0x7b0ec9)
            embed.set_thumbnail(url=treat_links(icon))
            for j in range(len(games)):
                
                emoji = 'blue_circle'
                if games[j][1] == 'Derrota':
                    emoji = 'red_circle'
                elif games[j][1] == 'Vit??ria':
                    emoji = 'green_circle'

                embed.add_field(name=f":{emoji}: ({games[j][0]}) - {games[j][1]}", value=f"\t**{games[j][6]}**\n~~- -~~\tKDA: {games[j][3]}/{games[j][4]}/{games[j][5]}\n~~- -~~\t N??vel {games[j][8]}, {games[j][7]} CS\n~~- -~~\tDura????o: {games[j][2]}", inline=False)
            embed.set_footer(text=f"Solicitado por {message.author}", icon_url=message.author.avatar_url)
            
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
            await message.channel.send(":exclamation: O bot j?? est?? conectado!")
            return

        vc = await channel.connect()
        audio = join_audio.streams.get_audio_only().url
        vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
        vc.is_playing()
    
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
                await message.channel.send(":exclamation: O bot j?? est?? reproduzindo no momento!")
                return

            audio = join_audio.streams.get_audio_only().url
            vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
           
            await asyncio.sleep(sound['time'])

            if vc != None:
                for vc in client.voice_clients:
                    if vc.guild == message.guild:
                        await vc.disconnect()

    if message.content.startswith(">play "):
        link = message.content[6:]
        author = message.author
        channel = author.voice.channel
        playlist = valid_playlist_link(link)
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        if voice == None:
            vc = await channel.connect()
            await message.channel.send("> :musical_note: **Gary na ??rea** :musical_note:\n> no canal `" + channel.name + "`")
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
                curr_q.append(join_audio)
                await message.channel.send("> :arrow_double_down: **Adicionado ?? fila** [" + str(len(mq)) + "] : `" + join_audio.title + "`")
            else:
                for music in playlist_musics:
                    curr_q.append(music)
                await message.channel.send("> :arrow_double_down: **Adicionado ?? fila** : " + str(len(playlist_info)) + " m??sicas de `" + playlist_info.title + "`")
        else:
            if not playlist:
                curr_q.append(join_audio)
                await message.channel.send("> :notes: **Tocando** :notes: : `" + join_audio.title + "`")
            else:
                for music in playlist_musics:
                    curr_q.append(music)
                await message.channel.send("> :arrow_double_down: **Adicionado ?? fila** : " + str(len(playlist_info)) + " m??sicas de `" + playlist_info.title + "`")
            
            while len(curr_q) > 0:
                audio = curr_q[0].streams.get_audio_only().url
                vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
            
                while vc.is_playing() or vc.is_paused():
                    await asyncio.sleep(1)
                
                if len(curr_q) > 0:
                    curr_q.pop(0)

            for vc in client.voice_clients:
                if vc.guild == message.guild:
                    mq.pop(vc.token)
                    await vc.disconnect()


    if message.content == '>queue':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if (voice == None or len(mq[voice.token]) == 0):
            await message.channel.send("A fila de reprodu????o est?? vazia!")
            return

        current = 1;
        numByPage = 7;
        firstElement = (numByPage * (current - 1)) + 1
        totalPages = int(np.ceil((len(mq[voice.token]) - 1) / numByPage))

        queue = np.array(mq[voice.token])
        queue_info = ""
        i = 1

        current_track = "`" + str(i) + ".` [" + queue[0].title + "](" + queue[0].watch_url + ") `(" + format_duration(queue[0].length) + ")`"
        i += 1

        for music in queue[firstElement:firstElement + numByPage]:
            queue_info += "`" + str(i) + ".` [" + music.title + "](" + music.watch_url + ") `(" + format_duration(music.length) + ")`\n"
            i += 1

        embed = discord.Embed(title=f":loud_sound: Tocando agora", description=current_track, color=0x7b0ec9)
        if queue_info != "":
            embed.add_field(name=f":headphones: Lista de reprodu????o", value=queue_info, inline=False)
            embed.add_field(name=f"{len(mq[voice.token])} m??sicas na fila.", value=f"Dura????o total m??dia esperada: entre {format_duration(len(mq[voice.token])*180)} e {format_duration(len(mq[voice.token])*300)}", inline=False)

        mainMsg = await message.channel.send(embed=embed, 
                                               components = [
                                                [
                                                Button(
                                                    label = "<",
                                                    id = "back",
                                                    style = ButtonStyle.blue,
                                                    disabled = True
                                                ),
                                                Button(
                                                    label = f"P??gina {current}/{totalPages}",
                                                    id = "cur",
                                                    style = ButtonStyle.grey,
                                                    disabled = True
                                                ),
                                                Button(
                                                    label = ">",
                                                    id = "front",
                                                    style = ButtonStyle.blue,
                                                    disabled = False
                                                )
                                                ]
                                            ]
                                        )
        while True:
            try:
                interaction = await client.wait_for(
                    "button_click",
                    check = lambda i: i.component.id in ["back", "front"], 
                    timeout = 10.0 
                )
                buttonNext = False
                buttonPrev = False
                if interaction.component.id == "back":
                    current -= 1
                elif interaction.component.id == "front":
                    current += 1

                if current >= totalPages:
                    buttonNext = True
                elif current <= 1:
                    buttonPrev = True
                
                firstElement = (numByPage * (current - 1)) + 1
                lastElement = firstElement + numByPage
                if (lastElement > len(mq[voice.token])):
                    outOffset = lastElement - len(mq[voice.token])
                    lastElement = lastElement - outOffset

                queue_info = ""
                i = firstElement + 1
                for music in queue[firstElement:lastElement]:
                    queue_info += "`" + str(i) + ".` [" + music.title + "](" + music.watch_url + ") `(" + format_duration(music.length) + ")`\n"
                    i += 1

                embed.remove_field(0) 
                embed.insert_field_at(0, name=f":headphones: Lista de reprodu????o", value=queue_info, inline=False)
    
                await interaction.respond(
                    type = 7,
                    embed = embed,
                    components = [
                        [
                            Button(
                                label = "<",
                                id = "back",
                                style = ButtonStyle.blue,
                                disabled = buttonPrev
                            ),
                            Button(
                                label = f"P??gina {current}/{totalPages}",
                                id = "cur",
                                style = ButtonStyle.grey,
                                disabled = True
                            ),
                            Button(
                                label = ">",
                                id = "front",
                                style = ButtonStyle.blue,
                                disabled = buttonNext
                            )
                        ]
                    ]
                )
            except asyncio.TimeoutError:
                await mainMsg.edit(
                    components = [
                        [
                            Button(
                                label = "<",
                                id = "back",
                                style = ButtonStyle.blue,
                                disabled = True
                            ),
                            Button(
                                label = f"P??gina {current}/{totalPages}",
                                id = "cur",
                                style = ButtonStyle.grey,
                                disabled = True
                            ),
                            Button(
                                label = ">",
                                id = "front",
                                style = ButtonStyle.blue,
                                disabled = True
                            )
                        ]
                    ]
                )
                break

    if message.content == '>skip':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot n??o est?? tocando nenhuma m??sica no momento")
            return
        
        if len(mq[voice.token]) > 1:
            voice.pause()
            mq[voice.token].pop(0)
            audio = mq[voice.token][0].streams.get_audio_only().url
            voice.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
            await message.channel.send(":fast_forward: **Pulando para**: `" + mq[voice.token][0].title + "`")
        else:
            voice.stop()
            await message.channel.send(":arrow_down_small: A fila de reprodu????o chegou ao fim!")

    if message.content == '>pause':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot n??o est?? tocando nenhuma m??sica no momento")
            return
        
        voice.pause()
        await message.channel.send(":pause_button: M??sica pausada")

    if message.content == '>resume':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot n??o est?? tocando nenhuma m??sica no momento")
            return
        
        voice.resume()
        await message.channel.send(":arrow_forward: M??sica despausada")
    
    if message.content == '>shuffle':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot n??o est?? tocando nenhuma m??sica no momento")
            return

        if (len(mq[voice.token]) > 1):
            mq_slice = mq[voice.token][1:]
            np.random.shuffle(mq_slice)
            mq[voice.token][1:] = mq_slice

            await message.channel.send(":twisted_rightwards_arrows: A fila de reprodu????o foi embaralhada!")
        else:
            await message.channel.send(":exclamation: A fila ?? pequena demais para ser embaralhada!")

    if message.content.startswith(">move "):
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot n??o est?? tocando nenhuma m??sica no momento")
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
                await message.channel.send(":left_right_arrow: **Movendo** `" + music_at.title + "` **para** `" + str(num_to) + "`")
                return
            else:
                await message.channel.send(":exclamation: H?? n??meros de posi????o maiores que a fila ou menores que 2")
                return
        else:
            await message.channel.send(":exclamation: Os pares n??o s??o adequados!")
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
            await message.channel.send("O bot n??o est?? conectado!")

    if message.content.startswith('>remove '):
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot n??o est?? tocando nenhuma m??sica no momento")
            return
        
        position = message.content[8:]
        position = position.replace(" ", "")
        
        if position.isdigit():
            position = int(position)
            if (1 < position <= len(mq[voice.token])):
                music = mq[voice.token].pop(position - 1)
                await message.channel.send(":hash: **Removendo** `" + music.title + "` da lista de reprodu????o!")
            else:
                await message.channel.send(":exclamation: O n??mero da posi????o ?? maior que a fila ou menor que 2!")
                return
        else:
            await message.channel.send(":exclamation: A posi????o n??o ?? adequada!")
            return

@client.event
async def on_connect():
    print("Executando")

client.run(TOKEN)
