from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import httpx
import os
from pathlib import Path
import asyncio
import time

app = FastAPI(
    title="HTML File Proxy Server",
    description="Downloads and serves HTML files from Supabase storage"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a cache directory if it doesn't exist
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

class FileUrl(BaseModel):
    url: HttpUrl

async def download_file(url: str, filename: str) -> str:
    """Download file from URL and save to cache"""
    cache_path = CACHE_DIR / filename
    
    # Return cached file if it exists and is less than 1 hour old
    if cache_path.exists():
        file_age = os.path.getmtime(cache_path)
        if (time.time() - file_age) < 3600:  # 1 hour cache
            return cache_path.read_text(encoding='utf-8')
    
    # Download file if not cached or cache expired
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            # Save to cache
            cache_path.write_text(response.text, encoding='utf-8')
            return response.text
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

@app.post("/serve", response_class=HTMLResponse)
async def serve_html(file_url: FileUrl):
    """
    Download and serve HTML file from provided URL
    """
    try:
        # Extract filename from URL
        filename = file_url.url.split('/')[-1]
        
        # Download and get content
        content = await download_file(str(file_url.url), filename)
        
        return HTMLResponse(content=content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

@app.get("/cached/{filename}", response_class=HTMLResponse)
async def serve_cached(filename: str):
    """
    Serve a cached HTML file
    """
    try:
        cache_path = CACHE_DIR / filename
        if not cache_path.exists():
            raise HTTPException(status_code=404, detail="File not found in cache")
            
        content = cache_path.read_text(encoding='utf-8')
        return HTMLResponse(content=content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving cached file: {str(e)}")

@app.get("/cache-list")
async def list_cached_files():
    """
    List all cached files
    """
    try:
        files = [f.name for f in CACHE_DIR.glob("*.html")]
        return {"cached_files": files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing cache: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 