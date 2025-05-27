import uuid
from typing import Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.callbacks import PromptLoggerCallback
from app.core.decorators import measure_time
from app.core.prompts import EXTRACT_PROMPT
from app.core.state import app_state


class CodeOutput(BaseModel):
    code: str = Field(default=None,
                      description="The extracted and cleaned, pure code string. Non-code text and irrelevant comments should be removed.")
    description: Optional[str] = Field(default=None,
                                       description="A brief, optional summary of the extracted code\'s apparent purpose or functionality, if discernible. Can be omitted if no clear description is inferable or if the input is purely code.")


class CodeCleaner(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(schema=CodeOutput)
        self.conversion_prompt = ChatPromptTemplate.from_messages([
            ("system", EXTRACT_PROMPT),
            ("human", """Please extract and clean the code from the following text, which may be raw OCR output from an image. Focus on isolating runnable code snippets, removing any non-code text, and correcting minor OCR errors if possible, based on the detailed instructions provided in the system prompt.
            
            Text to process:
            {code}""")
        ])

        self.chain = self.conversion_prompt | self.structured_chat

    @measure_time
    def invoke(self, input: str, config=None) -> Dict[str, Any]:
        result = self.chain.invoke({"code": input}, config={"callbacks": [PromptLoggerCallback()]})

        id = str(uuid.uuid4())
        app_state.redis_client.set(id, result.code)

        return {"id": id, "code": result.code}
