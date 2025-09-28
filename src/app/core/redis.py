from redis.asyncio import Redis

from .config import config

redis = Redis.from_url(config.REDIS_URL, decode_responses=True)
