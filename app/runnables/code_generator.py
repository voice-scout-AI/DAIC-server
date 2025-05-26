from typing import Dict, Any

import redis
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.config import CODE_GENERATOR_PROMPT, REDIS_HOST, REDIS_PORT


class ConvertedCodeOutput(BaseModel):
    code: str = Field(description="변환된 코드")


class CodeGenerator(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(
            schema=ConvertedCodeOutput)
        self.conversion_prompt = ChatPromptTemplate.from_messages([
            ("system", CODE_GENERATOR_PROMPT),
            ("human", """다음 코드를 변환해주세요:

원본 기술: {fromname} {fromversion}
타겟 기술: {toname} {toversion}

원본 코드:
{code}

위 코드를 {toname} {toversion}으로 변환해주세요.""")
        ])

        # 구조화된 출력을 사용하는 체인 구성
        self.chain = self.conversion_prompt | self.structured_chat

    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        code = r.get(input["id"])

        result = self.chain.invoke({
            "code": code,
            "fromname": input["fromname"],
            "fromversion": input["fromversion"],
            "toname": input["toname"],
            "toversion": input["toversion"]
        })

        return {"transformed_code": result.code}


if __name__ == "__main__":
    processor = CodeGenerator()

    result = processor.invoke({
        "id": "10a71804-1558-465c-8696-14b71197d4cf",
        "fromname": "React",
        "fromversion": "18.0.0",
        "toname": "Vue.js",
        "toversion": "3.4.14",
    })

    print("처리 결과 ->")
    print(result['transformed_code'])
