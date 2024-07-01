import os
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import subprocess
import json
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv

# Load the environment variables
load_dotenv(find_dotenv())

youtube_url = "https://www.youtube.com/watch?v=4WO5kJChg3w"

os.makedirs("downloaded_videos", exist_ok=True)

# Pytube download video part
yt = YouTube(youtube_url)
video = yt.streams.filter(file_extension='mp4').first()
safe_title = yt.title.replace(' ', '_')
filename = f"downloaded_videos/{safe_title}.mp4"

video.download(filename=filename)

# Get the transcript
video_id = yt.video_id
transcript = YouTubeTranscriptApi.get_transcript(video_id)
print(transcript)

# Initialize the Gemini model
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# Build prompt for LLM
prompt = f"""Provided to you is a transcript of a video. 
Please identify all segments that can be extracted as 
subtopics from the video based on the transcript.
Make sure each segment is between 30-500 seconds in duration.
Make sure you provide extremely accurate timestamps
and respond only in the format provided. 
\n Here is the transcription : \n {transcript}"""

# Generate text with the Gemini model
response = model.generate_content(prompt)
print("API Response:")
print(response.text)  # Print the response to check its content


