from datetime import datetime
import uuid

class Task:
    def __init__(self, agent_id, command):
        self.task_id = str(uuid.uuid4())  # auto generate unique id
        self.agent_id = agent_id
        self.command = command
        self.status = "pending"
        self.created_at = datetime.now()