from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, case, inspect, or_
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


class ChatSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def schema_ready(self) -> bool:
        bind = self.db.get_bind()
        if bind is None:
            return False

        inspector = inspect(bind)
        tables = set(inspector.get_table_names())
        return {"chat_sessions", "chat_messages"}.issubset(tables)

    @staticmethod
    def _is_expired(session: ChatSession) -> bool:
        return bool(
            session.expires_at
            and session.expires_at <= datetime.now(UTC)
        )

    @staticmethod
    def _default_expires_at() -> datetime | None:
        if settings.CHAT_SESSION_TTL_HOURS <= 0:
            return None

        return datetime.now(UTC) + timedelta(
            hours=settings.CHAT_SESSION_TTL_HOURS,
        )

    @staticmethod
    def _normalize_title(title: str | None) -> str | None:
        if not title:
            return None

        normalized = " ".join(title.strip().split())
        if not normalized:
            return None

        return normalized[:255]

    def prune_expired(self) -> int:
        removed = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.expires_at.is_not(None),
                ChatSession.expires_at <= datetime.now(UTC),
            )
            .delete(synchronize_session=False)
        )
        if removed:
            self.db.commit()
        return removed

    def create(self, title: str | None = None) -> ChatSession:
        session = ChatSession(
            title=self._normalize_title(title),
            expires_at=self._default_expires_at(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(
        self,
        session_id: UUID,
        include_messages: bool = False,
    ) -> ChatSession | None:
        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

        if session is None:
            return None

        if self._is_expired(session):
            self.db.delete(session)
            self.db.commit()
            return None

        if include_messages:
            session.messages

        return session

    def list_page(
        self,
        limit: int,
        cursor: UUID | None = None,
    ) -> tuple[list[ChatSession], UUID | None]:
        query = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.expires_at.is_(None)
                | (ChatSession.expires_at > datetime.now(UTC))
            )
        )

        if cursor is not None:
            cursor_session = self.db.get(ChatSession, cursor)
            if cursor_session is None:
                return [], None
            query = query.filter(
                or_(
                    ChatSession.last_message_at < cursor_session.last_message_at,
                    and_(
                        ChatSession.last_message_at == cursor_session.last_message_at,
                        ChatSession.id < cursor_session.id,
                    ),
                )
            )

        sessions = (
            query.order_by(ChatSession.last_message_at.desc(), ChatSession.id.desc())
            .limit(limit + 1)
            .all()
        )
        next_cursor = sessions[limit].id if len(sessions) > limit else None
        return sessions[:limit], next_cursor

    def delete(self, session_id: UUID) -> bool:
        session = self.get_by_id(session_id, include_messages=True)
        if session is None:
            return False

        self.db.delete(session)
        self.db.commit()
        return True


class ChatMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _generate_title_from_message(content: str) -> str:
        summary = " ".join(content.strip().split())
        if not summary:
            return "New Chat"

        return summary[:60].rstrip() or "New Chat"

    def add_message(
        self,
        session: ChatSession,
        role: str,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session.id,
            role=role,
            content=content.strip(),
        )
        self.db.add(message)

        if not session.title and role == "user":
            session.title = self._generate_title_from_message(content)

        session.last_message_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(message)
        self.db.refresh(session)
        return message

    def add_turn(
        self,
        session: ChatSession,
        question: str,
        answer: str,
    ) -> tuple[ChatMessage, ChatMessage]:
        """Persist one completed question/answer turn as a single transaction."""
        turn_started_at = datetime.now(UTC)
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=question.strip(),
            created_at=turn_started_at,
            updated_at=turn_started_at,
        )
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer.strip(),
            created_at=turn_started_at + timedelta(microseconds=1),
            updated_at=turn_started_at + timedelta(microseconds=1),
        )

        self.db.add_all([user_message, assistant_message])

        if not session.title:
            session.title = self._generate_title_from_message(question)

        session.last_message_at = datetime.now(UTC)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(user_message)
        self.db.refresh(assistant_message)
        self.db.refresh(session)
        return user_message, assistant_message

    def get_history_for_session(
        self,
        session_id: UUID,
        max_turns: int,
        max_chars: int,
    ) -> list[ChatMessage]:
        newest_role_first = case(
            (ChatMessage.role == "assistant", 1),
            else_=0,
        )
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(
                ChatMessage.created_at.desc(),
                newest_role_first.desc(),
                ChatMessage.id.desc(),
            )
            .limit(max_turns * 4)
            .all()
        )
        chronological = list(reversed(messages))
        turns: list[list[ChatMessage]] = []
        pending_user: ChatMessage | None = None
        for message in chronological:
            if message.role == "user":
                pending_user = message
            elif message.role == "assistant" and pending_user is not None:
                turns.append([pending_user, message])
                pending_user = None

        selected: list[list[ChatMessage]] = []
        used_chars = 0
        for turn in reversed(turns):
            turn_chars = sum(len(message.content) for message in turn)
            if selected and used_chars + turn_chars > max_chars:
                break
            if turn_chars > max_chars:
                continue
            selected.append(turn)
            used_chars += turn_chars
            if len(selected) >= max_turns:
                break

        return [message for turn in reversed(selected) for message in turn]

    def get_messages_page(
        self,
        session_id: UUID,
        limit: int,
        before: UUID | None = None,
    ) -> tuple[list[ChatMessage], UUID | None]:
        query = self.db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
        if before is not None:
            cursor_message = self.db.get(ChatMessage, before)
            if cursor_message is None or cursor_message.session_id != session_id:
                return [], None
            query = query.filter(
                or_(
                    ChatMessage.created_at < cursor_message.created_at,
                    and_(
                        ChatMessage.created_at == cursor_message.created_at,
                        ChatMessage.id < cursor_message.id,
                    ),
                )
            )
        newest_role_first = case(
            (ChatMessage.role == "assistant", 1),
            else_=0,
        )
        messages = (
            query.order_by(
                ChatMessage.created_at.desc(),
                newest_role_first.desc(),
                ChatMessage.id.desc(),
            )
            .limit(limit + 1)
            .all()
        )
        next_before = messages[limit].id if len(messages) > limit else None
        return list(reversed(messages[:limit])), next_before
