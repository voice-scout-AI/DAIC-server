import uuid
from typing import Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.config import EXTRACT_PROMPT
from app.core.state import app_state


class CodeOutput(BaseModel):
    code: str = Field(default=None, description="추출된 순수 코드 내용만 포함")
    description: Optional[str] = Field(default=None, description="코드에 대한 간단한 설명 (선택사항)")


class CodeCleaner(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(schema=CodeOutput)
        self.conversion_prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_PROMPT),
            ("human", "{code}")
        ])

        # 구조화된 출력을 사용하는 체인 구성
        self.chain = self.conversion_prompt | self.structured_chat

    def invoke(self, input: str, config=None) -> Dict[str, Any]:
        result = self.chain.invoke({"code": input})

        id = str(uuid.uuid4())
        app_state.redis_client.set(id, result.code)

        return {"id": id, "code": result.code}
