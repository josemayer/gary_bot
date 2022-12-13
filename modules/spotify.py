import os
import sys
import requests
import base64
import json
import traceback
from dotenv import load_dotenv
from collections import namedtuple

sys.path.append('../')
load_dotenv()

clientId=os.getenv("SPOTIPY_CLIENT_ID")
clientSecret=os.getenv("SPOTIPY_CLIENT_SECRET")

def auth():
    url = "https://accounts.spotify.com/api/token"
    headers = {}
    data = {}

    message = f"{clientId}:{clientSecret}"
    messageBytes = message.encode('ascii')
    base64Bytes = base64.b64encode(messageBytes)
    base64Message = base64Bytes.decode('ascii')

    headers['Authorization'] = f"Basic {base64Message}"
    data['grant_type'] = "client_credentials"

    r = requests.post(url, headers=headers, data=data)

    token = r.json()['access_token']
    return token

def get_id_by_link(url):
    if 'playlist' in url:
        try:
            playlist_partial_id = url.split('playlist')[1][1:]
        except:
            print('erro ao recuperar o id da playlist, corrigir link')
        index_final = playlist_partial_id.find('?')
        playlist_id = playlist_partial_id[:index_final]

        return 'playlists', playlist_id
    elif 'album' in url:
        try:
            album_partial_id = url.split('album')[1][1:]
        except:
            print('erro ao recuperar o id do album, corrigir link')
        index_final = album_partial_id.find('?')
        album_id = album_partial_id[:index_final]
        
        return 'albums', album_id

def create_playlist_info(dict_playlist, typeList):
    playlist = []
    for music in dict_playlist['tracks']['items']:
        music_info = {}
        
        if typeList == 'playlists':
            music = music['track']
            
        music_info['title'] = music['name']
        music_info['length'] = music['duration_ms'] // 1000
        music_info['watch_url'] = music['external_urls']['spotify']
        artists = music['artists']
        music_info['artists'] = []
        for artist in artists:
            music_info['artists'].append(artist['name'])
        playlist.append(music_info)

    return playlist

def dict_to_object(dict_playlist):
    obj_music_info = namedtuple('music_info', dict_playlist.keys())(*dict_playlist.values())
    return obj_music_info

def playlist_musics(url):
    typeList, playlistId = get_id_by_link(url)

    playlistUrl = f"https://api.spotify.com/v1/{typeList}/{playlistId}"
    token = auth()
    headers = {
        "Authorization": "Bearer " + token
    }

    res = requests.get(url=playlistUrl, headers=headers)
    dict_playlist = res.json()
    print(dict_playlist)

    
    try:
        name_playlist = dict_playlist['name']
    except:
        traceback.print_exc()

    return name_playlist, create_playlist_info(dict_playlist, typeList)
