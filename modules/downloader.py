import subprocess
import os

YTDLP_PATH = os.path.join(os.getcwd(), "lib", "yt-dlp.exe")
DOWNLOAD_DIR = os.path.join(os.getcwd(), "download")

def download_media(url, format_type='mp4'):
    """
    Downloads media from URL in specified format.
    format_type: mp4, m4a, mp3, wav
    """
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        
    output_template = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    
    cmd = [YTDLP_PATH, "-o", output_template]
    
    if format_type == 'mp3':
        cmd += ["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0"]
    elif format_type == 'm4a':
        cmd += ["-f", "bestaudio[ext=m4a]"]
    elif format_type == 'wav':
        cmd += ["-f", "bestaudio", "--extract-audio", "--audio-format", "wav"]
    elif format_type == 'mp4':
        cmd += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
    
    # Add ffmpeg path from lib folder
    cmd += ["--ffmpeg-location", os.path.join(os.getcwd(), "lib")]
    cmd += [url]
    
    try:
        # Run in background or wait? For downloader, usually we want to see progress or run in thread.
        # For now, let's just run it.
        subprocess.Popen(cmd)
        print(f"Started downloading {url} as {format_type}")
    except Exception as e:
        print(f"Error starting download: {e}")

if __name__ == "__main__":
    # Test download
    # download_media("https://www.youtube.com/watch?v=aqvZeN-r_t4", "mp3")
    pass
