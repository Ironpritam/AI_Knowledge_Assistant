from uuid import uuid4

import pytest

from app.models.chat_session import ChatSession
from app.repositories.chat_repository import ChatMessageRepository


class FakeSession:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.added: list = []
        self.commit_count = 0
        self.rollback_count = 0

    def add_all(self, models: list) -> None:
        self.added.extend(models)

    def commit(self) -> None:
        self.commit_count += 1
        if self.should_fail:
            raise RuntimeError("database write failed")

    def rollback(self) -> None:
        self.rollback_count += 1

    def refresh(self, model) -> None:
        return None


def test_add_turn_persists_question_and_answer_in_one_commit() -> None:
    db = FakeSession()
    chat_session = ChatSession(id=uuid4(), title=None)

    user_message, assistant_message = ChatMessageRepository(db).add_turn(
        session=chat_session,
        question="  What is normalization?  ",
        answer="Normalization organizes data to reduce redundancy.",
    )

    assert db.commit_count == 1
    assert db.rollback_count == 0
    assert [message.role for message in db.added] == ["user", "assistant"]
    assert user_message.content == "What is normalization?"
    assert assistant_message.content == "Normalization organizes data to reduce redundancy."
    assert user_message.created_at < assistant_message.created_at
    assert chat_session.title == "What is normalization?"


def test_add_turn_rolls_back_when_the_commit_fails() -> None:
    db = FakeSession(should_fail=True)
    chat_session = ChatSession(id=uuid4(), title=None)

    with pytest.raises(RuntimeError, match="database write failed"):
        ChatMessageRepository(db).add_turn(
            session=chat_session,
            question="Question",
            answer="Answer",
        )

    assert db.commit_count == 1
    assert db.rollback_count == 1
