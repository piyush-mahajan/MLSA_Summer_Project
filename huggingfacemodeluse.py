import os
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_huggingface import HuggingFaceEndpoint
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
import subprocess
import json
from typing import List
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Set your Hugging Face API token
os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

youtube_url = "https://www.youtube.com/watch?v=PHNJ2_4oefE"
# youtube_url = "https://www.youtube.com/watch?v=4WO5kJChg3w"
os.makedirs("downloaded_videos", exist_ok=True)

# pytube download video part
yt = YouTube(youtube_url)
video = yt.streams.filter(file_extension='mp4').first()
safe_title = yt.title.replace(' ', '_')
filename = f"downloaded_videos/{safe_title}.mp4"
video.download(filename=filename)

# get the transcript
video_id = yt.video_id
transcript = YouTubeTranscriptApi.get_transcript(video_id)

# define the llm
llm = HuggingFaceEndpoint(
    endpoint_url="https://api-inference.huggingface.co/models/facebook/bart-large",
    task="text2text-generation",
    temperature=0.7,
    max_new_tokens=512,
    parameters={"truncation": "only_first"}
)

class Segment(BaseModel):
    """ Represents a segment of a video"""
    start_time: float = Field(..., description="The start time of the segment in seconds")
    end_time: float = Field(..., description="The end time of the segment in seconds")
    yt_title: str = Field(..., description="The youtube title to make this segment as a viral sub-topic")
    description: str = Field(..., description="The detailed youtube description to make this segment viral ")
    duration : int = Field(..., description="The duration of the segment in seconds")

class VideoTranscript(BaseModel):
    """ Represents the transcript of a video with identified viral segments"""
    segments: List[Segment] = Field(..., description="List of viral segments in the video")

# Create output parser
parser = PydanticOutputParser(pydantic_object=VideoTranscript)

def process_chunk(chunk):
    prompt = f"""Provided to you is a part of a transcript of a video. 
    Please identify segments that can be extracted as 
    subtopics from the video based on this part of the transcript.
    Make sure each segment is between 30-500 seconds in duration.
    Make sure you provide extremely accurate timestamps
    and respond only in the format provided. 
    \n Here is the transcription part: \n {chunk}"""

    messages = [
        SystemMessage(content="You are a viral content producer. You are master at reading youtube transcripts and identifying the most intriguing content. You have extraordinary skills to extract subtopics from content. Your subtopics can be repurposed as a separate video."),
        HumanMessage(content=prompt)
    ]

    # Create a chat prompt template
    chat_prompt = ChatPromptTemplate.from_messages(messages)

    # Combine the chat prompt with the output parser
    chain = chat_prompt | llm | parser

    try:
        result = chain.invoke({"chunk": chunk})
        return result.segments
    except Exception as e:
        print(f"An error occurred processing a chunk: {e}")
        return []

# Process transcript in chunks
chunk_size = 1000  # adjust this based on model's input limit
chunks = [transcript[i:i+chunk_size] for i in range(0, len(transcript), chunk_size)]

all_segments = []
for chunk in chunks:
    all_segments.extend(process_chunk(chunk))

# Sort segments by start time
all_segments.sort(key=lambda x: x.start_time)

# Merge overlapping segments
merged_segments = []
for segment in all_segments:
    if not merged_segments or segment.start_time > merged_segments[-1].end_time:
        merged_segments.append(segment)
    else:
        merged_segments[-1].end_time = max(merged_segments[-1].end_time, segment.end_time)
        merged_segments[-1].duration = int(merged_segments[-1].end_time - merged_segments[-1].start_time)

# create a folder to store clips
os.makedirs("generated_clips", exist_ok=True)
segment_labels = []
video_title = safe_title

for i, segment in enumerate(merged_segments):
    start_time = segment.start_time
    end_time = segment.end_time
    yt_title = segment.yt_title
    description = segment.description
    duration = segment.duration
    output_file = f"generated_clips/{video_title}_{str(i+1)}.mp4"
    command = f"ffmpeg -i {filename} -ss {start_time} -to {end_time} -c:v libx264 -c:a aac -strict experimental -b:a 192k {output_file}"
    subprocess.call(command, shell=True)
    segment_labels.append(f"Sub-Topic {i+1}: {yt_title}, Duration: {duration}s\nDescription: {description}\n")

with open('generated_clips/segment_labels.txt', 'w') as f:
    for label in segment_labels:
        f.write(label +"\n")

# save the segments to a json file
with open('generated_clips/segments.json', 'w') as f:
    json.dump([segment.dict() for segment in merged_segments], f, indent=4)