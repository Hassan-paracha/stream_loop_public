import os, random, subprocess, time

# ... (keep your get_yt_service and update_metadata functions the same) ...

def run_stream():
    stream_key = os.getenv('YT_STREAM_KEY')
    start_time = time.time()
    # 5 Hours = 18000 seconds
    duration_limit = 18000 
    
    print(f"Starting 5-hour stream session...")
    
    while (time.time() - start_time) < duration_limit:
        try:
            video_list = subprocess.check_output("rclone lsf db:Shorts", shell=True).decode().splitlines()
            random.shuffle(video_list)

            for video in video_list:
                # Check timer inside the video loop too
                if (time.time() - start_time) > duration_limit:
                    break
                
                if not video.strip(): continue
                
                raw_url = subprocess.check_output(f'rclone link "db:Shorts/{video}"', shell=True).decode().strip()
                video_url = raw_url.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
                
                print(f"Streaming: {video} | Time left: {int((duration_limit - (time.time() - start_time))/60)} mins")
                
                cmd = [
                    'ffmpeg', '-re', '-i', video_url,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-tune', 'zerolatency', 
                    '-b:v', '2000k', '-maxrate', '2000k', '-bufsize', '4000k', '-g', '60',
                    '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
                    '-f', 'flv', f'rtmp://a.rtmp.youtube.com/live2/{stream_key}'
                ]
                
                # If FFmpeg crashes, it will just move to the next video or retry
                subprocess.run(cmd)
                
        except Exception as e:
            print(f"Error: {e}. Retrying in 10 seconds...")
            time.sleep(10)
            
    print("5-hour limit reached. Ending stream to stay safe.")
