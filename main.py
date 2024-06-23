import os
import urllib.error  # Import urllib.error
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

import subprocess
import json
import socket  # Import socket

from typing import List

# load the environment variables
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

youtube_url = "https://www.youtube.com/watch?v=4WO5kJChg3w"

os.makedirs("downloaded_videos", exist_ok=True)

try:
    # pytube download video part
    yt = YouTube(youtube_url)
    video = yt.streams.filter(file_extension='mp4').first()
    if video is None:
        raise ValueError("No mp4 stream available.")
    
    safe_title = yt.title.replace(' ', '_')
    filename = f"downloaded_videos/{safe_title}.mp4"
    
    video.download(filename=filename)
    print(f"Downloaded video to {filename}")

except urllib.error.URLError as e:
    print(f"Failed to open URL: {e.reason}")
except socket.gaierror as e:
    print(f"Address-related error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
