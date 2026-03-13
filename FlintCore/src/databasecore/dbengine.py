from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from FlintCore.src.databasecore.Models.agent_model import AgentModel
from FlintCore.src.databasecore.Models.task_model import TaskModel
from FlintCore.src.databasecore.base import Base


class Database:
    def __init__(self, config):
        self.config = config
        self.engine = create_engine("sqlite:///" + config['database']['path'])
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)  # replaces entire create_tables method
        print("Tables OK")

    def save_agent(self, agent):
        session = self.SessionLocal()
        db_agent = AgentModel(
            agent_id=agent.agent_id,
            ip=agent.ip,
            hostname=agent.hostname,
            os=agent.os,
            last_seen=str(agent.last_seen)
        )
        session.add(db_agent)
        session.commit()
        session.close()

    def get_agent(self, agent_id):
        session = self.SessionLocal()
        result = session.query(AgentModel).filter(AgentModel.agent_id == agent_id).first()
        session.close()
        return result

    def save_task(self, task):
        session = self.SessionLocal()
        db_task = TaskModel(
            task_id=task.task_id,
            agent_id=task.agent_id,
            command=task.command,
            status=task.status,
            created_at=str(task.created_at)
        )
        session.add(db_task)
        session.commit()
        session.close()