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

# GitHub Environment Variables se secrets milenge
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def process_to_916_fast(input_file, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "copy",
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def get_telegram_funny_video():
    channels = TELEGRAM_CHANNELS.copy()
    random.shuffle(channels)
    headers = {'User-Agent': 'Mozilla/5.0'}

    for channel in channels:
        url = f"https://t.me/s/{channel}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            video_tags = soup.find_all('video')
            video_urls = [v.get('src') for v in video_tags if v.get('src')]

            if video_urls:
                return random.choice(video_urls)
        except Exception:
            continue
    return None

def send_video_to_telegram(video_path):
    """Processed video ko aapke Telegram channel me upload karta hai"""
    print("📤 Telegram channel par upload ho raha hai...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    
    with open(video_path, 'rb') as video_file:
        payload = {'chat_id': TARGET_CHAT_ID, 'caption': '🔥 New Viral Short!'}
        files = {'video': video_file}
        res = requests.post(url, data=payload, files=files)
        
    if res.status_code == 200:
        print("✅ Telegram par successfully upload ho gaya!")
    else:
        print(f"❌ Upload failed: {res.text}")

def main():
    video_url = get_telegram_funny_video()
    if not video_url:
        video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"

    print("⬇️ Video download ho rahi hai...")
    r = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
    if r.status_code == 200:
        with open(RAW_FILE, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)

        if os.path.exists(RAW_FILE) and os.path.getsize(RAW_FILE) > 0:
            print("⚡ 9:16 vertical video me convert ho raha hai...")
            process_to_916_fast(RAW_FILE, OUTPUT_VIDEO)
            
            if os.path.exists(OUTPUT_VIDEO):
                send_video_to_telegram(OUTPUT_VIDEO)
                os.remove(OUTPUT_VIDEO)
            
            if os.path.exists(RAW_FILE):
                os.remove(RAW_FILE)

if __name__ == "__main__":
    main()

