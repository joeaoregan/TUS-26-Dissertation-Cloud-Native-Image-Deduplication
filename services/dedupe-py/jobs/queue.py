import os

from redis import Redis
from rq import Queue


def get_queue() -> Queue:
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    queue_name = os.getenv("QUEUE_NAME", "dedupe-jobs")
    conn = Redis(host=host, port=port)
    return Queue(queue_name, connection=conn)
