import os, random, subprocess, time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# --- CONFIGURATION ---
STREAM_DURATION = 18000  # 5 Hours (in seconds)
BITRATE = "2000k"        # Optimized for Dropbox safety
BUFSIZE = "4000k"        # Smooth buffer

# --- 1. METADATA SETS (The Algorithm Fuel) ---
METADATA_OPTIONS = [
    {"title": "Non-Stop Funny Shorts 2026 😂 (Try Not To Laugh)", "desc": "The best viral funny shorts of the year! Subscribe for daily laughs. #shorts #funny #viral"},
    {"title": "Most Satisfying & Relaxing Loop 🍃 (24/7 Live)", "desc": "Relax with the most satisfying video loop. Perfect for chilling. #satisfying #relaxing #shorts"},
    {"title": "Ultimate Drone Fails & Wins 🚁 (Viral Moments)", "desc": "Crazy drone shots and funny fails caught on camera. #drone #fails #viral"},
    {"title": "Best of Internet: Viral Clips Marathon 🔥", "desc": "Watching the most viewed videos on the internet right now. #trending #shortsfeed"},
    {"title": "Comedy Gold: 5 Hours of Laughs 😆", "desc": "You will laugh! Best comedy skits and bloopers. #comedy #humor #shorts"},
    {"title": "Respect Moments & Wholesome Shorts ❤️", "desc": "Restoring faith in humanity with these wholesome clips. #respect #wholesome"},
    {"title": "Impossible Camera Shots 📸 (Must See)", "desc": "How did they film this? insane camera angles and skills. #photography #viral"},
    {"title": "Cats, Dogs & Funny Animals 🐶 (Cute Overload)", "desc": "The funniest animal videos to brighten your day. #cats #dogs #funnyanimals"},
    {"title": "Legendary Shorts Loop 🏆 (High Quality)", "desc": "High definition viral shorts loop for your entertainment. #hd #shorts"},
    {"title": "Daily Dose of Internet 💊 (Live Stream)", "desc": "Your daily fix of the best short videos online. Don't forget to like! #dailydose"}
]

# --- 2. CHAT SCENARIOS (The Auto-Chatter) ---
# Each set has 2 messages to look like a real conversation starter
CHAT_PAIRS = [
    ["Who is watching right now?", "Say 'Hi' if you are here! 👋"],
    ["Wait for the ending of this one...", "I did not expect that! 😂"],
    ["We are so close to our sub goal!", "Hit that Subscribe button to help us out! 🚀"],
    ["Rate this video 1-10", "I give it a solid 9! What about you?"],
    ["Where are you guys watching from?", "Rep your country in the chat! 🌍"]
]

def get_yt_service():
    try:
        creds = Credentials(
            None,
            refresh_token=os.getenv('YT_REFRESH_TOKEN'),
            client_id=os.getenv('YT_CLIENT_ID'),
            client_secret=os.getenv('YT_CLIENT_SECRET'),
            token_uri="https://oauth2.googleapis.com/token"
        )
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Login Error: {e}")
        return None

def update_metadata_and_thumbnail(youtube, video_id):
    # 1. Pick Random Metadata
    data = random.choice(METADATA_OPTIONS)
    final_title = f"{data['title']} (#{random.randint(100, 999)})"
    
    try:
        # Update Title & Description
        youtube.liveBroadcasts().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": final_title,
                    "description": data['desc'],
                    "scheduledStartTime": time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
                }
            }
        ).execute()
        print(f"✅ Metadata Updated: {final_title}")

        # 2. Update Thumbnail (If files exist in 'thumbs' folder)
        # To use this: Create a folder named 'thumbs' in your repo and put jpg files there.
        if os.path.exists("thumbs"):
            thumb_files = [f for f in os.listdir("thumbs") if f.endswith(('.jpg', '.png'))]
            if thumb_files:
                selected_thumb = random.choice(thumb_files)
                print(f"Uploading Thumbnail: {selected_thumb}")
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(f"thumbs/{selected_thumb}")
                ).execute()
    except Exception as e:
        print(f"⚠️ Metadata/Thumbnail Update Failed: {e}")

def send_chat_pair(youtube, chat_id):
    pair = random.choice(CHAT_PAIRS)
    try:
        for msg in pair:
            youtube.liveChatMessages().insert(
                part="snippet",
                body={
                    "snippet": {
                        "liveChatId": chat_id,
                        "type": "textMessageEvent",
                        "textMessageDetails": {"messageText": msg}
                    }
                }
            ).execute()
            print(f"💬 Bot Sent: {msg}")
            time.sleep(2) # Wait 2 seconds between messages for realism
    except Exception as e:
        print(f"⚠️ Chat Error: {e}")

def run_stream():
    stream_key = os.getenv('YT_STREAM_KEY')
    youtube = get_yt_service()
    
    # --- SETUP PHASE ---
    live_chat_id = None
    if youtube:
        try:
            # Get current broadcast ID
            request = youtube.liveBroadcasts().list(part="id,snippet", broadcastStatus="active")
            response = request.execute()
            if response['items']:
                video_id = response['items'][0]['id']
                live_chat_id = response['items'][0]['snippet']['liveChatId']
                
                # Update Title/Thumbnail immediately
                update_metadata_and_thumbnail(youtube, video_id)
        except Exception as e:
            print(f"Setup Error: {e}")

    # --- STREAM LOOP ---
    start_time = time.time()
    last_chat_time = time.time()
    chat_interval = random.randint(1800, 2700) # Randomly between 30-45 mins

    print("🚀 Streaming Engine Started...")

    while (time.time() - start_time) < STREAM_DURATION:
        try:
            # Fetch Videos
            video_list = subprocess.check_output("rclone lsf db:Shorts", shell=True).decode().splitlines()
            random.shuffle(video_list)

            for video in video_list:
                # 1. Check Time Limit
                if (time.time() - start_time) > STREAM_DURATION:
                    print("🛑 5-Hour Limit Reached. Shutting down.")
                    return

                if not video.strip() or not video.endswith('.mp4'): continue

                # 2. Check Auto-Chatter
                if youtube and live_chat_id and (time.time() - last_chat_time) > chat_interval:
                    send_chat_pair(youtube, live_chat_id)
                    last_chat_time = time.time()
                    chat_interval = random.randint(1800, 2700) # Reset timer to new random

                # 3. Get Link & Stream
                try:
                    raw_url = subprocess.check_output(f'rclone link "db:Shorts/{video}"', shell=True).decode().strip()
                    video_url = raw_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
                    
                    print(f"▶️ Now Playing: {video}")
                    
                    cmd = [
                        'ffmpeg', '-re', '-i', video_url,
                        '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', 
                        '-b:v', BITRATE, '-maxrate', BITRATE, '-bufsize', BUFSIZE, '-g', '60',
                        '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
                        '-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
                    ]
                    subprocess.run(cmd) # This waits until video finishes
                    
                except Exception as e:
                    print(f"⚠️ Video Error: {e}. Retrying...")
                    time.sleep(5)

        except Exception as e:
            print(f"⚠️ Global Loop Error: {e}. Restarting...")
            time.sleep(10)

if __name__ == "__main__":
    run_stream()
