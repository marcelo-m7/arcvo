from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import require_admin
from app.integrations.odoo.client import OdooClientError
from app.schemas.knowledge import (
    KnowledgeArticle,
    KnowledgeArticleCreate,
    KnowledgeArticleTransition,
    KnowledgeArticleUpdate,
    KnowledgeCategory,
    KnowledgeCategoryCreate,
)
from app.services.knowledge_service import KnowledgeService, get_knowledge_service

router = APIRouter(dependencies=[Depends(require_admin)])
knowledge_service_dependency = Depends(get_knowledge_service)


@router.get("/categories", response_model=list[KnowledgeCategory])
def list_categories(
    limit: int = Query(default=100, ge=1, le=300),
    service: KnowledgeService = knowledge_service_dependency,
) -> list[KnowledgeCategory]:
    try:
        return service.list_categories(limit=limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/categories", response_model=KnowledgeCategory)
def create_category(
    payload: KnowledgeCategoryCreate,
    service: KnowledgeService = knowledge_service_dependency,
) -> KnowledgeCategory:
    try:
        return service.create_category(payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/articles", response_model=list[KnowledgeArticle])
def list_articles(
    state: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    service: KnowledgeService = knowledge_service_dependency,
) -> list[KnowledgeArticle]:
    try:
        return service.list_articles(state=state, limit=limit)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/articles/{article_id}", response_model=KnowledgeArticle)
def get_article(
    article_id: int,
    service: KnowledgeService = knowledge_service_dependency,
) -> KnowledgeArticle:
    try:
        article = service.get_article(article_id)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/articles", response_model=KnowledgeArticle)
def create_article(
    payload: KnowledgeArticleCreate,
    service: KnowledgeService = knowledge_service_dependency,
) -> KnowledgeArticle:
    try:
        return service.create_article(payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/articles/{article_id}", response_model=KnowledgeArticle)
def update_article(
    article_id: int,
    payload: KnowledgeArticleUpdate,
    service: KnowledgeService = knowledge_service_dependency,
) -> KnowledgeArticle:
    try:
        return service.update_article(article_id, payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/articles/{article_id}/transition", response_model=KnowledgeArticle)
def transition_article(
    article_id: int,
    payload: KnowledgeArticleTransition,
    service: KnowledgeService = knowledge_service_dependency,
) -> KnowledgeArticle:
    try:
        return service.transition_article(article_id, payload)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
