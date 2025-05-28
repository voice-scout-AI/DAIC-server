from typing import List, Dict, Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.callbacks import PromptLoggerCallback
from app.core.decorators import measure_time
from app.core.prompts import CANDIDATE_FINDER_PROMPT


class SuggestionInfo(BaseModel):
    name: str = Field(description="The canonical, standardized name of the suggested alternative technology.")
    versions: List[str] = Field(
        description="A list of recommended versions for the suggested technology, adhering to system prompt guidelines (e.g., latest/relevant first, ~5-10 versions, A.B or A.B.x format)."
    )


class CandidateOutput(BaseModel):
    id: int = Field(description="The ID of the original technology from the input analysis.")
    type: Literal["language", "framework", "library"] = Field(description="The type of the original technology.")
    suggestions: List[SuggestionInfo] = Field(
        description="A list of SuggestionInfo objects, each representing a viable transformation candidate for the original technology."
    )


class CandidateFinderOutput(BaseModel):
    candidates: List[CandidateOutput] = Field(
        description="A list of CandidateOutput objects, covering all original technologies for which transformation candidates are suggested."
    )


class CandidateFinder(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(
            schema=CandidateFinderOutput
        )

        self.candidate_prompt = ChatPromptTemplate.from_messages([
            ("system", CANDIDATE_FINDER_PROMPT),
            ("human",
             "Based on the following analysis of the current technology stack, please suggest viable transformation candidates. Ensure your output strictly adheres to the JSON schema and guidelines provided in the system prompt.\n\nAnalyzed Technologies:\n{technologies}")
        ])

        self.chain = self.candidate_prompt | self.structured_chat

    @measure_time
    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, List[any]]:
        technologies_str = ""
        for i, tech_info in enumerate(input["tech"]):
            versions_str = ', '.join(tech_info.possible_versions)
            technologies_str += f"ID: {i}, Name: {tech_info.name}, Type: {tech_info.type}, Versions: [{versions_str}]\n"

        result = self.chain.invoke({"technologies": technologies_str}, config={"callbacks": [PromptLoggerCallback()]})

        processed_candidates = []
        if result and result.candidates:
            for candidate_output in result.candidates:
                suggestions_list = []
                if candidate_output.suggestions:
                    for suggestion_info in candidate_output.suggestions:
                        suggestions_list.append({
                            "name": suggestion_info.name,
                            "versions": suggestion_info.versions
                        })
                processed_candidates.append({
                    "id": candidate_output.id,
                    "type": candidate_output.type,
                    "suggestions": suggestions_list
                })

        return {"id": input.get("id"), "from": input.get("tech"), "to": processed_candidates, 'code': input.get("code")}
