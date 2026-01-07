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
    titles = ["BEST Funny Shorts 2026 😂", "Viral Shorts Marathon 🚀", "Ultimate Comedy Loop 🔥"]
    new_title = f"{random.choice(titles)} (#{random.randint(100, 999)})"
    try:
        request = youtube.liveBroadcasts().list(part="id,snippet", broadcastStatus="active")
        response = request.execute()
        if response['items']:
            b_id = response['items'][0]['id']
            youtube.liveBroadcasts().update(
                part="snippet",
                body={"id": b_id, "snippet": {"title": new_title, "description": "Enjoy the marathon! Subscribe for more!", "scheduledStartTime": response['items'][0]['snippet']['scheduledStartTime']}}
            ).execute()
            print(f"Title Updated: {new_title}")
    except Exception as e:
        print(f"Metadata Update Skipped: {e}")

def run_stream():
    stream_key = os.getenv('YT_STREAM_KEY')
    start_time = time.time()
    duration_limit = 18000 # 5 Hours exactly
    
    print("Stream Engine Started...")
    
    # Outer Loop: Keep trying until the 5-hour limit is reached
    while (time.time() - start_time) < duration_limit:
        try:
            video_list = subprocess.check_output("rclone lsf db:Shorts", shell=True).decode().splitlines()
            random.shuffle(video_list)

            for video in video_list:
                # Break if 5 hours are up
                if (time.time() - start_time) > duration_limit:
                    break
                
                if not video.strip() or not video.endswith('.mp4'): continue
                
                # Fetch Link with Retry
                try:
                    raw_url = subprocess.check_output(f'rclone link "db:Shorts/{video}"', shell=True).decode().strip()
                    video_url = raw_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
                except:
                    print(f"Failed to get link for {video}, skipping...")
                    continue

                print(f"Now Streaming: {video}")
                
                # FFmpeg with Optimized Settings
                cmd = [
                    'ffmpeg', '-re', '-i', video_url,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', 
                    '-b:v', '2000k', '-maxrate', '2000k', '-bufsize', '4000k', '-g', '60',
                    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
                    '-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
                ]
                
                # Run video and check if it crashed
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    print("Video connection lost. Retrying next video...")
                    time.sleep(2)
                    
        except Exception as e:
            print(f"System Error: {e}. Cooling down for 10s...")
            time.sleep(10)

if __name__ == "__main__":
    # Try metadata update after 30 seconds of streaming
    try:
        service = get_yt_service()
        # In a real environment, you'd run this in a thread, 
        # but for simplicity, we'll just stream.
    except:
        print("YouTube API not available.")
    
    run_stream()
