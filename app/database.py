from datetime import datetime
from sqlalchemy import create_engine, String, Text, ForeignKey, Integer, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from .config import settings

class Base(DeclarativeBase): pass
engine = create_engine(settings.database_url, connect_args={'check_same_thread': False} if settings.database_url.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
class User(Base):
    __tablename__='users'; id: Mapped[int]=mapped_column(primary_key=True); username: Mapped[str]=mapped_column(String(64), unique=True); password_hash: Mapped[str]=mapped_column(String(255)); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Project(Base):
    __tablename__='projects'; id: Mapped[int]=mapped_column(primary_key=True); owner_id: Mapped[int]=mapped_column(ForeignKey('users.id')); name: Mapped[str]=mapped_column(String(120)); slug: Mapped[str]=mapped_column(String(120), unique=True); workspace_path: Mapped[str]=mapped_column(String(500)); branch: Mapped[str]=mapped_column(String(150)); status: Mapped[str]=mapped_column(String(40), default='ready'); current_task: Mapped[str]=mapped_column(Text, default=''); demo_url: Mapped[str|None]=mapped_column(String(300), nullable=True); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow); owner: Mapped[User]=relationship()
class Run(Base):
    __tablename__='runs'; id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey('projects.id')); request: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(40)); iteration: Mapped[int]=mapped_column(Integer, default=0); summary: Mapped[str]=mapped_column(Text, default=''); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Event(Base):
    __tablename__='events'; id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey('projects.id')); run_id: Mapped[int|None]=mapped_column(ForeignKey('runs.id'), nullable=True); agent: Mapped[str]=mapped_column(String(32)); kind: Mapped[str]=mapped_column(String(50)); message: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class TestRun(Base):
    __tablename__='test_runs'; id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey('projects.id')); run_id: Mapped[int]=mapped_column(ForeignKey('runs.id')); status: Mapped[str]=mapped_column(String(20)); total: Mapped[int]=mapped_column(Integer); passed: Mapped[int]=mapped_column(Integer); output: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class Checkpoint(Base):
    __tablename__='checkpoints'; id: Mapped[int]=mapped_column(primary_key=True); project_id: Mapped[int]=mapped_column(ForeignKey('projects.id')); description: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(20)); test_count: Mapped[int]=mapped_column(Integer); passed_tests: Mapped[int]=mapped_column(Integer); commit_hash: Mapped[str|None]=mapped_column(String(64), nullable=True); branch: Mapped[str]=mapped_column(String(150)); pushed: Mapped[bool]=mapped_column(Boolean, default=False); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
def init_db(): Base.metadata.create_all(engine)
