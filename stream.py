import os
import random
import subprocess
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# 1. Connect to YouTube API
def get_yt_service():
    creds = Credentials(
        None,
        refresh_token=os.getenv('YT_REFRESH_TOKEN'),
        client_id=os.getenv('YT_CLIENT_ID'),
        client_secret=os.getenv('YT_CLIENT_SECRET'),
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('youtube', 'v3', credentials=creds)

# 2. Update Live Stream Title (Algorithm Boost)
def update_metadata(youtube):
    titles = ["BEST OF SHORTS 2026", "Viral Shorts Marathon", "Daily Fun Loop", "Non-Stop Entertainment"]
    new_title = f"{random.choice(titles)} | Loop {random.randint(1, 99)}"
    try:
        request = youtube.liveBroadcasts().list(part="id", broadcastStatus="active")
        response = request.execute()
        if response['items']:
            b_id = response['items'][0]['id']
            youtube.liveBroadcasts().update(
                part="snippet",
                body={"id": b_id, "snippet": {"title": new_title}}
            ).execute()
    except:
        pass # If stream isn't active yet, skip metadata update

# 3. The Main Stream Loop
def run_stream():
    stream_key = os.getenv('YT_STREAM_KEY')
    
    # Get the list of videos from Dropbox once at the start
    print("Fetching video list from Dropbox...")
    video_list = subprocess.check_output("rclone lsf db:Shorts", shell=True).decode().splitlines()
    
    # This loop runs forever until GitHub kills the process at 5 hours
    while True:
        random.shuffle(video_list)
        for video in video_list:
            if not video.strip(): continue
            
            print(f"Now Streaming: {video}")
            # Get a temporary direct link from Dropbox
            raw_url = subprocess.check_output(f'rclone link "db:Shorts/{video}"', shell=True).decode().strip()
            video_url = raw_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
            
            # FFmpeg Command - Optimized for YouTube Live
            cmd = [
                'ffmpeg', '-re', '-i', video_url,
                '-c:v', 'libx264', '-preset', 'veryfast', '-b:v', '3000k', 
                '-maxrate', '3000k', '-bufsize', '6000k', '-g', '60',
                '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
                '-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
            ]
            
            subprocess.run(cmd)
            time.sleep(1) # Short pause between videos

if __name__ == "__main__":
    try:
        yt = get_yt_service()
        update_metadata(yt)
    except:
        print("API Metadata update failed, proceeding to stream anyway.")
    
    run_stream()
