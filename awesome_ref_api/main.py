from dotenv import load_dotenv
load_dotenv()

import sys
import time
import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path

from database import engine, SessionLocal, Base
from models import User, Reference, Note, Group
from auth_utils import init_default_user
from routers import auth, references, notes, groups, export

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
logger = logging.getLogger("awesomeref")

app = FastAPI(title="AwesomeRef API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    msg = f"{request.method} {request.url.path} -> {response.status_code} ({duration:.0f}ms)"
    logger.info(msg)
    sys.stdout.flush()
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
    status_code = getattr(exc, "status_code", 500)
    if hasattr(exc, "status_code"):
        # HTTPException — safe to return its detail
        detail = getattr(exc, "detail", "Internal server error")
    else:
        detail = "Internal server error"
    return JSONResponse(status_code=status_code, content={"detail": detail})


# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化默认用户
db = SessionLocal()
try:
    init_default_user(db)
finally:
    db.close()

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(references.router, prefix="/api", tags=["references"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(groups.router, prefix="/api", tags=["groups"])
app.include_router(export.router, prefix="/api", tags=["export"])

# 生产模式：服务前端静态文件
dist_dir = Path(__file__).parent.parent / "awesome_ref_frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
