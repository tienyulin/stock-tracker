"""
AI Portfolio Assistant API v1 routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.ai_portfolio_service import AIService
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Portfolio Assistant"])


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Send a message to the AI portfolio assistant.
    Streams response in SSE format.
    """
    service = AIService(db)

    async def event_generator():
        async for chunk in service.chat_stream(
            user_id=current_user.id,
            message=request.message,
            conversation_id=request.conversation_id,
        ):
            if "delta" in chunk:
                yield f"data: {chunk['delta']}\n\n"
            elif chunk.get("done"):
                yield f"data: [DONE] conversation_id={chunk['conversation_id']}\n\n"
                yield f"data: disclaimer={chunk.get('disclaimer', '')}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def list_conversations(
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """List all AI conversations for the current user."""
    service = AIService(db)
    conversations = service.list_conversations(current_user.id)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get a specific conversation with all messages."""
    service = AIService(db)
    conv = service.get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in conv.messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Delete an AI conversation."""
    service = AIService(db)
    success = service.delete_conversation(conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}
