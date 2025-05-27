from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.config import CODE_GENERATOR_PROMPT
from app.core.state import app_state


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

참고 문서:
{reference_docs}

원본 코드:
{code}

위 코드를 {toname} {toversion}으로 변환해주세요. 참고 문서의 내용을 활용하여 더 정확하고 최신의 방법으로 변환해주세요.""")
        ])

        # 구조화된 출력을 사용하는 체인 구성
        self.chain = self.conversion_prompt | self.structured_chat

    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        # Redis에서 원본 코드 가져오기
        code = app_state.redis_client.get(input["id"])

        result = self.chain.invoke({
            "code": code,
            "fromname": input["fromname"],
            "fromversion": input["fromversion"],
            "toname": input["toname"],
            "toversion": input["toversion"],
            "reference_docs": input["reference_docs"]
        })

        return {"original_code": code, "transformed_code": result.code}
