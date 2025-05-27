import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from flo_json_collector import FloJsonOutputCollector, CollectionStatus, FloException

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(
    title="LLM Memory Management Demo",
    description="Advanced JSON collection and memory management for LLM outputs",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global collector instances (in production, this would be session-based)
collectors: Dict[str, FloJsonOutputCollector] = {}

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class LLMResponseInput(BaseModel):
    content: str
    session_id: Optional[str] = None
    strict_mode: bool = False

class CollectorCreateInput(BaseModel):
    session_id: str
    strict_mode: bool = False

class IterationRequest(BaseModel):
    session_id: str
    depth: Optional[int] = None

class RewindRequest(BaseModel):
    session_id: str
    depth: Optional[int] = None

# ———————————————————————————————
# Original API Endpoints
# ———————————————————————————————

@api_router.get("/")
async def root():
    return {"message": "LLM Memory Management Demo API", "version": "1.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# ———————————————————————————————
# FloJsonOutputCollector API Endpoints
# ———————————————————————————————

@api_router.post("/collector/create")
async def create_collector(input: CollectorCreateInput):
    """Create a new FloJsonOutputCollector instance."""
    if input.session_id in collectors:
        raise HTTPException(status_code=400, detail="Session already exists")
    
    collector = FloJsonOutputCollector(strict=input.strict_mode)
    collector.set_session_context(input.session_id)
    collectors[input.session_id] = collector
    
    return {
        "message": "Collector created successfully",
        "session_id": input.session_id,
        "strict_mode": input.strict_mode,
        "status": "active"
    }

@api_router.post("/collector/process")
async def process_llm_response(input: LLMResponseInput):
    """Process LLM response and extract JSON."""
    session_id = input.session_id or "default"
    
    # Create collector if it doesn't exist
    if session_id not in collectors:
        collector = FloJsonOutputCollector(strict=input.strict_mode)
        collector.set_session_context(session_id)
        collectors[session_id] = collector
    else:
        collector = collectors[session_id]
    
    try:
        collector.append(input.content)
        return {
            "success": True,
            "session_id": session_id,
            "extracted_json": collector.peek(),
            "status": collector.status.value,
            "total_entries": len(collector.data),
            "memory_trail_length": len(collector.memory_trail)
        }
    except FloException as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/collector/status/{session_id}")
async def get_collector_status(session_id: str):
    """Get current status and summary of a collector."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[session_id]
    return collector.get_context_summary()

@api_router.get("/collector/memory/{session_id}")
async def get_memory_trail(session_id: str):
    """Get the complete memory breadcrumb trail."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[session_id]
    return {
        "session_id": session_id,
        "memory_trail": collector.get_memory_trail(),
        "total_entries": len(collector.data)
    }

@api_router.get("/collector/peek/{session_id}")
async def peek_latest(session_id: str):
    """Peek at the latest collected entry without removing it."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[session_id]
    latest = collector.peek()
    return {
        "session_id": session_id,
        "latest_entry": latest,
        "has_data": latest is not None
    }

@api_router.post("/collector/pop/{session_id}")
async def pop_latest(session_id: str):
    """Remove and return the latest collected entry."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[session_id]
    try:
        popped = collector.pop()
        return {
            "session_id": session_id,
            "popped_entry": popped,
            "remaining_entries": len(collector.data)
        }
    except IndexError:
        raise HTTPException(status_code=404, detail="No entries to pop")

@api_router.get("/collector/fetch/{session_id}")
async def fetch_merged(session_id: str):
    """Get all collected data merged into a single dictionary."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[session_id]
    merged = collector.fetch()
    return {
        "session_id": session_id,
        "merged_data": merged,
        "source_entries": len(collector.data)
    }

@api_router.post("/collector/iterator/create")
async def create_iterator(input: IterationRequest):
    """Create a new iterator for the collector data."""
    if input.session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[input.session_id]
    iterator = collector.iter_q(depth=input.depth)
    
    # Store iterator in memory (in production, use proper session management)
    iterator_id = str(uuid.uuid4())
    # For this demo, we'll return iterator info rather than storing it
    
    return {
        "iterator_id": iterator_id,
        "session_id": input.session_id,
        "total_entries": len(iterator.entries),
        "limit": iterator.limit,
        "position": iterator.current_position()
    }

@api_router.post("/collector/iterator/next")
async def iterator_next(input: IterationRequest):
    """Get next batch from iterator."""
    if input.session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[input.session_id]
    iterator = collector.iter_q(depth=input.depth)
    
    next_batch = iterator.next()
    position = iterator.current_position()
    
    return {
        "session_id": input.session_id,
        "next_batch": next_batch,
        "position": position,
        "has_more": position["has_next"]
    }

@api_router.post("/collector/rewind")
async def rewind_memory(input: RewindRequest):
    """Demonstrate rewind functionality."""
    if input.session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[input.session_id]
    rewind_trail = []
    
    def capture_rewind(entry):
        rewind_trail.append({
            "entry": entry,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    collector.rewind(then_callback=capture_rewind, depth=input.depth)
    
    return {
        "session_id": input.session_id,
        "rewind_trail": rewind_trail,
        "depth_processed": len(rewind_trail)
    }

@api_router.delete("/collector/clear/{session_id}")
async def clear_collector(session_id: str):
    """Clear all data from a collector."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    collector = collectors[session_id]
    collector.clear_memory()
    
    return {
        "session_id": session_id,
        "message": "Collector cleared successfully",
        "status": "cleared"
    }

@api_router.delete("/collector/delete/{session_id}")
async def delete_collector(session_id: str):
    """Delete a collector session."""
    if session_id not in collectors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del collectors[session_id]
    
    return {
        "session_id": session_id,
        "message": "Collector deleted successfully",
        "status": "deleted"
    }

@api_router.get("/collector/sessions")
async def list_sessions():
    """List all active collector sessions."""
    sessions = []
    for session_id, collector in collectors.items():
        sessions.append({
            "session_id": session_id,
            "status": collector.status.value,
            "strict_mode": collector.strict,
            "total_entries": len(collector.data),
            "memory_trail_length": len(collector.memory_trail)
        })
    
    return {
        "active_sessions": sessions,
        "total_sessions": len(sessions)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
