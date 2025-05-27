# app.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# 1. Define where your video files live on disk.
VIDEO_DIR = Path(__file__).parent / "videos"

@app.get("/videos/{video_name}")
async def serve_video(video_name: str):
    """
    Serves any file named `video_name` from the ./videos/ directory.
    Discord will see the returned Content-Type (e.g. video/mp4)
    and embed it when you point an Embed at this URL.
    """
    file_path = VIDEO_DIR / video_name

    # Make sure the file actually exists and is a video
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    # Rely on FileResponse to guess the correct media_type (e.g. video/mp4)
    return FileResponse(file_path)

@app.get("/embed/video/{video_name}")
async def get_video_embed_payload(video_name: str):
    """
    Returns a JSON payload (Discord‐style embed) pointing at the video URL.
    If your bot does a GET to /embed/video/{video_name}, it can then relay
    that JSON embed object to Discord’s API in one step.

    Example response:
    {
        "embed": {
            "title": "My Cool Clip",
            "description": "Here’s a video for you!",
            "url": "https://<your-domain>/videos/myclip.mp4",
            "video": {
                "url": "https://<your-domain>/videos/myclip.mp4"
            }
        }
    }
    """
    file_path = VIDEO_DIR / video_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    # Build the public URL. In production, you’d replace this with your real domain.
    base = "https://your-domain.com"   # ← Change to your actual HTTPS domain
    video_url = f"{base}/videos/{video_name}"

    embed_payload = {
        "embed": {
            "title": f"📹 {video_name}",
            "description": f"Streaming **{video_name}** now!",
            "url": video_url,
            # Including a `video` field is optional; Discord auto‐embeds known video types.
            "video": {
                "url": video_url
            }
        }
    }
    return embed_payload
