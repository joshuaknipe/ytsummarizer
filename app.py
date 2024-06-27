from flask import Flask, request, render_template, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import os
import re

app = Flask(__name__)

# Ensure your OPENAI_API_KEY environment variable is set
client = OpenAI()

@app.route('/')
def index():
    return render_template('index.html')

def get_video_id(video_url):
    # Regular expression to match video IDs from both URL formats
    regex_pattern = r'(?:v=|\.be/)([^&?]+)'
    match = re.search(regex_pattern, video_url)
    if match:
        return match.group(1)
    else:
        return None  # Return None or raise an error if no ID is found
    

# Function to get a combined transcript as a single string with timestamps
def get_combined_transcript_with_timestamps(video_id):
    try:
        # Fetch the transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Initialize an empty list to hold formatted segments
        formatted_segments = []
        
        for entry in transcript:
            # Ensure 'start' and 'text' keys exist in the entry
            if 'start' in entry and 'text' in entry:
                # Calculate HH:MM:SS from 'start'
                hours, remainder = divmod(int(entry['start']), 3600)
                minutes, seconds = divmod(remainder, 60)
                timestamp = f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
                
                # Append formatted segment to the list
                formatted_segments.append(f"{timestamp} {entry['text']}")
                
        # Combine all formatted segments into one string
        combined_transcript = " ".join(formatted_segments)
        
        return combined_transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    video_url = data['video_url']
    video_id = get_video_id(data['video_url'])
    #video_id = video_url.split('v=')[-1]  # Basic extraction, might need improvement based on URL format

    try:
        transcript = get_combined_transcript_with_timestamps(video_id)
        #transcript = ' '.join([i['text'] for i in transcript_list])

        # Create a chat completion request
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following video transcript into between 1 and 3 paragraphs. After that add a new line and then give a bulleted list of key highlights which are timestamped as [mm:ss] : {transcript}"}
            ],
            model="gpt-3.5-turbo-0125",
        )

        summary = response.choices[0].message.content
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

