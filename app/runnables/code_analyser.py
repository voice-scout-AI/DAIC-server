from typing import List, Dict, Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.callbacks import PromptLoggerCallback
from app.core.config import ANALYZE_PROMPT
from app.core.decorators import measure_time


class TechnologyInfo(BaseModel):
    name: str = Field(description="기술의 이름")
    type: Literal["language", "framework", "library"] = Field(
        description="기술의 타입, (language, framework, library) 중 하나를 골라야 함.")
    possible_versions: List[str] = Field(description="가능한 버전들의 리스트, 여러 개일 경우 가장 최근 버전이 먼저 오는 순서")


class CodeAnalysisOutput(BaseModel):
    technologies: List[TechnologyInfo] = Field(description="분석된 기술들의 리스트")


class CodeAnalyser(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(schema=CodeAnalysisOutput)

        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYZE_PROMPT),
            ("human", "다음 코드를 분석해주세요:\n\n{code}")
        ])

        self.chain = self.analysis_prompt | self.structured_chat

    @measure_time
    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        result = self.chain.invoke({"code": input['code']}, config={"callbacks": [PromptLoggerCallback()]})

        technologies = []
        for i, tech in enumerate(result.technologies):
            technologies.append({
                "id": i,
                "name": tech.name,
                "type": tech.type,
                "possible_versions": tech.possible_versions
            })

        return {"id": input["id"], "tech": technologies}
