import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx

load_dotenv()

router = APIRouter(
    prefix="",
    tags=["proxy"]
)

BASE_URL = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/static_flyers"

@router.get("/{user_id}/{file_id}")
async def get_flyer(user_id: str, file_id: str):
    """Proxy and serve HTML content directly from file ID"""
    try:
        # Construct full URL
        full_url = f"{BASE_URL}/{user_id}/{file_id}"
        
        # Fetch and serve content
        async with httpx.AsyncClient() as client:
            response = await client.get(full_url)
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