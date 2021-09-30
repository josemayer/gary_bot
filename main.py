import discord
import os
import requests
import asyncio
import json
import numpy as np
from discord import FFmpegPCMAudio
from pafy import new, get_playlist
from pytube import Playlist
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from youtube_dl import YoutubeDL
import sys
sys.path.append('functions/')
from tictactoe import saveImageTTT

client = discord.Client()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

load_dotenv()
TOKEN = os.getenv('TOKEN')

# ===== LOAD DATA FILES =====

with open('commands/data.json') as data:
    d = json.loads(data.read())
    sounds_list = d['sounds']
    emotes_list = d['emotes']
    data.close()

# ===========================

# ===== YOUTUBE-DL OPTIONS =====

ydl_opt = {'format': 'bestaudio', 'quiet': 'True'}

# ==============================

# ===== INITIALIZE MUSIC QUEUE =====

mq = []

# ==================================

# ===== GENERAL FUNCTIONS =====

def correct_name(city):
    city = city.replace(" ", "+")
    res = requests.get(f'https://www.google.com/search?q={city}&oq={city}&aqs=chrome.0.35i39l2j0l4j46j69i60.6128j1j7&sourceid=chrome&ie=UTF-8', headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    name_content = soup.select('.kno-ecr-pt');

    if name_content == []:
        return ""

    name = name_content[0].getText().strip()
    return name

def get_weather(city):
    city = city + " clima"
    res = requests.get(f'https://www.google.com/search?q={city}&oq={city}&aqs=chrome.0.35i39l2j0l4j46j69i60.6128j1j7&sourceid=chrome&ie=UTF-8', headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    weather = soup.select('#wob_tm')[0].getText().strip()
    info = soup.select('#wob_dc')[0].getText().strip()
    humidity = soup.select('#wob_hm')[0].getText().strip()
    return weather, info, humidity

def get_time(city):
    city = city + " horario"
    res = requests.get(f'https://www.google.com/search?q={city}&oq={city}&aqs=chrome.0.35i39l2j0l4j46j69i60.6128j1j7&sourceid=chrome&ie=UTF-8', headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    time = soup.select('.vk_bk')[0].getText().strip()
    date = soup.select('.KfQeJ')[0].getText().strip()
    return date, time

def list_matchs(user):
    res = requests.get(f'https://br.op.gg/summoner/userName={user}', headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    verify_list = soup.select('.GameItemList')
    if verify_list == []:
        return verify_list

    game_attribs = ['.GameItemList .GameType', '.GameItemList .GameResult', '.GameItemList .GameLength', '.GameItemList .KDA .KDA .Kill', '.GameItemList .KDA .KDA .Death', '.GameItemList .KDA .KDA .Assist', '.GameItemList .ChampionName', '.GameItemList .CS .CS', '.GameItemList .Level']
    game = []
    for element in game_attribs:
        game.append(soup.select(element))
    game_data = []
    for element in game:
        array = []
        for data in element:
            array.append(data.getText().strip())
        game_data.append(array)

    icon_content = soup.select('.ProfileImage')
    icon = icon_content[0]['src']
    return icon, game_data

def treat_links(url):
    if url[0:2] == "//":
        url = "https://" + url[2:]
    return url

def get_youtube_link(search):
    with YoutubeDL(ydl_opt) as ydl:
            r = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
    link = "https://www.youtube.com/watch?v=" + r['id']
    return link

def valid_playlist_link(url):
    if url.find("&list=") != -1 or url.find("?list=") != -1:
        return True
    return False

def format_playlist_link(url):
    position = url.find("list=")
    playlist_id = ""
    if position != -1:
        playlist_id = url[position + 5:]
        position = playlist_id.find("&")
        if position != -1:
            playlist_id = playlist_id[:position]

    if playlist_id == "":
        return ""
    else:
        return "https://www.youtube.com/playlist?list=" + playlist_id

# =============================

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('>help'):
        embed = discord.Embed(title=f":microscope: Gary Bot", description=f"Olá, agente! Meu nome é Gary, o pinguim inventor! Fui recrutado para executar pequenas missões cotidianas que lhe podem ser úteis. Se restarem dúvidas, não hesite em me contatar pelo celular da EPF. Estarei na minha oficina!", color=0x003366)
        embed.set_thumbnail(url='https://i.imgur.com/fWskrI4.png')
        embed.add_field(name=f"Comandos gerais", value=f"`1.` **>report** *<nome de uma cidade>*\n > Gera um relatório com os dados climáticos e de fuso horário da cidade especificada.\n`2.` **>matchs** *<nome de um invocador>*\n > Mostra o histórico das últimas 10 partidas de League of Legends do jogador especificado.\n`3.` **>join**\n > Acessa o canal de voz do usuário.\n`4.` **>leave**\n > Desconecta do canal de voz em que está conectado.\n`5.` **>ttt** *<mensagem>*\n > Gera uma mensagem codificada na simbologia tic-tac-toe, construída baseada [nesta tabela](https://i.imgur.com/3fifBia.png).\n`6.` **>hentai** *<nome de um personagem>*\n > ʕ•́ᴥ•̀ʔ", inline=False)
        embed.add_field(name=f"Comandos do Club Penguin", value=f"`1.` **>bless**\n`2.` **>clovys**\n`3.` **>cone**\n`4.` **>pedro**\n`5.` **>ulisses**\n`6.` **>victor**\n`7.` **>vs**\n`8.` **>ze**", inline=False)
        embed.add_field(name=f"Comandos de Vinheta", value=f"`1.` **>cavalo**\n`2.` **>btv**\n`3.` **>defuse**\n`4.` **>plant**\n`5.` **>jumpscare**\n`6.` **>fortnite**", inline=False)
        embed.add_field(name=f"Comandos de Música", value=f"`1.` **>play** *<link do youtube>*\n > Toca a música do youtube com o link fornecido.\n`2.` **>queue**\n > Mostra a fila de reprodução.", inline=False)
        embed.set_footer(text=f"{client.user}: Quantos pares de meia eu tenho?", icon_url=client.user.avatar_url)    
        await message.channel.send(embed=embed)

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
            city_correct = correct_name(city)

            if city_correct == "":
                await message.channel.send(":question: Cidade não encontrada")
                return

            local_weather = get_weather(city)
            local_time = get_time(city)
            await message.channel.send(f":bar_chart: **Relatório de {city_correct}**:\n\n:alarm_clock: {city_correct}, {local_time[0]}, {local_time[1]}\n:thermometer: {local_weather[0]} °C, {local_weather[2]} de umidade, {local_weather[1]}")

    if message.content.startswith('>matchs '):
        nickname = message.content[8:]
        if len(nickname) > 0:
            icon, games = list_matchs(nickname)

            if games == []:
                await message.channel.send(f":question: Invocador não encontrado!")
                return

            embed = discord.Embed(title=f"Histórico de {nickname}", description=f"Partidas recentes de League of Legends de {nickname}", color=0x7b0ec9)
            embed.set_thumbnail(url=treat_links(icon))
            for j in range(10):
                
                emoji = 'blue_circle'
                if games[1][j] == 'Defeat':
                    emoji = 'red_circle'
                elif games[1][j] == 'Victory':
                    emoji = 'green_circle'

                embed.add_field(name=f":{emoji}: ({games[0][j]}) - {games[1][j]}", value=f"\t**{games[6][j]}**\n~~- -~~\tKDA: {games[3][j]}/{games[4][j]}/{games[5][j]}\n~~- -~~\t{games[8][j]}, {games[7][j]} CS\n~~- -~~\tDuração: {games[2][j]}", inline=False)
            embed.set_footer(text=f"Solicitado por {message.author}", icon_url=message.author.avatar_url)
            
            await message.channel.send(embed=embed)

    if message.content.startswith('>ttt '):
        msg_content = message.content[5:]
        saveImageTTT(msg_content)
        await message.channel.send(file=discord.File('assets/imgs/msg.png'))
        os.remove('assets/imgs/msg.png')

    if message.content == '>join':
        join_audio = new("https://www.youtube.com/watch?v=EVVp0J1-aU8")
        author = message.author
        channel = author.voice.channel

        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice != None:
            await message.channel.send(":exclamation: O bot já está conectado!")
            return

        vc = await channel.connect()
        audio = join_audio.getbestaudio().url
        vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
        vc.is_playing()
    
    for sound in sounds_list:
        if message.content == '>' + sound['command']:
            join_audio = new(sound['link'])
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

            audio = join_audio.getbestaudio().url
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
            await message.channel.send("> :musical_note: **Gary na área** :musical_note:\n> no canal `" + channel.name + "`")
        else:
            vc = voice
        
        if not playlist:
            join_audio = new(get_youtube_link(link))
        else:
            playlist_info = Playlist(link)

            if len(playlist_info) == 0:
                await message.channel.send(":question: Ocorreu um erro inesperado com a playlist!")
                return

            join_audio = new(playlist_info[0])

        if len(mq) > 0:
            if not playlist:
                mq.append(join_audio)
                await message.channel.send("> :arrow_double_down: **Adicionado à fila** [" + str(len(mq)) + "] : `" + join_audio.title + "`")
            else:
                for music in playlist_info:
                    join_music_audio = new(music)
                    mq.append(join_music_audio)
                await message.channel.send("> :arrow_double_down: **Adicionado à fila** : " + str(len(playlist_info)) + " músicas de `" + playlist_info.title + "`")
        else:
            if not playlist:
                mq.append(join_audio)
                await message.channel.send("> :notes: **Tocando** :notes: : `" + join_audio.title + "`")
            else:
                for music in playlist_info:
                    join_music_audio = new(music)
                    mq.append(join_music_audio)
                await message.channel.send("> :arrow_double_down: **Adicionado à fila** : " + str(len(playlist_info)) + " músicas de `" + playlist_info.title + "`")
            
            while len(mq) > 0:
                audio = mq[0].getbestaudio().url
                vc.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
            
                while vc.is_playing() or vc.is_paused():
                    await asyncio.sleep(1)
                
                if len(mq) > 0:
                    mq.pop(0)

            for vc in client.voice_clients:
                if vc.guild == message.guild:
                    await vc.disconnect()

    if message.content == '>queue':
        if len(mq) == 0:
            await message.channel.send("A fila de reprodução está vazia!")
            return

        queue = np.array(mq)
        queue_info = ""
        i = 1

        current_track = str(i) + ". `" + queue[0].title + "` (" + queue[0].duration + ")"
        i += 1

        for music in queue[1:10]:
            queue_info += str(i) + ". `" + music.title + "` (" + music.duration + ")\n"
            i += 1

        embed = discord.Embed(title=f":loud_sound: Tocando agora", description=current_track, color=0x7b0ec9)
        if queue_info != "":
            embed.add_field(name=f":headphones: Lista de reprodução", value=queue_info, inline=False)

        await message.channel.send(embed=embed)

    if message.content == '>skip':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)

        if voice == None:
            await message.channel.send(":exclamation: O bot não está tocando nenhuma música no momento")
            return
        
        if len(mq) > 1:
            voice.pause()
            mq.pop(0)
            audio = mq[0].getbestaudio().url
            voice.play(FFmpegPCMAudio(audio, **ffmpeg_opts))
            await message.channel.send(":fast_forward: **Pulando para**: `" + mq[0].title + "`")
        else:
            voice.stop()
            await message.channel.send(":arrow_down_small: A fila de reprodução chegou ao fim!")

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

    if message.content == '>leave':
        voice = discord.utils.get(client.voice_clients, guild=message.guild)
        
        if voice != None:
            voice.stop()

            if len(mq) > 0:
                mq.clear()

            for vc in client.voice_clients:
                if vc.guild == message.guild:
                    await vc.disconnect()
        else:
            await message.channel.send("O bot não está conectado!")

@client.event
async def on_connect():
    print("O bot está em execução!")

client.run(TOKEN)
