from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.routers.proxy import router as proxy_router

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="File Server API",
    description="A FastAPI server for file operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"visit www.realbroker.pro"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add routers
app.include_router(proxy_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 