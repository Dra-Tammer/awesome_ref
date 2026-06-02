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

from sqlalchemy import text
from database import engine, SessionLocal, Base
from models import User, Reference, Note, Group, StandaloneNote, DailyPlan, DailyTask
from auth_utils import init_default_user
from routers import auth, references, notes, groups, export, standalone_notes, stats, daily_tasks

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

# 自动迁移：添加缺失的列
with engine.begin() as conn:
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'ref' AND COLUMN_NAME = 'pdf_filename'"
    ))
    if result.scalar() == 0:
        conn.execute(text("ALTER TABLE ref ADD COLUMN pdf_filename VARCHAR(255) DEFAULT NULL"))
        print("[migrate] 已添加 ref.pdf_filename 列")

    # standalone_notes 表迁移: content → filename
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'standalone_notes' AND COLUMN_NAME = 'filename'"
    ))
    if result.scalar() == 0:
        conn.execute(text("ALTER TABLE standalone_notes ADD COLUMN filename VARCHAR(255) NOT NULL DEFAULT ''"))
        print("[migrate] 已添加 standalone_notes.filename 列")
    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'standalone_notes' AND COLUMN_NAME = 'content'"
    ))
    if result.scalar() > 0:
        conn.execute(text("ALTER TABLE standalone_notes DROP COLUMN content"))
        print("[migrate] 已移除 standalone_notes.content 列")

    result = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'standalone_notes' AND COLUMN_NAME = 'pinned'"
    ))
    if result.scalar() == 0:
        conn.execute(text("ALTER TABLE standalone_notes ADD COLUMN pinned INT DEFAULT 0"))
        print("[migrate] 已添加 standalone_notes.pinned 列")

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
app.include_router(standalone_notes.router, prefix="/api", tags=["standalone-notes"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(daily_tasks.router, prefix="/api", tags=["daily-tasks"])

# 生产模式：服务前端静态文件
dist_dir = Path(__file__).parent.parent / "awesome_ref_frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
