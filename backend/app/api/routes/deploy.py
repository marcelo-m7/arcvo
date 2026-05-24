from fastapi import APIRouter, Depends

from app.core.security import require_admin
from app.schemas.deploy import CoolifyDeployResult, ProductionStatus
from app.services.deploy_service import DeployService, get_deploy_service

router = APIRouter(dependencies=[Depends(require_admin)])
deploy_service_dependency = Depends(get_deploy_service)


@router.get("/coolify/status", response_model=ProductionStatus)
async def coolify_status(service: DeployService = deploy_service_dependency) -> ProductionStatus:
    return await service.status()


@router.post("/coolify", response_model=CoolifyDeployResult)
async def trigger_coolify(
    service: DeployService = deploy_service_dependency,
) -> CoolifyDeployResult:
    return await service.trigger_coolify()
