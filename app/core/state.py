from typing import Optional

import redis

from app.core.config import REDIS_HOST, REDIS_PORT
from app.rag.vector_store import VectorStore


class AppState:
    _instance = None
    _redis_client: Optional[redis.Redis] = None
    _vector_store = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
        return cls._instance

    def initialize_redis(self):
        self._redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        print("redis 로드 성공")

    def initialize_vector_store(self):
        self._vector_store = VectorStore().vector_store
        print("vector store 로드 성공")

    @property
    def redis_client(self) -> redis.Redis:
        if self._redis_client is None:
            raise RuntimeError("Redis client가 초기화되지 않았습니다.")
        return self._redis_client

    @property
    def vector_store(self):
        if self._vector_store is None:
            raise RuntimeError("Vector store가 초기화되지 않았습니다.")
        return self._vector_store

    def close_redis(self):
        if self._redis_client:
            self._redis_client.close()


# 전역 상태 인스턴스
app_state = AppState()
