from fastapi import HTTPException
from fastapi.routing import APIRouter

from app.core.success_response import success_response
from app.db.db_config import check_mysql_connection
from app.db.redis_config import check_redis_connection

health_router = APIRouter(prefix="/health")

@health_router.get("/live", tags=["健康检查"], summary="健康检查")
async def get_health_application_status():
    """健康检查-存活"""
    return success_response(
        message="health application status",
        data={
            "status": "ok"
        }
    )

@health_router.get("/ready", tags=["健康检查"], summary="健康检查")
async def get_health_readiness():
    """健康检查-就绪"""
    # 检查mysql连接
    mysql_status = await check_mysql_connection()
    # 检查redis连接
    redis_status = await check_redis_connection()
    if mysql_status and redis_status:
        return success_response(
            message="health readiness status",
            data={
                "status": "ok"
            }
        )
    else:
        raise HTTPException(status_code=503, detail="MySQL或Redis连接失败")

