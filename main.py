import os
import random
import requests
import subprocess
from bs4 import BeautifulSoup

TELEGRAM_CHANNELS = [
    "Funcology",
    "funny_videos_memes",
    "Funny_Videos_Gifs",
    "memes",
    "viral_videos_channel",
    "funny_shorts_hd"
]

OUTPUT_VIDEO = "single_viral_short.mp4"
RAW_FILE = "raw_single.mp4"

# GitHub Environment Variables se secrets fetch karna
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def process_to_916_fast(input_file, output_file):
    """FFmpeg ka use karke video ko 9:16 vertical format me convert karta hai"""
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
        output_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0

def get_telegram_funny_video():
    """Telegram web preview se video URL scrape karta hai"""
    channels = TELEGRAM_CHANNELS.copy()
    random.shuffle(channels)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for channel in channels:
        url = f"https://t.me/s/{channel}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                video_tags = soup.find_all('video')
                video_urls = [v.get('src') for v in video_tags if v.get('src')]

                if video_urls:
                    selected_url = random.choice(video_urls)
                    print(f"✅ Video mil gayi: {channel}")
                    return selected_url
        except Exception as e:
            print(f"⚠️ Channel {channel} scrape karne me error: {e}")
            continue
            
    print("⚠️ Kisi bhi channel se video nahi mili, fallback URL apply ho raha hai.")
    return None

def send_video_to_telegram(video_path):
    """Processed video ko Telegram Bot API se channel me send karta hai"""
    if not BOT_TOKEN or not TARGET_CHAT_ID:
        print("❌ Error: TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID env variables miss hain!")
        return

    print("📤 Telegram channel par upload ho raha hai...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    
    try:
        with open(video_path, 'rb') as video_file:
            payload = {'chat_id': TARGET_CHAT_ID, 'caption': '🔥 New Viral Short!'}
            files = {'video': video_file}
            res = requests.post(url, data=payload, files=files, timeout=60)
            
        if res.status_code == 200:
            print("✅ Telegram par successfully upload ho gaya!")
        else:
            print(f"❌ Upload failed (Status Code {res.status_code}): {res.text}")
    except Exception as e:
        print(f"❌ Telegram upload me exception aaya: {e}")

def main():
    video_url = get_telegram_funny_video()
    if not video_url:
        video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

    print("⬇️ Video download ho rahi hai...")
    try:
        r = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
        if r.status_code == 200:
            with open(RAW_FILE, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(RAW_FILE) and os.path.getsize(RAW_FILE) > 0:
                print("⚡ 9:16 vertical video me convert ho raha hai...")
                success = process_to_916_fast(RAW_FILE, OUTPUT_VIDEO)
                
                if success and os.path.exists(OUTPUT_VIDEO):
                    send_video_to_telegram(OUTPUT_VIDEO)
                else:
                    print("❌ FFmpeg video process karne me fail ho gaya.")

    except Exception as e:
        print(f"❌ Video download/process karne me error aaya: {e}")
    finally:
        # Temporary files clean up karna
        if os.path.exists(OUTPUT_VIDEO):
            os.remove(OUTPUT_VIDEO)
        if os.path.exists(RAW_FILE):
            os.remove(RAW_FILE)

if __name__ == "__main__":
    main()
