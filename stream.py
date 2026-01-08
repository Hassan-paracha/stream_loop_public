import os, random, subprocess, time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# --- CONFIGURATION ---
STREAM_DURATION = 18000  # 5 Hours
BITRATE = "2000k"
BUFSIZE = "4000k"

# --- 1. OPTIMIZED METADATA SETS ---
METADATA_OPTIONS = [
    {"title": "😂 UNREAL Funny Moments #shorts #viral", "desc": "Can you handle these funniest moments? 🤣 #funny #comedy #shorts #viral"},
    {"title": "🚀 BEST Drone Views & Fails #shorts #drone", "desc": "Insane drone camera shots! 🚁 #drone #aerial #amazing #viralshorts"},
    {"title": "🍃 ODDLY Satisfying Loop (24/7) #satisfying", "desc": "The most relaxing video ever made. 🧘‍♂️ #satisfying #relax #asmr #loop"},
    {"title": "🤯 TRY NOT TO LAUGH! (Impossible) #funny", "desc": "Level: Extreme. Don't laugh! 🔥 #challenge #funnyvideo #humor #shorts"},
    {"title": "🔥 MOST VIEWED Shorts 2026 #trending", "desc": "Watching the internet's favorite viral videos. 💎 #trending #viral #shorts"},
    {"title": "🎖️ RESPECT Moments & Wins #respect #shorts", "desc": "Faith in humanity restored. ❤️ #respect #wholesome #humanity #viral"},
    {"title": "🐱 FUNNY Animals being Humans #pets #shorts", "desc": "Hilarious animal clips to melt your heart. 🐶 #animals #cats #dogs #funny"},
    {"title": "🤳 SECRETS Caught on Camera #viral #shorts", "desc": "You won't believe what happened... 😱 #mystery #caughtoncamera #trending"},
    {"title": "📸 IMPOSSIBLE Camera Angles #photography", "desc": "How did they even film this? 🎥 #camera #skills #photography #viral"},
    {"title": "🏆 BEST OF THE WEEK: Viral Loop #shorts", "desc": "Top trending videos in one non-stop stream. 🌟 #best #trending #shortsfeed"}
]

# --- 2. CHAT SCENARIOS (Auto-Chatter) ---
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
    data = random.choice(METADATA_OPTIONS)
    final_title = f"{data['title']} (#{random.randint(100, 999)})"
    try:
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
            time.sleep(2)
    except Exception as e:
        print(f"⚠️ Chat Error: {e}")

def run_stream():
    stream_key = os.getenv('YT_STREAM_KEY')
    youtube = get_yt_service()
    live_chat_id = None

    if youtube:
        try:
            request = youtube.liveBroadcasts().list(part="id,snippet", broadcastStatus="active")
            response = request.execute()
            if response['items']:
                video_id = response['items'][0]['id']
                live_chat_id = response['items'][0]['snippet']['liveChatId']
                update_metadata_and_thumbnail(youtube, video_id)
        except Exception as e:
            print(f"Setup Error: {e}")

    start_time = time.time()
    last_chat_time = time.time()
    chat_interval = random.randint(1800, 2700)

    print("🚀 Streaming Engine Started...")

    while (time.time() - start_time) < STREAM_DURATION:
        try:
            # 1. Fetch Videos from Rclone
            result = subprocess.check_output("rclone lsf db:Shorts", shell=True).decode().splitlines()
            video_list = [v for v in result if v.strip() and v.endswith('.mp4')]
            random.shuffle(video_list)

            if not video_list:
                print("❌ No videos found in Dropbox/Shorts folder!")
                time.sleep(60)
                continue

            for video in video_list:
                if (time.time() - start_time) > STREAM_DURATION: 
                    return

                # 2. Check Auto-Chatter
                if youtube and live_chat_id and (time.time() - last_chat_time) > chat_interval:
                    send_chat_pair(youtube, live_chat_id)
                    last_chat_time = time.time()
                    chat_interval = random.randint(1800, 2700)

                # 3. Get Link and FORCE Direct Download Format
                try:
                    raw_url = subprocess.check_output(f'rclone link "db:Shorts/{video}"', shell=True).decode().strip()
                    
                    # Clean and rebuild the URL to avoid 404 errors
                    video_url = raw_url.replace("www.dropbox.com", "dl.dropboxusercontent.com")
                    video_url = video_url.replace("?dl=0", "").replace("&dl=0", "").replace("?dl=1", "").replace("&dl=1", "")
                    
                    if "?" in video_url:
                        video_url += "&dl=1"
                    else:
                        video_url += "?dl=1"
                    
                    print(f"▶️ Now Playing: {video}")

                    # 4. Launch FFmpeg
                    cmd = [
                        'ffmpeg', '-re', 
                        '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5',
                        '-i', video_url,
                        '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', 
                        '-b:v', BITRATE, '-maxrate', BITRATE, '-bufsize', BUFSIZE, '-g', '60',
                        '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
                        '-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
                    ]
                    subprocess.run(cmd, check=True)
                    
                except Exception as e:
                    print(f"⚠️ Video Playback Error: {e}")
                    time.sleep(5)

        except Exception as e:
            print(f"⚠️ Global Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_stream()
