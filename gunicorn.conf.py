import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120