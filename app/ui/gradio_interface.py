import os
import shutil

import gradio as gr

from app.services.process_images import ImageProcessorChain
from app.services.transform_code import CodeTransformerChain


class GradioInterface:
    """Gradio 인터페이스를 관리하는 클래스"""

    def __init__(self, upload_directory: str = "./uploads"):
        self.upload_directory = upload_directory

    def process_images_gradio(self, images):
        """Gradio용 이미지 처리 함수"""
        if not images:
            return "이미지를 업로드해주세요.", "", ""

        try:
            # 이미지 파일들을 uploads 디렉토리에 저장
            saved_files = []
            for image in images:
                if hasattr(image, 'name'):
                    # 파일 이름에서 확장자 추출
                    filename = os.path.basename(image.name)
                    file_path = os.path.join(self.upload_directory, filename)

                    # 파일 복사
                    shutil.copy2(image.name, file_path)
                    saved_files.append(file_path)

            # ImageProcessorChain 실행
            result = ImageProcessorChain().invoke(saved_files)

            if "error" in result:
                return f"오류: {result['error']}", "", ""

            # 결과 포맷팅
            extracted_code = result.get('code', '코드를 추출할 수 없습니다.')
            code_id = result.get('id', '')

            # 기술 스택 정보 포맷팅
            tech_info = ""
            if 'from' in result:
                tech_info = "감지된 기술 스택:\n"
                for tech in result['from']:
                    # TechnologyInfo 객체는 Pydantic 모델이므로 속성으로 직접 접근
                    tech_name = getattr(tech, 'name', 'Unknown')
                    tech_type = getattr(tech, 'type', 'Unknown')
                    tech_versions = getattr(tech, 'possible_versions', [])

                    tech_info += f"- {tech_name} ({tech_type})\n"
                    if tech_versions:
                        tech_info += f"  가능한 버전: {', '.join(tech_versions)}\n"

            # 변환 후보 정보 포맷팅
            candidates_info = ""
            if 'to' in result:
                candidates_info = "\n변환 가능한 기술들:"
                for i, candidate in enumerate(result['to']):
                    # 원본 기술 정보 가져오기
                    if i < len(result['from']):
                        from_tech = result['from'][i]
                        from_name = getattr(from_tech, 'name', 'Unknown')
                        from_type = getattr(from_tech, 'type', 'Unknown')
                        candidates_info += f"\n {from_name} ({from_type}) -> \n"

                    # 변환 후보들 (딕셔너리 형태)
                    for suggestion in candidate.get('suggestions', []):
                        candidates_info += f"- {suggestion.get('name', 'Unknown')}\n"
                        if suggestion.get('versions'):
                            candidates_info += f"  버전: {', '.join(suggestion['versions'])}\n"

            full_result = f"코드 ID: {code_id}\n\n{tech_info}{candidates_info}"

            return full_result, extracted_code, code_id

        except Exception as e:
            return f"오류 발생: {str(e)}", "", ""

    def transform_code_gradio(self, code_id, from_tech, from_version, to_tech, to_version):
        """Gradio용 코드 변환 함수"""
        if not all([code_id, from_tech, to_tech]):
            return "코드 ID, 원본 기술, 대상 기술을 모두 입력해주세요."

        try:
            result = CodeTransformerChain().invoke({
                "id": code_id,
                "fromname": from_tech,
                "fromversion": from_version,
                "toname": to_tech,
                "toversion": to_version
            })

            if "error" in result:
                return f"오류: {result['error']}"

            original_code = result.get('original_code', '원본 코드 없음')
            transformed_code = result.get('transformed_code', '변환된 코드 없음')

            return f"원본 코드:\n{original_code}\n\n변환된 코드:\n{transformed_code}"

        except Exception as e:
            return f"오류 발생: {str(e)}"

    def create_gradio_interface(self):
        """Gradio 인터페이스를 생성하는 함수"""
        with gr.Blocks(title="코드 추출 및 변환 테스트", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🖼️ 이미지에서 코드 추출 및 변환 테스트")
            gr.Markdown("이 인터페이스를 통해 이미지에서 코드를 추출하고 다른 기술로 변환할 수 있습니다.")

            with gr.Tab("📸 이미지에서 코드 추출"):
                with gr.Row():
                    with gr.Column():
                        image_input = gr.File(
                            label="이미지 업로드 (여러 개 가능)",
                            file_count="multiple",
                            file_types=["image"]
                        )
                        extract_btn = gr.Button("코드 추출", variant="primary")

                    with gr.Column():
                        result_output = gr.Textbox(
                            label="추출 결과",
                            lines=15,
                            max_lines=20
                        )

                with gr.Row():
                    extracted_code = gr.Textbox(
                        label="추출된 코드",
                        lines=10,
                        visible=False
                    )
                    code_id_output = gr.Textbox(
                        label="코드 ID",
                        visible=False
                    )

            with gr.Tab("🔄 코드 변환"):
                with gr.Row():
                    with gr.Column():
                        code_id_input = gr.Textbox(
                            label="코드 ID",
                            placeholder="위에서 추출한 코드 ID를 입력하세요"
                        )

                        with gr.Row():
                            from_tech = gr.Textbox(
                                label="원본 기술",
                                placeholder="예: React"
                            )
                            from_version = gr.Textbox(
                                label="원본 버전",
                                placeholder="예: 18"
                            )

                        with gr.Row():
                            to_tech = gr.Textbox(
                                label="대상 기술",
                                placeholder="예: Vue"
                            )
                            to_version = gr.Textbox(
                                label="대상 버전",
                                placeholder="예: 3"
                            )

                        transform_btn = gr.Button("코드 변환", variant="primary")

                    with gr.Column():
                        transform_result = gr.Textbox(
                            label="변환 결과",
                            lines=15,
                            max_lines=20
                        )

            with gr.Tab("📋 API 문서"):
                gr.Markdown("""
                ## API 엔드포인트
                
                ### 1. 이미지 업로드 및 코드 추출
                ```
                POST /upload-images/
                Content-Type: multipart/form-data
                
                Body: images (파일 배열)
                ```
                
                ### 2. 코드 변환
                ```
                POST /transform/
                Content-Type: application/json
                
                Body:
                {
                    "id": "코드 ID",
                    "from": {
                        "name": "원본 기술명",
                        "version": "원본 버전"
                    },
                    "to": {
                        "name": "대상 기술명", 
                        "version": "대상 버전"
                    }
                }
                ```
                
                ### 3. 지원되는 기술 예시
                - **프론트엔드**: React, Vue, Angular, Svelte
                - **백엔드**: Node.js, Python, Java, Go
                - **CSS**: Sass, Tailwind CSS, styled-components
                - **상태관리**: Redux, Zustand, Vuex
                - **기타**: TypeScript, JavaScript, Docker, Kubernetes
                
                ### 4. 사용 방법
                1. **이미지 업로드** 탭에서 코드가 포함된 이미지를 업로드
                2. **코드 추출** 버튼을 클릭하여 코드와 기술 스택 분석
                3. **코드 변환** 탭에서 원본/대상 기술 정보 입력
                4. **코드 변환** 버튼을 클릭하여 변환된 코드 확인
                """)

            # 이벤트 핸들러
            extract_btn.click(
                fn=self.process_images_gradio,
                inputs=[image_input],
                outputs=[result_output, extracted_code, code_id_output]
            )

            # 코드 ID를 자동으로 복사
            code_id_output.change(
                fn=lambda x: x,
                inputs=[code_id_output],
                outputs=[code_id_input]
            )

            transform_btn.click(
                fn=self.transform_code_gradio,
                inputs=[code_id_input, from_tech, from_version, to_tech, to_version],
                outputs=[transform_result]
            )

        return demo


def create_gradio_app(upload_directory: str = "./uploads"):
    """Gradio 앱을 생성하는 팩토리 함수"""
    interface = GradioInterface(upload_directory)
    return interface.create_gradio_interface()
