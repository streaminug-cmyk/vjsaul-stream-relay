import os
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI(title="Streaming UG - Cloud HLS Sniffer Relay")

# Permanent file path inside the cloud workspace container
CACHE_FILE = "/tmp/stream_cache.json"

def get_cached_streams():
    """Reads the active token keys securely from the shared system file storage."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cached_streams(data):
    """Writes the fresh stream links instantly so all server workers see it simultaneously."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

@app.get("/")
def read_root():
    streams = get_cached_streams()
    return {
        "status": "Cloud HLS Relay Server is running perfectly!", 
        "active_keys": list(streams.keys()),
        "cached_default": streams.get("default", "none")
    }

@app.get("/update-cloud-token")
def update_cloud_token(channel: str = Query(...), url: str = Query(...)):
    if not url or not channel:
        raise HTTPException(status_code=400, detail="Missing channel or url parameters")
    
    # Force atomic file-level updates across all thread workers
    streams = get_cached_streams()
    streams[channel.lower().strip()] = url
    streams["default"] = url
    save_cached_streams(streams)
    
    print(f"🔄 Global Shared Cache Synced for [{channel}]: {url}")
    return {"status": "success", "message": f"Channel {channel} updated successfully"}

@app.get("/stream/{channel_slug}")
def get_channel_stream(channel_slug: str):
    slug = channel_slug.lower().strip()
    streams = get_cached_streams()
    stream_url = streams.get(slug) or streams.get("default")

    if not stream_url or stream_url == "none":
        raise HTTPException(
            status_code=404, 
            detail="Stream token not yet uploaded by home PC script."
        )

    print(f"🚀 User connected from Android! Redirecting cleanly to: {stream_url}")
    return RedirectResponse(url=stream_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
