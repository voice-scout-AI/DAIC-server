import functools
import time

from langchain_core.runnables import RunnableLambda

from app.core.config import DEBUG


def measure_time(func):
    if not DEBUG:  # 프로덕션 환경에서는 원래 함수를 그대로 반환
        return func

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # 클래스 이름과 메소드 이름을 가져옵니다
        class_name = args[0].__class__.__name__ if args else "Unknown"
        print(f"[🔥🔥🔥🔥{class_name} 실행 시간🔥🔥🔥🔥]:")
        print(f"{end_time - start_time:.2f}초")
        print("=" * 50)

        return result

    return wrapper


def timing_wrapper(name, runnable):
    if not DEBUG:  # 프로덕션 환경에서는 원래 runnable을 그대로 반환
        return runnable

    def wrapped(input):
        start = time.perf_counter()
        result = runnable.invoke(input)
        end = time.perf_counter()
        print(f"[{name}] 실행 시간: {end - start:.3f}초")
        return result

    return RunnableLambda(wrapped)
