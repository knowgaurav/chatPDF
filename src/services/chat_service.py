"""
Chat Service - Conversation Management

Manages chat sessions with:
- Conversation memory (buffer, window, summary)
- Chat history persistence
- Context window management
- Multi-turn dialogue support
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque

from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationBufferWindowMemory
)

from ..providers.base_provider import Message

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Individual chat message"""
    id: Optional[str] = None
    session_id: str = ""
    role: str = ""  # 'user', 'assistant', 'system'
    content: str = ""
    sources: Optional[List[Dict[str, Any]]] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_message(self) -> Message:
        """Convert to provider Message format"""
        return Message(role=self.role, content=self.content)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata
        }


@dataclass
class ChatSession:
    """Chat session with conversation state"""
    id: str
    user_id: Optional[str] = None
    document_ids: List[str] = field(default_factory=list)
    title: Optional[str] = None
    memory_type: str = "buffer"  # 'buffer', 'window', 'summary'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatConfig:
    """Configuration for chat service"""
    memory_type: str = "buffer"  # 'buffer', 'window', 'summary'
    window_size: int = 5  # For window memory
    max_token_limit: int = 4000  # Context window limit
    include_sources: bool = True
    persist_history: bool = True


class ChatService:
    """
    Chat service for managing conversations and memory
    """

    def __init__(
        self,
        db_session,
        llm_service,
        config: Optional[ChatConfig] = None
    ):
        """
        Initialize chat service

        Args:
            db_session: Database session for persistence
            llm_service: LLM service for summary generation
            config: Chat configuration
        """
        self.db = db_session
        self.llm_service = llm_service
        self.config = config or ChatConfig()

        # In-memory session storage
        self.sessions: Dict[str, ChatSession] = {}
        self.memories: Dict[str, Any] = {}  # session_id -> memory object
        self.message_buffers: Dict[str, deque] = {}  # session_id -> message buffer

        logger.info("Chat service initialized")

    async def create_session(
        self,
        user_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        title: Optional[str] = None,
        memory_type: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session

        Args:
            user_id: User identifier
            document_ids: List of document IDs for context
            title: Session title
            memory_type: Type of memory to use

        Returns:
            Created ChatSession
        """
        import uuid

        session_id = str(uuid.uuid4())
        memory_type = memory_type or self.config.memory_type

        session = ChatSession(
            id=session_id,
            user_id=user_id,
            document_ids=document_ids or [],
            title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            memory_type=memory_type,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Store session
        self.sessions[session_id] = session

        # Initialize memory
        self.memories[session_id] = self._create_memory(memory_type)

        # Initialize message buffer
        self.message_buffers[session_id] = deque(maxlen=100)  # Keep last 100 messages

        # Persist to database if enabled
        if self.config.persist_history:
            await self._persist_session(session)

        logger.info(f"Created chat session: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a chat session

        Args:
            session_id: Session identifier

        Returns:
            ChatSession or None if not found
        """
        # Check in-memory first
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Try loading from database
        if self.config.persist_history:
            session = await self._load_session(session_id)
            if session:
                self.sessions[session_id] = session
                return session

        return None

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost: Optional[float] = None,
        latency_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Add a message to chat history

        Args:
            session_id: Session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            sources: Source citations (for assistant messages)
            model_used: LLM model used
            tokens_used: Tokens consumed
            cost: API cost
            latency_ms: Response latency
            metadata: Additional metadata

        Returns:
            Created ChatMessage
        """
        import uuid

        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            model_used=model_used,
            tokens_used=tokens_used,
            cost=cost,
            latency_ms=latency_ms,
            created_at=datetime.now(),
            metadata=metadata
        )

        # Add to buffer
        if session_id not in self.message_buffers:
            self.message_buffers[session_id] = deque(maxlen=100)

        self.message_buffers[session_id].append(message)

        # Update memory
        if session_id in self.memories:
            memory = self.memories[session_id]
            if role == "user":
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                memory.chat_memory.add_ai_message(content)

        # Update session timestamp
        if session_id in self.sessions:
            self.sessions[session_id].updated_at = datetime.now()

        # Persist to database if enabled
        if self.config.persist_history:
            await self._persist_message(message)

        logger.debug(f"Added message to session {session_id}: {role}")
        return message

    async def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
        include_system: bool = False
    ) -> List[ChatMessage]:
        """
        Get chat history for a session

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            include_system: Whether to include system messages

        Returns:
            List of ChatMessage objects
        """
        # Get from buffer
        if session_id in self.message_buffers:
            messages = list(self.message_buffers[session_id])

            # Filter system messages if needed
            if not include_system:
                messages = [msg for msg in messages if msg.role != "system"]

            # Apply limit
            if limit:
                messages = messages[-limit:]

            return messages

        # Try loading from database
        if self.config.persist_history:
            return await self._load_messages(session_id, limit, include_system)

        return []

    async def get_context_messages(
        self,
        session_id: str,
        max_tokens: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages for LLM context, respecting token limits

        Args:
            session_id: Session identifier
            max_tokens: Maximum tokens to include

        Returns:
            List of Message objects for LLM
        """
        max_tokens = max_tokens or self.config.max_token_limit

        # Get recent history
        messages = await self.get_history(session_id, limit=20)

        # Convert to Message format
        context_messages = [msg.to_message() for msg in messages]

        # Simple token estimation (4 chars ≈ 1 token)
        total_chars = sum(len(msg.content) for msg in context_messages)
        estimated_tokens = total_chars // 4

        # Trim if needed
        while estimated_tokens > max_tokens and len(context_messages) > 1:
            # Remove oldest message (but keep system messages)
            if context_messages[0].role != "system":
                context_messages.pop(0)
            else:
                context_messages.pop(1)

            total_chars = sum(len(msg.content) for msg in context_messages)
            estimated_tokens = total_chars // 4

        return context_messages

    async def get_memory_context(self, session_id: str) -> str:
        """
        Get conversation context from memory

        Args:
            session_id: Session identifier

        Returns:
            Context string from memory
        """
        if session_id not in self.memories:
            return ""

        memory = self.memories[session_id]

        try:
            # Get memory variables
            memory_vars = memory.load_memory_variables({})
            return memory_vars.get("history", "")
        except Exception as e:
            logger.warning(f"Failed to load memory context: {e}")
            return ""

    async def clear_history(self, session_id: str):
        """
        Clear chat history for a session

        Args:
            session_id: Session identifier
        """
        # Clear buffer
        if session_id in self.message_buffers:
            self.message_buffers[session_id].clear()

        # Clear memory
        if session_id in self.memories:
            self.memories[session_id].clear()

        # Clear from database if needed
        if self.config.persist_history:
            await self._delete_messages(session_id)

        logger.info(f"Cleared history for session: {session_id}")

    async def delete_session(self, session_id: str):
        """
        Delete a chat session

        Args:
            session_id: Session identifier
        """
        # Remove from memory
        self.sessions.pop(session_id, None)
        self.memories.pop(session_id, None)
        self.message_buffers.pop(session_id, None)

        # Delete from database
        if self.config.persist_history:
            await self._delete_session(session_id)

        logger.info(f"Deleted session: {session_id}")

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatSession]:
        """
        List chat sessions

        Args:
            user_id: Filter by user ID
            limit: Maximum number of sessions to return

        Returns:
            List of ChatSession objects
        """
        # Get from memory
        sessions = list(self.sessions.values())

        # Filter by user
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]

        # Sort by updated time
        sessions.sort(key=lambda s: s.updated_at or s.created_at, reverse=True)

        # Apply limit
        return sessions[:limit]

    def _create_memory(self, memory_type: str):
        """
        Create appropriate memory object

        Args:
            memory_type: Type of memory ('buffer', 'window', 'summary')

        Returns:
            Memory object
        """
        if memory_type == "buffer":
            return ConversationBufferMemory(
                return_messages=True
            )
        elif memory_type == "window":
            return ConversationBufferWindowMemory(
                k=self.config.window_size,
                return_messages=True
            )
        elif memory_type == "summary":
            # Note: Requires LLM for summarization
            return ConversationSummaryMemory(
                llm=self.llm_service,
                return_messages=True
            )
        else:
            logger.warning(f"Unknown memory type: {memory_type}, using buffer")
            return ConversationBufferMemory(
                return_messages=True
            )

    async def _persist_session(self, session: ChatSession):
        """Persist session to database"""
        # TODO: Implement database persistence
        pass

    async def _load_session(self, session_id: str) -> Optional[ChatSession]:
        """Load session from database"""
        # TODO: Implement database loading
        return None

    async def _persist_message(self, message: ChatMessage):
        """Persist message to database"""
        # TODO: Implement database persistence
        pass

    async def _load_messages(
        self,
        session_id: str,
        limit: Optional[int],
        include_system: bool
    ) -> List[ChatMessage]:
        """Load messages from database"""
        # TODO: Implement database loading
        return []

    async def _delete_messages(self, session_id: str):
        """Delete messages from database"""
        # TODO: Implement database deletion
        pass

    async def _delete_session(self, session_id: str):
        """Delete session from database"""
        # TODO: Implement database deletion
        pass

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session statistics
        """
        if session_id not in self.message_buffers:
            return {}

        messages = list(self.message_buffers[session_id])

        total_tokens = sum(msg.tokens_used or 0 for msg in messages)
        total_cost = sum(msg.cost or 0.0 for msg in messages)

        user_messages = [msg for msg in messages if msg.role == "user"]
        assistant_messages = [msg for msg in messages if msg.role == "assistant"]

        return {
            "session_id": session_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "created_at": self.sessions[session_id].created_at.isoformat() if session_id in self.sessions else None,
            "updated_at": self.sessions[session_id].updated_at.isoformat() if session_id in self.sessions else None
        }
