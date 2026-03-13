# FlintCore/src/models/task_model.py
from sqlalchemy import Column, String, ForeignKey
from FlintCore.src.databasecore.base import Base
from datetime import datetime

class TaskModel(Base):
    __tablename__ = "tasks"
    task_id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.agent_id"))  # links to agents table
    command = Column(String)
    status = Column(String, default="pending")
    created_at = Column(String, default=str(datetime.now()))