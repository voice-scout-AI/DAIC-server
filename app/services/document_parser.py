import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_upstage import ChatUpstage
from langchain_upstage import UpstageDocumentParseLoader

from app.core.config import UPSTAGE_API_KEY, SYSTEM_PROMPT

os.environ["UPSTAGE_API_KEY"] = UPSTAGE_API_KEY
file_path = "../statics/test_img_0.png"  # ex: ./image.png

loader = UpstageDocumentParseLoader(file_path, ocr="force", output_format="text", coordinates=False)
chat = ChatUpstage(model="solar-pro2-preview")

pages = loader.load()
for page in pages:
    print(page)

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        HumanMessage(
            content=page.page_content
        )
    ]

    response = chat.invoke(messages)
    print(response)
