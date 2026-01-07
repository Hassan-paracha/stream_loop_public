import os, random, subprocess, time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def get_yt_service():
    creds = Credentials(
        None,
        refresh_token=os.getenv('YT_REFRESH_TOKEN'),
        client_id=os.getenv('YT_CLIENT_ID'),
        client_secret=os.getenv('YT_CLIENT_SECRET'),
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('youtube', 'v3', credentials=creds)

def update_metadata(youtube):
    # Dynamic Titles to avoid Shadowban
    titles = [
        "BEST Funny Shorts 2026 😂",
        "Non-Stop Entertainment Marathon 🚀",
        "Most Viral Shorts of the Week 🔥",
        "Ultimate Comedy Loop | 24/7 Live",
        "Don't Blink! Best Shorts Collection 💎"
    ]
    
    # Dynamic Descriptions
    descriptions = [
        "Welcome to the marathon! Subscribe for daily laughs.",
        "Streaming the best viral content. Check out our latest uploads!",
        "The #1 place for funny shorts. Support us by hitting Like!",
        "Looping the most liked videos from our channel."
    ]

    new_title = f"{random.choice(titles)} (#{random.randint(100, 999)})"
    new_desc = f"{random.choice(descriptions)}\n\nSupport the stream by subscribing!"

    try:
        request = youtube.liveBroadcasts().list(part="id,snippet", broadcastStatus="active")
        response = request.execute()
        if response['items']:
            b_id = response['items'][0]['id']
            # Update Title and Description
            youtube.liveBroadcasts().update(
                part="snippet",
                body={
                    "id": b_id,
                    "snippet": {
                        "title": new_title,
                        "description": new_desc,
                        "scheduledStartTime": response['items'][0]['snippet']['scheduledStartTime']
                    }
                }
            ).execute()
            print(f"Metadata Updated: {new_title}")
    except Exception as e:
        print(f"Metadata Update Skipped: {e}")

def run_stream():
    stream_key = os.getenv('YT_STREAM_KEY')
    print("Fetching video list from Dropbox...")
    video_list = subprocess.check_output("rclone lsf db:Shorts", shell=True).decode().splitlines()
    
    while True:
        random.shuffle(video_list)
        for video in video_list:
            if not video.strip(): continue
            
            raw_url = subprocess.check_output(f'rclone link "db:Shorts/{video}"', shell=True).decode().strip()
            # Fix Dropbox Link for direct play
            video_url = raw_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
            
            print(f"Now Streaming: {video}")
            # BITRATE REDUCED TO 2000k FOR DATA SAVING & NO LAG
            cmd = [
                'ffmpeg', '-re', '-i', video_url,
                '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', 
                '-b:v', '2000k', '-maxrate', '2000k', '-bufsize', '4000k', '-g', '60',
                '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
                '-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
            ]
            subprocess.run(cmd)
            time.sleep(1)

if __name__ == "__main__":
    yt_service = None
    try:
        yt_service = get_yt_service()
    except:
        print("YouTube Service initialization failed.")
        
    # Start Metadata update in background if possible, then stream
    if yt_service:
        # We wait 30 seconds to update metadata so the stream has time to connect
        time.sleep(30)
        update_metadata(yt_service)
    
    run_stream()
