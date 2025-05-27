from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from typing import Optional
from pathlib import Path
import shutil

app = FastAPI()

# Directory where videos are stored
VIDEO_DIR = Path(__file__).parent / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

# ─── Upload Endpoint ───────────────────────────────────────────────────────────
@app.post("/videos/", status_code=200)
async def upload_video(file: UploadFile = File(...)):
    """
    Accepts a video file upload (multipart/form-data) and saves it under ./videos.
    """
    destination = VIDEO_DIR / file.filename

    # You may add checks for file extension or size limits here.
    with destination.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    return {"detail": f"Uploaded as {file.filename}"}

# ─── Serve Video Endpoint ──────────────────────────────────────────────────────
@app.get("/videos/{video_name}")
async def serve_video(video_name: str):
    """
    Serves a video file from the ./videos directory.
    Discord will embed it based on Content-Type (e.g. video/mp4).
    """
    file_path = VIDEO_DIR / video_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(file_path)

# ─── Embed Payload Endpoint ────────────────────────────────────────────────────
@app.get("/embed/video/{video_name}")
async def get_video_embed_payload(
    video_name: str,
    title: Optional[str] = Query(
        None,
        description="Custom embed title. Defaults to '📹 {video_name}'."
    ),
    description: Optional[str] = Query(
        None,
        description="Custom embed description. Defaults to 'Streaming **{video_name}** now!'."
    ),
    thumbnail_url: Optional[str] = Query(
        None,
        description="URL of a custom thumbnail image."
    ),
    color: Optional[int] = Query(
        None,
        description="Integer color code for Discord embed (e.g. 0xFF00FF)."
    ),
):
    """
    Returns a JSON payload containing a Discord-style embed for the video.
    """
    file_path = VIDEO_DIR / video_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    # Base URL of your deployed FastAPI
    BASE_URL = "https://tragic-embed.onrender.com"
    video_url = f"{BASE_URL}/videos/{video_name}"

    # Default embed fields
    default_title = f"📹 {video_name}"
    default_desc = f"Streaming **{video_name}** now!"

    embed = {
        "title": title.strip() if title else default_title,
        "description": description.strip() if description else default_desc,
        "url": video_url,
        "video": {"url": video_url},
    }

    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url.strip()}
    if color is not None:
        embed["color"] = color

    return {"embed": embed}
