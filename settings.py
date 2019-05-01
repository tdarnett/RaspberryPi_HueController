import os
from dotenv import load_dotenv
load_dotenv()

HUE_API_KEY = os.getenv("HUE_API_KEY")
ROOM_LIGHT = os.getenv("ROOM_LIGHT")