from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

ref_group_assoc = Table(
    "ref_group_assoc",
    Base.metadata,
    Column("ref_id", Integer, ForeignKey("ref.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    references = relationship("Reference", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="user", cascade="all, delete-orphan")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_key = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="groups")
    references = relationship("Reference", secondary=ref_group_assoc, back_populates="groups")

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_group_name"),
        UniqueConstraint("user_id", "group_key", name="uq_user_group_key"),
    )


class Reference(Base):
    __tablename__ = "ref"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ref_key = Column(String(100), nullable=False, index=True)
    ref_type = Column(String(10), default="")
    title = Column(Text, default="")
    authors_json = Column(Text, default="[]")
    year = Column(String(10), default="")
    journal = Column(Text, default="")
    volume = Column(String(20), default="")
    issue = Column(String(20), default="")
    pages = Column(String(30), default="")
    abstract = Column(Text, default="")
    doi = Column(Text, default="")
    keywords_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True, default=None, index=True)

    user = relationship("User", back_populates="references")
    groups = relationship("Group", secondary=ref_group_assoc, back_populates="references")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ref_key = Column(String(100), nullable=False, index=True)
    content = Column(Text, default="")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notes")
