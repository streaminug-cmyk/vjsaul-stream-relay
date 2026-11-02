import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
from playwright.async_api import async_playwright

app = FastAPI(title="Streaming UG - Cloud HLS Sniffer Relay")

# Global cache to store active sniffed .m3u8 links per channel
active_streams = {}

DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
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
                # Headless is strictly required on cloud environments
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=DESKTOP_UA,
                    viewport={"width": 1366, "height": 768}
                )
                page = await context.new_page()

                # Intercept network requests to capture .m3u8 streaming links
                def handle_request(request):
                    url = request.url
                    if ".m3u8" in url.lower() or "/hls/" in url.lower() or ":8443" in url:
                        print(f"[SNIFFED STREAM CLOUD]: {url}")
                        active_streams["default"] = url
                        
                        if "2vrp5s4duu8un" in url or "supersport" in url.lower():
                            active_streams["supersport-variety-4"] = url
                        elif "bein" in url.lower():
                            active_streams["bein-sports-1"] = url

                page.on("request", handle_request)

                print(f"Navigating to {TARGET_SITE}...")
                await page.goto(TARGET_SITE, timeout=60000, wait_until="networkidle")

                # Keep browser alive and sniffing for 10 minutes, then restart to refresh session
                await asyncio.sleep(600)
                await browser.close()

        except Exception as e:
            print(f"Playwright sniffer error on cloud: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Automatically spawn the background crawler worker loop when FastAPI spins up
    asyncio.create_task(sniff_channels_background())

@app.get("/")
def read_root():
    # Root path required by cloud status checkers to verify the service is running cleanly
    return {
        "status": "Cloud HLS Relay Server is running perfectly!", 
        "active_keys": list(active_streams.keys()),
        "cached_default": active_streams.get("default", "none")
    }

@app.get("/stream/{channel_slug}")
def get_channel_stream(channel_slug: str):
    """
    API Endpoint called directly by your Media3 Player:
    https://onrender.com
    """
    slug = channel_slug.lower().strip()
    stream_url = active_streams.get(slug) or active_streams.get("default")

    if not stream_url:
        raise HTTPException(status_code=404, detail="Stream token not yet sniffed by cloud worker. Wait 5 seconds and try again.")

    print(f"🚀 User connected from Android! Redirecting cleanly to: {stream_url}")
    
    # 🎯 Returns a clean HTTP 307 RedirectResponse layout back to Media3 ExoPlayer.
    return RedirectResponse(url=stream_url)

if __name__ == "__main__":
    # Bind dynamically to the port provided by the environment configuration
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
