from datetime import datetime

from FlintCore.src.utils.config_structure import config


class Database:
    def __init__(self,config):
        self.config = config
        self.engine = config['database']['engine']
        self.conn = self._connect()
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
        already_exists = cursor.fetchone() is not None
        agent = cursor.execute('''
                       CREATE TABLE IF NOT EXISTS agents
                       (
                           agent_id
                           TEXT
                           PRIMARY
                           KEY,
                           ip
                           TEXT,
                           hostname
                           TEXT,
                           os
                           TEXT,
                           last_seen
                           TEXT
                       )
                       ''')
        tasks = cursor.execute('''
                       CREATE TABLE IF NOT EXISTS tasks
                       (
                           task_id
                           TEXT
                           PRIMARY
                           KEY,
                           agent_id
                           TEXT,
                           command
                           TEXT,
                           status
                           TEXT,
                           created_at
                           TEXT,
                           FOREIGN
                           KEY
                       (
                           agent_id
                       ) REFERENCES agents
                       (
                           agent_id
                       )
                           )
                       ''')
        self.conn.commit()
        if already_exists:
            print("Tables loaded OK")  # db already existed
        else:
            print("Tables created OK")  # fresh database





    def _connect(self):
        if self.engine == 'sqlite':
            import sqlite3
            return sqlite3.connect(self.config['database']['path'])
        elif self.engine == 'mysql':
            import mysql.connector
            return mysql.connector.connect(...)
        else:
            raise Exception('Database engine not supported')

    def save_agent(self, agent):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO agents (agent_id, ip, hostname, os, last_seen)
            VALUES (?, ?, ?, ?, ?)
        ''', (agent.agent_id, agent.ip, agent.hostname, agent.os, str(agent.last_seen)))
        self.conn.commit()

    def get_agent(self, agent_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM agents WHERE agent_id = ?', (agent_id,))
        return cursor.fetchone()