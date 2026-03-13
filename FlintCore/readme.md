YourFramework/
├── core/
│   ├── server.py          # Main team server
│   ├── listener.py        # Socket/HTTP listener
│   ├── agent_manager.py   # Track connected RATs
│   ├── task_manager.py    # Issue and track commands
│   └── crypto.py          # Encryption handling
│
├── listeners/
│   ├── http_listener.py   # HTTP listener
│   ├── https_listener.py  # HTTPS listener
│   └── dns_listener.py    # DNS listener
│
├── modules/
│   ├── shell.py           # Remote shell
│   ├── upload.py          # File upload
│   ├── download.py        # File download
│   ├── screenshot.py      # Screenshot command
│   └── persistence.py     # Persistence commands
│
├── database/
│   ├── db.py              # Database engine
│   └── models.py          # Agent, Task, Result models
│
├── console/
│   ├── cli.py             # Operator CLI
│   └── commands.py        # CLI command handlers
│
└── config.py              # Global config
```