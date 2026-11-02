import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
from playwright.async_api import async_playwright

app = FastAPI(title="Streaming UG - Cloud HLS Sniffer Relay")

# Global cache to store active sniffed .m3u8 links per channel
active_streams = {}

DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
TARGET_SITE = "https://beyii.com"

async def sniff_channels_background():
    """
    Background worker using Playwright (Headless Chromium) to visit ://beyii.com,
    sniff incoming HLS (.m3u8) network requests, and cache them in real-time.
    """
    print("Starting Playwright background HLS sniffer...")
    while True:
        try:
            async with async_playwright() as p:
                # Headless mode is strictly required for cloud server deployment
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=DESKTOP_UA,
                    viewport={"width": 1366, "height": 768}
                )
                page = await context.new_page()

                # Intercept network requests to capture tokenized .m3u8 streaming links
                def handle_request(request):
                    url = request.url
                    url_lower = url.lower()
                    if ".m3u8" in url_lower or "/hls/" in url_lower or ":8443" in url:
                        print(f"[SNIFFED STREAM CLOUD]: {url}")
                        active_streams["default"] = url
                        
                        if "2vrp5s4duu8un" in url or "supersport" in url_lower:
                            active_streams["supersport-variety-4"] = url
                        elif "bein" in url_lower:
                            active_streams["bein-sports-1"] = url

                page.on("request", handle_request)

                print(f"Navigating to {TARGET_SITE}...")
                # Use domcontentloaded to handle heavy pages faster
                await page.goto(TARGET_SITE, timeout=60000, wait_until="domcontentloaded")

                # 🎯 Force user interaction to boot the HTML5 streaming player infrastructure
                await asyncio.sleep(5)
                try:
                    print("Simulating browser interaction clicks to trigger video initialization...")
                    
                    # 1. Click standard web video selectors if visible
                    video_elements = await page.query_selector_all("video, iframe, .player-container, #player")
                    for elem in video_elements[:3]: # Interact with primary nodes
                        await elem.click(timeout=2000)
                    
                    # 2. Search inside all available sub-iframes for nested player elements
                    for frame in page.frames:
                        try:
                            frame_video = await frame.query_selector("video, .jwplayer, .vjs-tech")
                            if frame_video:
                                await frame_video.click(timeout=2000)
                        except Exception:
                            continue
                            
                    print("Interaction completed. Waiting for server chunk manifest responses...")
                    await asyncio.sleep(10)
                except Exception as click_err:
                    print(f"Selector interaction skipped or timed out: {click_err}")

                # Keep browser active sniffing for 10 minutes, then recycle session to refresh dynamic tokens
                await asyncio.sleep(600)
                await browser.close()

        except Exception as e:
            print(f"Playwright sniffer error on cloud: {e}")
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    # Spawn the background crawler worker lifecycle task
    asyncio.create_task(sniff_channels_background())

@app.get("/")
def read_root():
    # Endpoint read by monitoring tools to keep instance healthy
    return {
        "status": "Cloud HLS Relay Server is running perfectly!", 
        "active_keys": list(active_streams.keys()),
        "cached_default": active_streams.get("default", "none")
    }

@app.get("/stream/{channel_slug}")
def get_channel_stream(channel_slug: str):
    """
    API Endpoint called directly by your Android application Media3 player layout
    """
    slug = channel_slug.lower().strip()
    stream_url = active_streams.get(slug) or active_streams.get("default")

    if not stream_url:
        raise HTTPException(
            status_code=404, 
            detail="Stream token not yet sniffed by cloud worker. Wait 10 seconds and refresh."
        )

    print(f"🚀 User connected from Android! Redirecting cleanly to: {stream_url}")
    
    # Returns an HTTP 307 Redirect layout right back to Media3 ExoPlayer
    return RedirectResponse(url=stream_url)

if __name__ == "__main__":
    # Bind dynamically to the port provided by Render's system engine
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
