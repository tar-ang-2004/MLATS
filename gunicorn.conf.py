# Gunicorn Configuration File
# Production-ready WSGI server configuration

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'ats-resume-checker'

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Preload application code before the worker processes are forked
preload_app = True

# Restart workers if they haven't handled a request in this many seconds
timeout = 30

# Workers silent for more than this many seconds are killed and restarted
graceful_timeout = 30

# Timeout for graceful workers restart
graceful_timeout = 30