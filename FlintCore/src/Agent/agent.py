from datetime import datetime


class Agent:
    def __init__(self, agent_id, ip, hostname, os):
        self.agent_id = agent_id
        self.ip = ip
        self.hostname = hostname
        self.os = os
        self.last_seen = datetime.now()