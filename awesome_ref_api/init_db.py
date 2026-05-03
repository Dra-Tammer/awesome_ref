"""重建数据库表并创建默认用户"""
from sqlalchemy import text
from database import engine, SessionLocal, Base
from models import User, Reference, Note, Group, ref_group_assoc
from auth_utils import init_default_user

print("Dropping all tables...")
with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
Base.metadata.drop_all(bind=engine)
with engine.begin() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
print("Creating all tables...")
Base.metadata.create_all(bind=engine)
print("Creating default users...")

db = SessionLocal()
try:
    init_default_user(db)
    print("Done! Users created:")
    for u in db.query(User).all():
        print(f"  - {u.username}")
finally:
    db.close()
