from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routers.chat import router as chat_router
from api.routers.healthcheck import router as healthcheck_router 

from api.core.logger import APILogger
from middleware.cors import add_cors_middleware

logger = APILogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FastAPI 서버 시작")
    yield
    # Shutdown
    logger.info("FastAPI 서버 종료")


def create_app():
    app = FastAPI(
        title="Quick Agent POC API",
        description="Azure OpenAI 기반 채팅 API",
        version="0.1.0",
        lifespan=lifespan
    )
    # CORS 설정 - Frontend와 통신 허용
    add_cors_middleware(app)

    # 라우터 등록
    app.include_router(chat_router, prefix="/api", tags=["chat"])
    app.include_router(healthcheck_router, prefix="/api", tags=["healthcheck"])
    return app

app = create_app()
