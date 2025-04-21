import os
import re
import io
import hashlib
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, FileResponse
import httpx
from PIL import Image

load_dotenv()

router = APIRouter(
    prefix="",
    tags=["proxy"]
)

BASE_URL = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/static_flyers"
IMAGES_URL = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/property_images"

# Create cache directory for optimized images - use a persistent path
CACHE_DIR = Path(os.getenv('CACHE_DIR', '/data/image_cache'))
CACHE_DIR.mkdir(exist_ok=True, parents=True)
print(f"📁 CACHE DIRECTORY: {CACHE_DIR.absolute()}")

# Specific routes first
@router.get("/sitemap.xml")
async def serve_sitemap():
    """Proxy the sitemap XML from Supabase function"""
    try:
        print(f"📝 SITEMAP REQUEST: Fetching from Supabase function")
        start_time = datetime.now()
        
        sitemap_url = "https://ayxhtlzyhpsjykxxnqqh.functions.supabase.co/generate-sitemap"
        async with httpx.AsyncClient() as client:
            response = await client.get(sitemap_url)
            response.raise_for_status()
            sitemap_content = response.text
            
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"✅ SITEMAP SERVED: Processing time: {processing_time:.2f}s")
            
        return Response(
            content=sitemap_content,
            media_type="application/xml",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Type": "application/xml; charset=utf-8",
            }
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to serve sitemap: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving sitemap: {str(e)}")

# Specific route for image proxy
@router.get("/image-proxy/{image_name}")
async def proxy_image(request: Request, image_name: str, width: int = 1200, height: int = 630, quality: int = 80):
    """Proxy and optimize an image using Pillow"""
    print(f"🖼️ IMAGE PROXY REQUEST: {image_name} (width={width}, height={height}, quality={quality})")
    start_time = datetime.now()
    
    try:
        # Create cache filename with parameters
        filename_base, ext = os.path.splitext(image_name)
        cache_filename = f"{filename_base}_w{width}_h{height}_q{quality}_cached.jpg"
        cache_path = CACHE_DIR / cache_filename
        
        # Check if cached version exists
        if cache_path.exists():
            print(f"✅ CACHE HIT: Serving {image_name} from cache")
            return FileResponse(
                cache_path,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=31536000"}
            )
        
        print(f"🔄 CACHE MISS: Fetching original image {image_name}")
        # Fetch original image
        original_url = f"{IMAGES_URL}/{image_name}"
        async with httpx.AsyncClient() as client:
            response = await client.get(original_url)
            response.raise_for_status()
            image_data = response.content
        
        print(f"🔧 PROCESSING: Optimizing image {image_name}")
        # Process with Pillow
        img = Image.open(io.BytesIO(image_data))
        original_size = len(image_data)
        
        # Resize while maintaining aspect ratio
        img.thumbnail((width, height), Image.LANCZOS)
        
        # Save optimized image to cache
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        output.seek(0)
        optimized_data = output.getvalue()
        optimized_size = len(optimized_data)
        
        # Write to cache file
        with open(cache_path, "wb") as f:
            f.write(optimized_data)
        
        compression_ratio = (1 - (optimized_size / original_size)) * 100
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"💾 CACHED: {cache_filename} - Original: {original_size/1024:.1f}KB, Optimized: {optimized_size/1024:.1f}KB")
        print(f"📊 STATS: Compression: {compression_ratio:.1f}%, Processing time: {processing_time:.2f}s")
        
        # Return the optimized image
        return Response(
            content=optimized_data,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000"}
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to optimize image {image_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error optimizing image: {str(e)}")

# Generic route last
@router.get("/{user_id}/{file_id:path}")
async def get_flyer(request: Request, user_id: str, file_id: str):
    """Proxy and serve HTML content with optimized OG images"""
    # Skip if this is a special route
    if user_id in ["sitemap", "image-proxy"]:
        raise HTTPException(status_code=404, detail="Not found")
    
    print(f"📄 HTML REQUEST: /{user_id}/{file_id}")
    start_time = datetime.now()
    
    try:
        # Construct full URL
        full_url = f"{BASE_URL}/{user_id}/{file_id}"
        print(f"🔄 FETCHING: HTML from {full_url}")
        
        # Fetch content
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url)
            response.raise_for_status()
            content = response.text
        
        # Find and replace og:image tags with optimized versions
        pattern = r'<meta\s+property="og:image"\s+content="([^"]+)"'
        
        def replace_with_optimized(match):
            original_url = match.group(1)
            # Extract image name from URL
            image_name = original_url.split('/')[-1]
            # Create optimized URL with absolute path using the production domain
            host = os.getenv('HOST_URL', 'https://show.realbroker.pro')
            optimized_url = f"{host}/image-proxy/{image_name}"
            print(f"🔄 REPLACING: OG image URL {original_url} → {optimized_url}")
            return f'<meta property="og:image" content="{optimized_url}"'
        
        original_content = content
        modified_content = re.sub(pattern, replace_with_optimized, content)
        
        is_modified = original_content != modified_content
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if is_modified:
            print(f"✅ MODIFIED: OG image tags replaced in HTML")
        else:
            print(f"ℹ️ UNCHANGED: No OG image tags found or replaced")
            
        print(f"⏱️ SERVED: HTML in {processing_time:.2f}s")
        
        return Response(
            content=modified_content,
            media_type='text/html',
            headers={
                "Cache-Control": "no-transform",
                "Content-Type": "text/html; charset=utf-8",
                "X-Content-Type-Options": "nosniff",
                "Content-Disposition": "inline"
            }
        )
        
    except Exception as e:
        print(f"❌ ERROR: Failed to serve HTML /{user_id}/{file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving page: {str(e)}") 