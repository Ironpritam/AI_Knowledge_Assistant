from sqlalchemy.orm import Session

from app.models.llm_model import LLMModel


class LLMRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, model_id: str) -> LLMModel | None:
        return self.db.query(LLMModel).filter(LLMModel.id == model_id).first()

    def get_all(self, enabled_only: bool = False) -> list[LLMModel]:
        query = self.db.query(LLMModel)
        if enabled_only:
            query = query.filter(LLMModel.is_enabled.is_(True))
        return query.order_by(LLMModel.created_at.asc()).all()

    def get_default(self) -> LLMModel | None:
        return self.db.query(LLMModel).filter(LLMModel.is_default.is_(True)).first()

    def create(self, model: LLMModel) -> LLMModel:
        if model.is_default:
            self._unset_default()
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def update(self, model_id: str, **kwargs) -> LLMModel | None:
        model = self.get_by_id(model_id)
        if not model:
            return None

        if kwargs.get("is_default"):
            self._unset_default(exclude_id=model_id)

        for key, value in kwargs.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)
        return model

    def delete(self, model_id: str) -> bool:
        model = self.get_by_id(model_id)
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def _unset_default(self, exclude_id: str | None = None) -> None:
        query = self.db.query(LLMModel).filter(LLMModel.is_default.is_(True))
        if exclude_id:
            query = query.filter(LLMModel.id != exclude_id)
        query.update({"is_default": False})
