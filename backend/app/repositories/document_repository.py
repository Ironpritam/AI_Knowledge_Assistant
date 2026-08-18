from uuid import UUID
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_by_id(self, document_id: UUID) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def get_all(self, document_ids: list[UUID] | None = None) -> list[Document]:
        query = self.db.query(Document)

        if document_ids:
            query = query.filter(Document.id.in_(document_ids))

        return (
            query
            .order_by(Document.created_at.desc())
            .all()
        )

    def update(self, document: Document) -> Document:
        self.db.commit()
        self.db.refresh(document)

        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()
