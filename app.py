# app.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
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
async def get_video_embed_payload(
    video_name: str,
    title: Optional[str] = Query(
        None,
        description="Custom title to show in the embed. "
                    "If omitted, defaults to '📹 {video_name}'.",
    ),
    description: Optional[str] = Query(
        None,
        description="Custom description to show in the embed. "
                    "If omitted, defaults to 'Streaming **{video_name}** now!'.",
    ),
    thumbnail_url: Optional[str] = Query(
        None,
        description="URL of a custom thumbnail (poster) image. "
                    "If omitted, no thumbnail field is included.",
    ),
    color: Optional[int] = Query(
        None,
        description="Integer color code for Discord embed (e.g. 0xFF00FF). "
                    "If omitted, Discord uses its default embed color.",
    ),
):
    """
    Returns a JSON payload (Discord-style embed) pointing at the video URL.
    You can override the default title/description/thumbnail/color by passing
    query-string parameters. If you leave them out, sensible defaults are used.

    Example GET (default):
      GET /embed/video/myclip.mp4
    Example GET (custom):
      GET /embed/video/myclip.mp4?
           title=My+Custom+Clip&
           description=Check+out+this+awesome+clip!&
           thumbnail_url=https://example.com/thumb.jpg&
           color=16711680
    """
    file_path = VIDEO_DIR / video_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")

    # Build the public URL. Update this to your actual HTTPS domain on Render.
    BASE_URL = "https://tragic-embeds.onrender.com"
    video_url = f"{BASE_URL}/videos/{video_name}"

    # Default fields if not provided
    default_title = f"📹 {video_name}"
    default_description = f"Streaming **{video_name}** now!"

    embed_dict = {
        "embed": {
            "title": title.strip() if title else default_title,
            "description": description.strip() if description else default_description,
            "url": video_url,
            "video": {"url": video_url},
        }
    }

    # Only include thumbnail if the user provided a URL
    if thumbnail_url:
        embed_dict["embed"]["thumbnail"] = {"url": thumbnail_url.strip()}

    # Only include color if the user provided an integer
    if color is not None:
        embed_dict["embed"]["color"] = color

    return embed_dict
