import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI(title="Streaming UG - Cloud HLS Sniffer Relay")

# Global cache to store active sniffed .m3u8 links sent by your PC
active_streams = {}

@app.get("/")
def read_root():
    return {
        "status": "Cloud HLS Relay Server is running perfectly!", 
        "active_keys": list(active_streams.keys()),
        "cached_default": active_streams.get("default", "none")
    }

# 🎯 NEW ENDPOINT: This allows your local PC sniffer to push fresh tokens to the cloud
@app.get("/update-cloud-token")
def update_cloud_token(channel: str = Query(...), url: str = Query(...)):
    if not url or not channel:
        raise HTTPException(status_code=400, detail="Missing channel or url parameters")
    
    # Save the fresh stream link into the cloud memory cache
    active_streams[channel.lower().strip()] = url
    active_streams["default"] = url
    print(f"🔄 Token updated from PC for channel [{channel}]: {url}")
    return {"status": "success", "message": f"Channel {channel} updated successfully"}

@app.get("/stream/{channel_slug}")
def get_channel_stream(channel_slug: str):
    slug = channel_slug.lower().strip()
    stream_url = active_streams.get(slug) or active_streams.get("default")

    if not stream_url or stream_url == "none":
        raise HTTPException(
            status_code=404, 
            detail="Stream token not yet uploaded by home PC script. Please ensure home sniffer is running."
        )

    print(f"🚀 User connected from Android! Redirecting cleanly to: {stream_url}")
    return RedirectResponse(url=stream_url)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
