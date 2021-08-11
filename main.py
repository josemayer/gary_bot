import discord
import os
import requests
from discord import FFmpegPCMAudio
from pafy import new
from dotenv import load_dotenv
from bs4 import BeautifulSoup

client = discord.Client()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

load_dotenv()
TOKEN = os.getenv('TOKEN')

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

def weather(city):
    city = city + " clima"
    res = requests.get(f'https://www.google.com/search?q={city}&oq={city}&aqs=chrome.0.35i39l2j0l4j46j69i60.6128j1j7&sourceid=chrome&ie=UTF-8', headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    weather = soup.select('#wob_tm')[0].getText().strip()
    info = soup.select('#wob_dc')[0].getText().strip()
    humidity = soup.select('#wob_hm')[0].getText().strip()
    return weather, info, humidity

def time(city):
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

# =============================

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('>ze'):
        await message.channel.send("o + top!!")
        await message.channel.send("<:ze:874783389218140200>\n:necktie: :briefcase:\n:jeans:\n:mans_shoe:")

    if message.content == '>pedro':
        await message.channel.send("<:pedro:395610851370860544>\n:running_shirt_with_sash: :middle_finger:\n:shorts:\n:athletic_shoe:")

    if message.content == '>clovys':
        await message.channel.send("<:clovys:395608953930645504>\n:shirt: :thumbsup:\n:jeans:")
    
    if message.content == '>vs':
        await message.channel.send("<:clovys:395608953930645504> :vs: <:pedro:395610851370860544>")

    if message.content == '>bless':
        await message.channel.send(":cloud: <:pedro:395610851370860544> :cloud:\n:cloud: :pray: :cloud:")

    if message.content == '>ulisses':
        await message.channel.send(":billed_cap:\n<:ulisses:874778518003781663>\n:womans_clothes:\n:shorts:\n:sandal:")

    if message.content == '>victor':
        await message.channel.send("<:victor:874775818881101824>\n:bikini: :point_right:\n:socks:")

    if message.content == '>cone':
        await message.channel.send("<:cone:874781203297886259>\n:school_satchel: :baby_bottle:\n:jeans:\n:hiking_boot:")

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

            local_weather = weather(city)
            local_time = time(city)
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


    if message.content == '>join':
        ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
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

    if message.content == '>leave':
        for vc in client.voice_clients:
            if vc.guild == message.guild:
                await vc.disconnect()

@client.event
async def on_connect():
    print("O bot está em execução!")

client.run(TOKEN)
