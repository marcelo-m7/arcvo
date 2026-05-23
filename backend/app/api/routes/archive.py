from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_admin
from app.integrations.odoo.client import OdooClientError
from app.integrations.youtube import YouTubeUrlError, fetch_youtube_metadata
from app.schemas.archive import (
    ArchiveCourse,
    ArchiveCourseCreate,
    ArchiveDashboard,
    ArchiveVideo,
    YouTubePreview,
    YouTubePreviewRequest,
    YouTubeVideoCreate,
    YouTubeVideoUpdate,
)
from app.services.archive_service import ArchiveService, get_archive_service

router = APIRouter(dependencies=[Depends(require_admin)])
archive_service_dependency = Depends(get_archive_service)


@router.get("/dashboard", response_model=ArchiveDashboard)
def dashboard(service: ArchiveService = archive_service_dependency) -> ArchiveDashboard:
    try:
        return service.dashboard()
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/courses", response_model=list[ArchiveCourse])
def list_courses(service: ArchiveService = archive_service_dependency) -> list[ArchiveCourse]:
    try:
        return service.list_courses()
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/courses", response_model=ArchiveCourse)
def create_course(
    payload: ArchiveCourseCreate,
    service: ArchiveService = archive_service_dependency,
) -> ArchiveCourse:
    try:
        return service.create_course(name=payload.name, publish=payload.publish)
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/youtube/preview", response_model=YouTubePreview)
async def preview_youtube(payload: YouTubePreviewRequest) -> YouTubePreview:
    try:
        metadata = await fetch_youtube_metadata(payload.url)
    except YouTubeUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return YouTubePreview(**metadata.__dict__)


@router.get("/youtube/videos", response_model=list[ArchiveVideo])
def list_videos(service: ArchiveService = archive_service_dependency) -> list[ArchiveVideo]:
    try:
        return service.list_videos()
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/youtube/videos", response_model=ArchiveVideo)
def create_youtube_video(
    payload: YouTubeVideoCreate,
    service: ArchiveService = archive_service_dependency,
) -> ArchiveVideo:
    try:
        return service.create_youtube_video(
            url=payload.url,
            course_name=payload.course_name,
            title=payload.title,
            description=payload.description,
            publish=payload.publish,
            tags=payload.tags,
        )
    except YouTubeUrlError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/youtube/videos/{video_id}", response_model=ArchiveVideo)
def update_youtube_video(
    video_id: int,
    payload: YouTubeVideoUpdate,
    service: ArchiveService = archive_service_dependency,
) -> ArchiveVideo:
    try:
        return service.update_video(
            video_id=video_id,
            title=payload.title,
            description=payload.description,
            publish=payload.publish,
            tags=payload.tags,
        )
    except OdooClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
