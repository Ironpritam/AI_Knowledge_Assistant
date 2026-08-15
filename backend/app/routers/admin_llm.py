from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models.llm_model import LLMModel
from app.repositories.llm_repository import LLMRepository
from app.schemas.llm import (LLMAdminModelResponse,
    LLMModelCreateRequest,
    LLMModelUpdateRequest,
)

router = APIRouter(
    prefix="/api/v1/admin/llm/models",
    tags=["Admin LLM"],
)


@router.post("", response_model=LLMAdminModelResponse, status_code=status.HTTP_201_CREATED)
def register_model(
    payload: LLMModelCreateRequest,
    db: Session = Depends(get_db),
):
    repo = LLMRepository(db)
    if repo.get_by_id(payload.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Model with id '{payload.id}' already exists.",
        )

    model = LLMModel(
        id=payload.id,
        provider=payload.provider,
        model_name=payload.model_name,
        label=payload.label,
        description=payload.description,
        is_enabled=payload.is_enabled,
        is_default=payload.is_default,
    )
    return repo.create(model)


@router.get("", response_model=list[LLMAdminModelResponse])
def list_registered_models(db: Session = Depends(get_db),):
    return LLMRepository(db).get_all()


@router.get("/{model_id:path}", response_model=LLMAdminModelResponse)
def get_registered_model(model_id: str,db: Session = Depends(get_db),):
    model = LLMRepository(db).get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
    return model


@router.patch("/{model_id:path}", response_model=LLMAdminModelResponse)
def update_registered_model(
    model_id: str,
    payload: LLMModelUpdateRequest,
    db: Session = Depends(get_db),
):
    repo = LLMRepository(db)
    updated = repo.update(
        model_id=model_id,
        **payload.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found.")
    return updated


@router.delete("/{model_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_registered_model(model_id: str,db: Session = Depends(get_db),):
    deleted = LLMRepository(db).delete(model_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Model not found.")
    return None
