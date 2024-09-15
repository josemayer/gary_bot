import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')
VISUALCROSSING_API_KEY = os.getenv('VISUALCROSSING_API_KEY')
