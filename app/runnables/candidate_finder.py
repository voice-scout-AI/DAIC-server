from typing import List, Dict, Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.callbacks import PromptLoggerCallback
from app.core.config import CANDIDATE_FINDER_PROMPT, DEBUG
from app.core.decorators import measure_time


class SuggestionInfo(BaseModel):
    name: str = Field(description="제안하는 기술의 이름")
    versions: List[str] = Field(description="권장 버전들의 리스트, 최신 버전부터 나열, 가능하다면 10개 정도 추천해주면 좋아.")


class CandidateOutput(BaseModel):
    id: int = Field(description="원본 기술의 ID")
    type: Literal["language", "framework", "library"] = Field(description="기술의 타입")
    suggestions: List[SuggestionInfo] = Field(description="변환 가능한 기술들의 리스트")


class CandidateFinderOutput(BaseModel):
    candidates: List[CandidateOutput] = Field(description="모든 기술에 대한 변환 후보들")


class CandidateFinder(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(
            schema=CandidateFinderOutput)

        self.candidate_prompt = ChatPromptTemplate.from_messages([
            ("system", CANDIDATE_FINDER_PROMPT),
            ("human", "다음 기술 분석 결과를 바탕으로 변환 가능한 기술들을 제안해주세요:\n\n{technologies}")
        ])

        self.chain = self.candidate_prompt | self.structured_chat

    @measure_time
    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, List[any]]:
        technologies_str = ""
        for tech in input["tech"]:
            technologies_str += f"ID: {tech['id']}, Name: {tech['name']}, Type: {tech['type']}, Versions: {tech['possible_versions']}\n"

        result = self.chain.invoke({"technologies": technologies_str}, config={"callbacks": [PromptLoggerCallback()]})

        candidates = []
        for candidate in result.candidates:
            suggestions = []
            for suggestion in candidate.suggestions:
                suggestions.append({
                    "name": suggestion.name,
                    "versions": suggestion.versions
                })

            candidates.append({
                "id": candidate.id,
                "type": candidate.type,
                "suggestions": suggestions
            })

        return {"id": input["id"], "from": input["tech"], "to": candidates}
