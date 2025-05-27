from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_upstage import ChatUpstage
from pydantic import BaseModel, Field

from app.core.callbacks import PromptLoggerCallback
from app.core.decorators import measure_time
from app.core.prompts import CODE_GENERATOR_PROMPT
from app.core.state import app_state


class ConvertedCodeOutput(BaseModel):
    code: str = Field(
        description="The transformed source code snippet converted to the target technology, maintaining functional equivalence while following target technology best practices and conventions")


class CodeGenerator(Runnable):
    def __init__(self):
        self.structured_chat = ChatUpstage(model="solar-pro2-preview").with_structured_output(
            schema=ConvertedCodeOutput)
        self.conversion_prompt = ChatPromptTemplate.from_messages([
            ("system", CODE_GENERATOR_PROMPT),
            ("human", """Please transform the following code snippet:

Source Technology: {fromname} {fromversion}
Target Technology: {toname} {toversion}

Reference Documentation:
{reference_docs}

Original Code:
{code}

Convert this code to {toname} {toversion} while ensuring:
1. Functional equivalence is preserved
2. Target technology best practices and idiomatic patterns are followed
3. Version-specific features and APIs of {toversion} are utilized appropriately
4. All necessary dependencies and imports are included
5. Reference documentation insights are incorporated for optimal conversion

Provide only the raw transformed code without any markdown formatting or explanatory text.""")
        ])

        self.chain = self.conversion_prompt | self.structured_chat

    @measure_time
    def invoke(self, input: Dict[str, Any], config=None) -> Dict[str, Any]:
        code = app_state.redis_client.get(input["id"])

        result = self.chain.invoke({
            "code": code,
            "fromname": input["fromname"],
            "fromversion": input["fromversion"],
            "toname": input["toname"],
            "toversion": input["toversion"],
            "reference_docs": input["reference_docs"]
        }, config={"callbacks": [PromptLoggerCallback()]})

        return {"original_code": code, "transformed_code": result.code}
