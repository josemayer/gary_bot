import aiohttp
import json
from time import strftime, gmtime
from datetime import timedelta
from config import RIOT_API_KEY, VISUALCROSSING_API_KEY

async def fetch_json(url, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            return None

async def list_matches(gameName, tagLine):
    num_partidas = 5
    user = await fetch_json(f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={RIOT_API_KEY}')

    if not user:
        return None, None, None

    user_data = await fetch_json(f'https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{user["puuid"]}?api_key={RIOT_API_KEY}')
    user_puuid = user['puuid']
    user_name = f"{user['gameName']}#{user['tagLine']}"

    ddragon_versions = await fetch_json('https://ddragon.leagueoflegends.com/api/versions.json')
    user_icon = f"https://ddragon.leagueoflegends.com/cdn/{ddragon_versions[0]}/img/profileicon/{user_data['profileIconId']}.png"

    matches_ids = await fetch_json(f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{user_puuid}/ids?start=0&count={num_partidas}&api_key={RIOT_API_KEY}')
    if not matches_ids:
        return None, None, None

    games = []
    queues_info = await fetch_json(f'https://static.developer.riotgames.com/docs/lol/queues.json')

    for match_id in matches_ids:
        match_info = await fetch_json(f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}')
        if not match_info:
            continue

        participant_info = next((p for p in match_info['info']['participants'] if p['puuid'] == user_puuid), None)
        if not participant_info:
            continue

        queue_info = next((q for q in queues_info if q['queueId'] == match_info['info']['queueId']), None)
        nome_fila = queue_info['description'][:-6] if queue_info else "Unknown"

        game_result = "Vitória" if participant_info['win'] else "Derrota"
        tempo_partida_sec = match_info['info']['gameDuration']
        tempo_partida = strftime('%H:%M:%S', gmtime(tempo_partida_sec)) if tempo_partida_sec >= 3600 else strftime('%M:%S', gmtime(tempo_partida_sec))

        games.append([
            nome_fila,
            game_result,
            tempo_partida,
            participant_info['kills'],
            participant_info['deaths'],
            participant_info['assists'],
            participant_info['championName'],
            participant_info['totalMinionsKilled'],
            participant_info['champLevel']
        ])

    return user_name, user_icon, games

def treat_links(url):
    return f"https://{url[2:]}" if url.startswith("//") else url

def valid_playlist_link(url):
    return "&list=" in url or "?list=" in url

def format_duration(duration):
    return strftime("%H:%M:%S", gmtime(duration)) if duration > 3600 else strftime("%M:%S", gmtime(duration))

async def get_weather_time_data(city):
    return await fetch_json(f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup=metric&lang=pt&key={VISUALCROSSING_API_KEY}&contentType=json')
