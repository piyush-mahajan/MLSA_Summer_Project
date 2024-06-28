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

# Check if the response contains valid JSON
try:
    parsed_content = json.loads(response.text)
except json.JSONDecodeError as e:
    print("Failed to parse JSON response:")
    print(response.text)
    raise e

# Check if the parsed content contains the expected 'segments' key
if 'segments' not in parsed_content:
    raise ValueError("The response JSON does not contain 'segments' key")

# Create a folder to store clips
os.makedirs("generated_clips", exist_ok=True)
segment_labels = []
video_title = safe_title

for i, segment in enumerate(parsed_content['segments']):
    start_time = segment['start_time']
    end_time = segment['end_time']
    yt_title = segment['yt_title']
    description = segment['description']
    duration = segment['duration']

    output_file = f"generated_clips/{video_title}_{str(i+1)}.mp4"
    command = f"ffmpeg -i {filename} -ss {start_time} -to {end_time} -c:v libx264 -c:a aac -strict experimental -b:a 192k {output_file}"
    subprocess.call(command, shell=True)
    segment_labels.append(f"Sub-Topic {i+1}: {yt_title}, Duration: {duration}s\nDescription: {description}\n")

with open('generated_clips/segment_labels.txt', 'w') as f:
    for label in segment_labels:
        f.write(label + "\n")

# Save the segments to a JSON file
with open('generated_clips/segments.json', 'w') as f:
    json.dump(parsed_content['segments'], f, indent=4)
