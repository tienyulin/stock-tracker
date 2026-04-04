"""
AI Portfolio Assistant Service
Provides RAG-powered chat responses using portfolio data.
"""
import os
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy.orm import Session

from app.models.ai_conversation import AIConversation, AIMessage
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioHolding


DISCLAIMER = "⚠️ This is not financial advice. Past performance does not guarantee future results. Always do your own research."


class AIService:
    def __init__(self, db: Session):
        self.db = db

    async def chat_stream(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream AI response with RAG context from user's portfolio."""
        # Get or create conversation
        if conversation_id:
            conv = self.db.query(AIConversation).filter(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
            ).first()
        else:
            conv = AIConversation(id=str(uuid.uuid4()), user_id=user_id, title=message[:50])
            self.db.add(conv)
            self.db.flush()

        # Save user message
        user_msg = AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=message,
        )
        self.db.add(user_msg)

        # Build context from portfolio data
        context = await self._build_portfolio_context(user_id)

        # Get conversation history for context
        history = self._get_conversation_history(conv.id)

        # Build prompt
        prompt = self._build_prompt(message, context, history)

        # Stream response from AI
        full_response = ""
        async for chunk in self._stream_ai_response(prompt):
            full_response += chunk
            yield {"delta": chunk, "conversation_id": conv.id}

        # Save assistant message
        assistant_msg = AIMessage(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="assistant",
            content=full_response + f"\n\n{DISCLAIMER}",
        )
        self.db.add(assistant_msg)
        self.db.commit()

        yield {"done": True, "conversation_id": conv.id, "disclaimer": DISCLAIMER}

    async def _build_portfolio_context(self, user_id: str) -> str:
        """Build RAG context from user's portfolio data."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return "No portfolio data available."

        portfolios = self.db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        if not portfolios:
            return "User has no portfolios yet."

        context_parts = []
        for portfolio in portfolios:
            holdings = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio.id
            ).all()

            holdings_str = ", ".join([
                f"{h.symbol}: {h.quantity} shares"
                for h in holdings
            ]) if holdings else "No holdings"

            context_parts.append(
                f"Portfolio '{portfolio.name}': {holdings_str}. "
                f"Total value: ${portfolio.total_value or 0:.2f}"
            )

        return " | ".join(context_parts)

    def _get_conversation_history(self, conversation_id: str, limit: int = 10) -> list:
        """Get recent messages for context."""
        messages = self.db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id
        ).order_by(AIMessage.created_at.desc()).limit(limit).all()
        return [(m.role, m.content) for m in reversed(messages)]

    def _build_prompt(self, message: str, context: str, history: list) -> str:
        """Build the full prompt with system instructions."""
        history_str = ""
        if history:
            history_str = "Conversation history:\n" + "\n".join(
                f"{role}: {content}" for role, content in history
            ) + "\n"

        return f"""You are an AI-powered portfolio assistant for a stock tracking application.

User's Portfolio Data: {context}

{history_str}
User: {message}
Assistant:"""

    async def _stream_ai_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream response from AI API (OpenAI or Claude)."""
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            # Fallback for demo mode
            demo_response = "I'm your portfolio assistant. To provide AI-powered responses, please configure an OpenAI or Anthropic API key in your environment variables."
            for word in demo_response.split():
                yield word + " "
                import asyncio
                await asyncio.sleep(0.05)
            return

        # OpenAI streaming implementation
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai
                client = openai.AsyncOpenAI()
                stream = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=1000,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                yield f"[Error calling AI API: {str(e)}]"
        else:
            # Claude implementation
            try:
                import anthropic
                client = anthropic.AsyncAnthropic()
                async with client.messages.stream(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                ) as stream:
                    async for text in stream.text_stream:
                        yield text
            except Exception as e:
                yield f"[Error calling AI API: {str(e)}]"

    def list_conversations(self, user_id: str) -> list:
        """List all conversations for a user."""
        return self.db.query(AIConversation).filter(
            AIConversation.user_id == user_id,
            AIConversation.is_active,
        ).order_by(AIConversation.updated_at.desc()).all()

    def get_conversation(self, conversation_id: str, user_id: str) -> Optional[AIConversation]:
        """Get a specific conversation with messages."""
        return self.db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id,
        ).first()

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Soft delete a conversation."""
        conv = self.get_conversation(conversation_id, user_id)
        if conv:
            conv.is_active = False
            self.db.commit()
            return True
        return False
