import logging
import os
import sys
from time import sleep
import redis
from app.utils import log

logger = log.get_logger(__name__)

class RedisQueue(object):
    """Simple Queue with Redis Backend"""
    def __init__(self, name, namespace='queue', **redis_kwargs):
        '''
        With k8s, this should no longer be necessary
        if os.environ.get('CLANENV') == 'prod':
            self.redis_server = 'sfredisprod'
        else:
            self.redis_server = 'sfredis'
        '''

        self.__db = redis.Redis(host="sfredis", port=6379, db=0)
        self.key = '%s:%s' %(namespace, name)

    def ping(self):
        """Ping the redis server."""
        return self.__db.ping()

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue. 

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            item = item[1]
        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

def get_redis_queue(queue_name):
    while True:
        try:
            q = RedisQueue(queue_name)
            q.ping()
            return q
        except Exception:
            logger.warning('Failed to connect to Redis. Retrying in 30 seconds.')
            sleep(30)
            pass
