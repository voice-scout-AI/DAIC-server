from typing import List, Dict, Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.callbacks import PromptLoggerCallback
from app.core.decorators import measure_time
from app.core.prompts import ANALYZE_PROMPT


class TechnologyInfo(BaseModel):
    name: str = Field(description="The canonical, standardized name of the technology (e.g., \"React\", \"Python\").")
    type: Literal["language", "framework", "library"] = Field(
        description="The type of the technology, must be one of 'language', 'framework', or 'library'."
    )
    possible_versions: List[str] = Field(
        description="A list of potential versions (e.g., [\"18.2.x\", \"3.10.x\"]). List the most probable or latest compatible versions first, adhering to A.B or A.B.x format as specified in system prompt."
    )


class CodeAnalysisOutput(BaseModel):
    technologies: List[TechnologyInfo] = Field(
        description="A list of TechnologyInfo objects detailing the analyzed technologies.")


class CodeAnalyser(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(schema=CodeAnalysisOutput)

        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYZE_PROMPT),
            ("human",
             "Please analyze the following code snippet to identify the programming languages, frameworks, and libraries used, along with their potential versions. Follow the detailed instructions provided in the system prompt for technology identification, name normalization, version extraction, and output formatting.\n\nCode to analyze:\n{code}")
        ])

        self.chain = self.analysis_prompt | self.structured_chat

    @measure_time
    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        result = self.chain.invoke({"code": input.get('code')}, config={"callbacks": [PromptLoggerCallback()]})

        return {"id": input.get("id"), "tech": result.technologies}
