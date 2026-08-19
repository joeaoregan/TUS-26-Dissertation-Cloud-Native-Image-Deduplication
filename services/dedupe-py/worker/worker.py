import os

from redis import Redis
from rq import Queue, Worker


def main():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    queue_name = os.getenv("QUEUE_NAME", "dedupe-jobs")
    conn = Redis(host=host, port=port)
    q = Queue(queue_name, connection=conn)
    worker = Worker([q], connection=conn)
    worker.work()


if __name__ == "__main__":
    main()
