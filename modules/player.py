import subprocess
import os

FFPLAY_PATH = os.path.join(os.getcwd(), "lib", "ffplay.exe")
YTDLP_PATH = os.path.join(os.getcwd(), "lib", "yt-dlp.exe")

def play_video(url):
    """
    Plays a YouTube video URL using ffplay and yt-dlp.
    """
    # Use yt-dlp to get the stream URL and pipe it to ffplay
    # Actually, ffplay can take the stream URL directly if we get it from ytdlp
    # Or we can just let ffplay handle it if it has gnutls/openssl, 
    # but the usual way with ytdlp is to get the best format URL.
    
    # Simpler: yt-dlp -g <url> gets the stream URL
    try:
        cmd_get_url = [YTDLP_PATH, "-g", "-f", "best", url]
        stream_url = subprocess.check_output(cmd_get_url, text=True, encoding='utf-8', errors='replace').strip()
        
        # Now play with ffplay
        # -nodisp if we wanted audio only, but ffplay by default shows video if available.
        # User said "play", so we use ffplay.
        subprocess.Popen([FFPLAY_PATH, "-autoexit", stream_url])
    except Exception as e:
        print(f"Error playing video: {e}")

if __name__ == "__main__":
    # Test play (requires a valid URL)
    # play_video("https://www.youtube.com/watch?v=aqvZeN-r_t4")
    pass
