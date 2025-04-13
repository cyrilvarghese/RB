from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx

router = APIRouter(
    prefix="/flyer",
    tags=["proxy"]
)

BASE_URL = "https://ayxhtlzyhpsjykxxnqqh.supabase.co/storage/v1/object/public/property_html_files"

@router.get("/{file_id}")
async def serve_page(file_id: str):
    """Proxy and serve HTML content directly from file ID"""
    try:
        # Construct full URL
        url = f"{BASE_URL}/{file_id}"
        
        # Fetch and serve content
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text
        
        return Response(
            content=content,
            media_type='text/html',
            headers={
                "Cache-Control": "no-transform",
                "Content-Type": "text/html; charset=utf-8",
                "X-Content-Type-Options": "nosniff",
                "Content-Disposition": "inline"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving page: {str(e)}") 