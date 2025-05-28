from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pathlib import Path
import shutil
import asyncio
import httpx

app = FastAPI()

# Directories
BASE_DIR = Path(__file__).parent
VIDEO_DIR = BASE_DIR / "videos"
TEMPLATES_DIR = BASE_DIR / "templates"
VIDEO_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
SERVICE_URL = "https://tragic-embed.onrender.com/"


# Jinja2 templates setup
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ─── Serve Upload Page ─────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """
    Renders the uploader HTML page.
    """
    return templates.TemplateResponse(
        "uploader.html",
        {"request": request}
    )

@app.on_event("startup")
async def schedule_ping_task():
    async def ping_loop():
        async with httpx.AsyncClient(timeout=5) as client:
            while True:
                try:
                    resp = await client.get(f"{SERVICE_URL}/ping")
                    if resp.status_code != 200:
                        print(f"Health ping returned {resp.status_code}")
                except Exception as e:
                    print(f"External ping failed: {e!r}")
                await asyncio.sleep(120)
    asyncio.create_task(ping_loop())

@app.get("/ping")
async def ping():
    return {"status": "alive"}

# ─── Upload Endpoint ───────────────────────────────────────────────────────────
@app.post("/videos/", status_code=200)
async def upload_video(file: UploadFile = File(...)):
    """
    Accepts a video file upload (multipart/form-data) and saves it under ./videos.
    Returns detail message.
    """
    destination = VIDEO_DIR / file.filename
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
    title: Optional[str] = Query(None, description="Custom embed title. Defaults to '📹 {video_name}'."),
    description: Optional[str] = Query(None, description="Custom embed description. Defaults to 'Streaming **{video_name}** now!'."),
    thumbnail_url: Optional[str] = Query(None, description="URL of a custom thumbnail image."),
    color: Optional[int] = Query(None, description="Integer color code for Discord embed (e.g. 0xFF00FF)."),
):
    """
    Returns a JSON payload containing a Discord-style embed for the video.
    """
    file_path = VIDEO_DIR / video_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    BASE_URL = "https://tragic-embed.onrender.com"
    video_url = f"{BASE_URL}/videos/{video_name}"

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
