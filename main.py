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
    "funny_shorts_hd",
    "humor_memes",
    "laughing_videos",
    "short_funny_clips",
    "fun_zone_memes",
    "memes_comedy",
    "funny1",
    "funny_humors",
    "DesiMemesOfficial"
]

OUTPUT_VIDEO = "single_viral_short.mp4"
RAW_FILE = "raw_single.mp4"
HISTORY_FILE = "uploaded_urls.txt"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_uploaded_history():
    """History file se bina token wale clean URLs load karta hai"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return set(line.strip().split('?')[0] for line in f if line.strip())
    return set()


def save_to_history(video_url):
    """Token ke bina clean URL ko history file me save karta hai"""
    clean_url = video_url.split('?')[0]
    with open(HISTORY_FILE, "a") as f:
        f.write(clean_url + "\n")


def has_audio(input_file):
    """FFprobe ka use karke check karta hai ki video file me audio stream hai ya nahi"""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return "audio" in result.stdout


def process_to_916_fast(input_file, output_file):
    """Sirf tabhi process karega jab video me sound/audio hoga, aur size compress karega taaki 413 error na aaye"""
    
    # Pehle check karein ki downloaded raw video me audio hai ya nahi
    if not has_audio(input_file):
        print("🔇 Is video me sound/audio nahi hai, isliye ise skip kiya ja raha hai.")
        return False

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",  # Size chhota rakhne ke liye compression
        "-c:a", "aac",
        "-b:a", "128k",
        output_file
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print("❌ FFmpeg processing error aayi.")
        return False
        
    return True


def get_telegram_funny_video():
    """Telegram web preview se unseen/fresh video URL scrape karta hai"""
    history = get_uploaded_history()
    channels = TELEGRAM_CHANNELS.copy()
    random.shuffle(channels)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for channel in channels:
        offset = random.choice([0, 20, 50, 100, 150, 200])
        url = f"https://t.me/s/{channel}?before={offset}" if offset > 0 else f"https://t.me/s/{channel}"

        print(f"🔍 Searching @{channel} (offset: {offset})...")
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                video_tags = soup.find_all('video')

                video_urls = []
                for v in video_tags:
                    src = v.get('src')
                    if src:
                        clean_url = src.split('?')[0]
                        if clean_url not in history:
                            video_urls.append(src)

                if video_urls:
                    selected_url = random.choice(video_urls)
                    print(f"✅ Fresh Video mil gayi (@{channel}): {selected_url.split('?')[0]}...")
                    return selected_url
                else:
                    print(f"⚠️ Channel @{channel} par koi unseen video nahi mili.")
        except Exception as e:
            print(f"⚠️ Channel @{channel} scrape karne me error: {e}")
            continue

    print("⚠️ Sabhi channels ki videos duplicate hain ya nahi mili.")
    return None


def send_video_to_telegram(video_path):
    """Processed video ko Telegram Bot API se send karta hai"""
    if not BOT_TOKEN or not TARGET_CHAT_ID:
        print("❌ Error: TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID missing hai!")
        return False

    print("📤 Telegram channel par upload ho raha hai...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    caption_text = "🔥 New Viral Short!\n\n#shorts #viral #trending #funny #memes"

    try:
        with open(video_path, 'rb') as video_file:
            payload = {'chat_id': TARGET_CHAT_ID, 'caption': caption_text}
            files = {'video': video_file}
            res = requests.post(url, data=payload, files=files, timeout=60)

        if res.status_code == 200:
            print("✅ Telegram par successfully upload ho gaya!")
            return True
        else:
            print(f"❌ Upload failed (Status Code {res.status_code}): {res.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram upload me exception aaya: {e}")
        return False


def main():
    video_url = get_telegram_funny_video()

    if not video_url:
        print("⏭️ Upload skipped: Koi nayi video available nahi thi.")
        return

    print("⬇️ Video download ho rahi hai...")
    try:
        r = requests.get(video_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
        if r.status_code == 200:
            with open(RAW_FILE, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(RAW_FILE) and os.path.getsize(RAW_FILE) > 0:
                print("⚡ Sound check aur 9:16 vertical video conversion ho raha hai...")
                success = process_to_916_fast(RAW_FILE, OUTPUT_VIDEO)

                if success and os.path.exists(OUTPUT_VIDEO):
                    uploaded = send_video_to_telegram(OUTPUT_VIDEO)
                    if uploaded:
                        save_to_history(video_url)
                else:
                    print("❌ Video me sound nahi tha ya FFmpeg processing fail ho gayi, isliye skip kar diya gaya.")
                    # Chahe sound na ho, par URL ko history me daal dein taaki script baar-baar usi be-awaaz video par na atke
                    save_to_history(video_url)
            else:
                print("❌ Downloaded file empty hai.")
        else:
            print(f"❌ Download failed (HTTP Status: {r.status_code})")

    except Exception as e:
        print(f"❌ Error aaya: {e}")
    finally:
        if os.path.exists(OUTPUT_VIDEO):
            os.path.exists(OUTPUT_VIDEO) and os.remove(OUTPUT_VIDEO)
        if os.path.exists(RAW_FILE):
            os.path.exists(RAW_FILE) and os.remove(RAW_FILE)


if __name__ == "__main__":
    main()
