# Gunicorn configuration for main application
import multiprocessing

# Server socket
bind = "127.0.0.1:5001"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = "bfgminer_main"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn_bfgminer_main.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"
loglevel = "info"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server hooks
def on_starting(server):
    print("Starting BFGMiner Main Application")

def on_exit(server):
    print("Stopping BFGMiner Main Application")