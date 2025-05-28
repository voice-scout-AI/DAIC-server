import os
import shutil

import gradio as gr

from app.services.process_images import ImageProcessorChain
from app.services.transform_code import CodeTransformerChain


class GradioInterface:
    """Gradio 인터페이스를 관리하는 클래스"""

    def __init__(self, upload_directory: str = "./uploads"):
        self.upload_directory = upload_directory
        self.extracted_data = {}  # 추출된 기술 스택 정보를 저장

    def parse_tech_data(self, result):
        """추출 결과에서 기술 스택 정보를 파싱"""
        tech_options = {}
        candidate_options = {}

        # 원본 기술 스택 파싱
        if 'from' in result:
            for tech in result['from']:
                tech_name = getattr(tech, 'name', 'Unknown')
                tech_versions = getattr(tech, 'possible_versions', [])
                tech_options[tech_name] = tech_versions

        # 변환 후보 파싱
        if 'to' in result and 'from' in result:
            for i, candidate in enumerate(result['to']):
                if i < len(result['from']):
                    from_tech = result['from'][i]
                    from_name = getattr(from_tech, 'name', 'Unknown')

                    candidate_options[from_name] = {}
                    for suggestion in candidate.get('suggestions', []):
                        tech_name = suggestion.get('name', 'Unknown')
                        versions = suggestion.get('versions', [])
                        candidate_options[from_name][tech_name] = versions

        return tech_options, candidate_options

    def update_from_version_dropdown(self, selected_tech):
        """선택한 원본 기술에 따라 버전 드롭다운 업데이트"""
        if selected_tech and hasattr(self, 'extracted_data') and selected_tech in self.extracted_data.get(
                'tech_options', {}):
            versions = self.extracted_data['tech_options'][selected_tech]
            return gr.Dropdown(choices=versions, value=versions[0] if versions else None, visible=True)
        return gr.Dropdown(choices=[], value=None, visible=True)

    def update_to_tech_dropdown(self, selected_from_tech):
        """선택한 원본 기술에 따라 대상 기술 드롭다운 업데이트"""
        if (selected_from_tech and hasattr(self, 'extracted_data') and
                selected_from_tech in self.extracted_data.get('candidate_options', {})):
            candidates = list(self.extracted_data['candidate_options'][selected_from_tech].keys())
            return gr.Dropdown(choices=candidates, value=candidates[0] if candidates else None, visible=True)
        return gr.Dropdown(choices=[], value=None, visible=True)

    def update_to_version_dropdown(self, selected_from_tech, selected_to_tech):
        """선택한 대상 기술에 따라 대상 버전 드롭다운 업데이트"""
        if (selected_from_tech and selected_to_tech and hasattr(self, 'extracted_data') and
                selected_from_tech in self.extracted_data.get('candidate_options', {}) and
                selected_to_tech in self.extracted_data['candidate_options'][selected_from_tech]):
            versions = self.extracted_data['candidate_options'][selected_from_tech][selected_to_tech]
            return gr.Dropdown(choices=versions, value=versions[0] if versions else None, visible=True)
        return gr.Dropdown(choices=[], value=None, visible=True)

    def update_from_tech_and_dependent_dropdowns(self, selected_tech):
        """원본 기술 선택 시 모든 관련 드롭다운들을 한번에 업데이트"""
        if not selected_tech or not hasattr(self, 'extracted_data'):
            return (
                gr.Dropdown(choices=[], value=None, visible=True),  # from_version
                gr.Dropdown(choices=[], value=None, visible=True),  # to_tech
                gr.Dropdown(choices=[], value=None, visible=True)  # to_version
            )

        # 원본 버전 업데이트
        from_versions = self.extracted_data.get('tech_options', {}).get(selected_tech, [])
        from_version_dropdown = gr.Dropdown(
            choices=from_versions,
            value=from_versions[0] if from_versions else None,
            visible=True
        )

        # 대상 기술 업데이트
        to_tech_options = list(self.extracted_data.get('candidate_options', {}).get(selected_tech, {}).keys())
        first_to_tech = to_tech_options[0] if to_tech_options else None
        to_tech_dropdown = gr.Dropdown(
            choices=to_tech_options,
            value=first_to_tech,
            visible=True
        )

        # 대상 버전 업데이트
        to_versions = []
        if first_to_tech and selected_tech in self.extracted_data.get('candidate_options', {}):
            to_versions = self.extracted_data['candidate_options'][selected_tech].get(first_to_tech, [])

        to_version_dropdown = gr.Dropdown(
            choices=to_versions,
            value=to_versions[0] if to_versions else None,
            visible=True
        )

        return from_version_dropdown, to_tech_dropdown, to_version_dropdown

    def update_dropdowns_from_result(self, result_text, extracted_code, code_id):
        """추출 결과로부터 드롭다운들을 업데이트"""
        # 결과가 있고 코드 ID가 있으면 드롭다운 옵션들을 업데이트
        if code_id and hasattr(self, 'last_result'):
            tech_options, candidate_options = self.parse_tech_data(self.last_result)
            self.extracted_data = {
                'tech_options': tech_options,
                'candidate_options': candidate_options
            }

            # 첫 번째 기술 선택
            first_tech = list(tech_options.keys())[0] if tech_options else None
            first_tech_versions = tech_options.get(first_tech, []) if first_tech else []
            first_version = first_tech_versions[0] if first_tech_versions else None

            # 첫 번째 대상 기술 선택
            first_to_techs = list(candidate_options.get(first_tech, {}).keys()) if first_tech and candidate_options.get(
                first_tech) else []
            first_to_tech = first_to_techs[0] if first_to_techs else None
            first_to_versions = candidate_options.get(first_tech, {}).get(first_to_tech,
                                                                          []) if first_tech and first_to_tech else []
            first_to_version = first_to_versions[0] if first_to_versions else None

            return (
                result_text, extracted_code, code_id,
                gr.Dropdown(choices=list(tech_options.keys()), value=first_tech, visible=True),
                gr.Dropdown(choices=first_tech_versions, value=first_version, visible=True),
                gr.Dropdown(choices=first_to_techs, value=first_to_tech, visible=True),
                gr.Dropdown(choices=first_to_versions, value=first_to_version, visible=True)
            )

        return (
            result_text, extracted_code, code_id,
            gr.Dropdown(choices=[], value=None, visible=True),
            gr.Dropdown(choices=[], value=None, visible=True),
            gr.Dropdown(choices=[], value=None, visible=True),
            gr.Dropdown(choices=[], value=None, visible=True)
        )

    def process_images_gradio(self, images):
        if not images:
            return "이미지를 업로드해주세요.", "", "", gr.Dropdown(), gr.Dropdown(), gr.Dropdown(), gr.Dropdown()

        try:
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
            self.last_result = result  # 결과 저장
            print(result)

            if "error" in result:
                return f"오류: {result['error']}", "", "", gr.Dropdown(), gr.Dropdown(), gr.Dropdown(), gr.Dropdown()

            # 결과 포맷팅
            extracted_code = result.get('code', '코드를 추출할 수 없습니다.')
            code_id = result.get('id', '')

            # 기술 스택 정보 포맷팅 (일반 텍스트 스타일)
            tech_info = ""
            if 'from' in result:
                tech_info = "감지된 기술 후보:\n\n"
                for i, tech in enumerate(result['from']):
                    tech_name = getattr(tech, 'name', 'Unknown')
                    tech_type = getattr(tech, 'type', 'Unknown')
                    tech_versions = getattr(tech, 'possible_versions', [])

                    tech_info += f"{i + 1}. {tech_name}\n"
                    tech_info += f"   - 분류: {tech_type}\n"
                    if tech_versions:
                        tech_info += f"   - 버전: {', '.join(tech_versions)}\n\n"
                    else:
                        tech_info += "\n"

            # 변환 후보 정보 포맷팅 (일반 텍스트 스타일)
            candidates_info = ""
            if 'to' in result:
                candidates_info = "변환 가능한 기술 후보:\n\n"
                for i, candidate in enumerate(result['to']):
                    # 원본 기술 정보 가져오기
                    if i < len(result['from']):
                        from_tech = result['from'][i]
                        from_name = getattr(from_tech, 'name', 'Unknown')
                        from_type = getattr(from_tech, 'type', 'Unknown')
                        candidates_info += f"{i + 1}. {from_name} ({from_type}) → \n\n"

                    # 변환 후보들 (딕셔너리 형태)
                    for suggestion in candidate.get('suggestions', []):
                        tech_name = suggestion.get('name', 'Unknown')
                        versions = suggestion.get('versions', [])
                        candidates_info += f"   • {tech_name}\n"
                        if versions:
                            candidates_info += f"     버전: {', '.join(versions)}\n\n"
                        else:
                            candidates_info += "\n"

            full_result = f"코드 ID: {code_id}\n\n{tech_info}{candidates_info}"

            return self.update_dropdowns_from_result(full_result, extracted_code, code_id)

        except Exception as e:
            return f"오류 발생: {str(e)}", "", "", gr.Dropdown(), gr.Dropdown(), gr.Dropdown(), gr.Dropdown()

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

            return [original_code, transformed_code]

        except Exception as e:
            return f"오류 발생: {str(e)}"

    def create_gradio_interface(self):
        with gr.Blocks(title="코드 추출 및 변환 테스트") as demo:
            gr.Markdown("# 이미지에서 코드 추출 및 변환 테스트")
            gr.Markdown("이 인터페이스를 통해 이미지에서 코드를 추출하고 다른 기술로 변환할 수 있습니다.")

            with gr.Tab("이미지에서 코드 추출"):
                with gr.Row():
                    with gr.Column(scale=1):
                        image_input = gr.File(
                            label="이미지 업로드 (여러 개 가능)",
                            file_count="multiple",
                            file_types=["image"]
                        )
                        extract_btn = gr.Button("코드 추출", variant="primary")

                    with gr.Column(scale=2):
                        result_output = gr.Code(
                            label="추출 결과",
                            lines=30,
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

            with gr.Tab("코드 변환"):
                with gr.Row():
                    with gr.Column(scale=1):
                        code_id_input = gr.Textbox(
                            label="코드 ID",
                            placeholder="위에서 추출한 코드 ID를 입력하세요"
                        )

                        with gr.Row():
                            from_tech = gr.Dropdown(
                                label="원본 기술",
                                choices=[],
                                value=None,
                                visible=True,
                                allow_custom_value=True,
                            )
                            from_version = gr.Dropdown(
                                label="원본 버전",
                                choices=[],
                                value=None,
                                visible=True,
                                allow_custom_value=True,
                            )

                        with gr.Row():
                            to_tech = gr.Dropdown(
                                label="대상 기술",
                                choices=[],
                                value=None,
                                visible=True,
                                allow_custom_value=True,
                            )
                            to_version = gr.Dropdown(
                                label="대상 버전",
                                choices=[],
                                value=None,
                                visible=True,
                                allow_custom_value=True,
                            )

                        transform_btn = gr.Button("코드 변환", variant="primary")

                    with gr.Column(scale=2):
                        with gr.Tab("원본 코드"):
                            original_code = gr.Code(
                                lines=20,
                            )
                        with gr.Tab("변환 코드"):
                            transformed_code = gr.Code(
                                lines=20,
                            )

            # 이벤트 핸들러
            extract_btn.click(
                fn=self.process_images_gradio,
                inputs=[image_input],
                outputs=[result_output, extracted_code, code_id_output, from_tech, from_version, to_tech, to_version]
            )

            # 코드 ID를 자동으로 복사
            code_id_output.change(
                fn=lambda x: x,
                inputs=[code_id_output],
                outputs=[code_id_input]
            )

            # 원본 기술 선택 시 원본 버전과 대상 기술 업데이트
            from_tech.change(
                fn=self.update_from_tech_and_dependent_dropdowns,
                inputs=[from_tech],
                outputs=[from_version, to_tech, to_version]
            )

            # 대상 기술 선택 시 대상 버전 업데이트
            to_tech.change(
                fn=self.update_to_version_dropdown,
                inputs=[from_tech, to_tech],
                outputs=[to_version]
            )

            transform_btn.click(
                fn=self.transform_code_gradio,
                inputs=[code_id_input, from_tech, from_version, to_tech, to_version],
                outputs=[original_code, transformed_code]
            )

        return demo


def create_gradio_app(upload_directory: str = "./uploads"):
    interface = GradioInterface(upload_directory)
    return interface.create_gradio_interface()
