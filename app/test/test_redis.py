import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
print(r.get("10a71804-1558-465c-8696-14b71197d4cf"))
