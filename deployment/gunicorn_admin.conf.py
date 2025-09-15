# Gunicorn configuration for admin server
import multiprocessing

# Server socket
bind = "127.0.0.1:5002"
backlog = 2048

# Worker processes - fewer workers for admin as it has less traffic
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = "bfgminer_admin"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn_bfgminer_admin.pid"
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
    print("Starting BFGMiner Admin Server")

def on_exit(server):
    print("Stopping BFGMiner Admin Server")