"""
프롬프트 선택 다이얼로그
기본 프롬프트와 사용자 정의 프롬프트 중 선택
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QButtonGroup, QRadioButton, QFrame, QScrollArea,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QPlainTextEdit
)
from PySide6.QtCore import Qt
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernCancelButton

# engine_local에서 기본 프롬프트 가져오기
from .engine_local import DEFAULT_AI_PROMPT


class PromptSelectionDialog(QDialog):
    """프롬프트 선택 다이얼로그"""
    
    def __init__(self, parent=None, current_type="default", current_content=""):
        super().__init__(parent)
        self.current_type = current_type
        self.current_content = current_content
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("AI 프롬프트 선택")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("🤖 AI 분석 프롬프트 선택")
        title_label.setObjectName("dialog_title")
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("상품명 분석에 사용할 AI 프롬프트를 선택하세요.")
        desc_label.setObjectName("dialog_desc")
        layout.addWidget(desc_label)
        
        # 프롬프트 선택 옵션
        self.setup_prompt_options(layout)
        
        # 버튼
        self.setup_buttons(layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def setup_prompt_options(self, layout):
        """프롬프트 선택 옵션 설정"""
        # 라디오 버튼 그룹
        self.prompt_group = QButtonGroup()
        
        # 기본 프롬프트 선택
        self.default_radio = QRadioButton("기본 프롬프트 사용")
        self.default_radio.setObjectName("prompt_radio")
        self.prompt_group.addButton(self.default_radio, 0)
        layout.addWidget(self.default_radio)
        
        # 기본 프롬프트 미리보기
        default_card = self.create_prompt_preview_card("기본 프롬프트", DEFAULT_AI_PROMPT)
        layout.addWidget(default_card)
        
        # 사용자 정의 프롬프트 선택
        self.custom_radio = QRadioButton("사용자 정의 프롬프트")
        self.custom_radio.setObjectName("prompt_radio")
        self.prompt_group.addButton(self.custom_radio, 1)
        layout.addWidget(self.custom_radio)
        
        # 사용자 정의 프롬프트 입력
        custom_card = self.create_custom_prompt_card()
        layout.addWidget(custom_card)
        
        # 라디오 버튼 변경 이벤트
        self.prompt_group.buttonClicked.connect(self.on_prompt_type_changed)
    
    def create_prompt_preview_card(self, title, content):
        """프롬프트 미리보기 카드"""
        card = QFrame()
        card.setObjectName("prompt_card")
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        # 제목과 복사 버튼
        header_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setObjectName("prompt_card_title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 복사 버튼
        copy_button = QPushButton("📋 복사")
        copy_button.setObjectName("copy_button")
        copy_button.clicked.connect(lambda: self.copy_prompt_to_clipboard(content))
        header_layout.addWidget(copy_button)
        
        card_layout.addLayout(header_layout)
        
        # 스크롤 가능한 프롬프트 내용
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setObjectName("prompt_content")
        scroll_area.setWidget(content_label)
        
        card_layout.addWidget(scroll_area)
        card.setLayout(card_layout)
        
        return card
    
    def create_custom_prompt_card(self):
        """사용자 정의 프롬프트 카드"""
        card = QFrame()
        card.setObjectName("prompt_card")
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)
        
        # 제목
        title_label = QLabel("사용자 정의 프롬프트")
        title_label.setObjectName("prompt_card_title")
        card_layout.addWidget(title_label)
        
        # 텍스트 에디터
        self.custom_prompt_edit = QTextEdit()
        self.custom_prompt_edit.setPlaceholderText("여기에 사용자 정의 AI 프롬프트를 입력하세요...")
        self.custom_prompt_edit.setMaximumHeight(200)
        self.custom_prompt_edit.setObjectName("custom_prompt_edit")
        card_layout.addWidget(self.custom_prompt_edit)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_button = QPushButton("💾 저장")
        self.save_button.setObjectName("save_button")
        self.save_button.clicked.connect(self.save_custom_prompt)
        save_layout.addWidget(self.save_button)
        
        card_layout.addLayout(save_layout)
        card.setLayout(card_layout)
        
        return card
    
    def setup_buttons(self, layout):
        """하단 버튼들"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        # 취소 버튼
        cancel_button = ModernCancelButton("취소")
        cancel_button.setMinimumWidth(80)
        cancel_button.setMinimumHeight(40)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # 확인 버튼
        confirm_button = ModernPrimaryButton("확인")
        confirm_button.setMinimumWidth(80)
        confirm_button.setMinimumHeight(40)
        confirm_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(confirm_button)
        
        layout.addLayout(button_layout)
    
    def load_current_settings(self):
        """현재 설정 로드"""
        # 저장된 사용자 정의 프롬프트 로드
        saved_prompt = self._load_prompt_from_config()
        
        if self.current_type == "custom":
            self.custom_radio.setChecked(True)
            # 현재 내용이 있으면 사용, 없으면 저장된 내용 사용
            content = self.current_content if self.current_content else saved_prompt
            self.custom_prompt_edit.setText(content)
        else:
            self.default_radio.setChecked(True)
            # 기본 프롬프트가 선택되어도 텍스트 에디터에는 저장된 프롬프트 표시
            if saved_prompt:
                self.custom_prompt_edit.setText(saved_prompt)
        
        self.on_prompt_type_changed()
    
    def on_prompt_type_changed(self):
        """프롬프트 타입 변경 시"""
        is_custom = self.custom_radio.isChecked()
        self.custom_prompt_edit.setEnabled(is_custom)
        self.save_button.setEnabled(is_custom)
    
    def save_custom_prompt(self):
        """사용자 정의 프롬프트 저장"""
        custom_content = self.custom_prompt_edit.toPlainText().strip()
        
        if not custom_content:
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, 
                "프롬프트 내용 없음", 
                "저장할 프롬프트 내용이 없습니다.\\n\\n"
                "프롬프트 내용을 입력해주세요.",
                confirm_text="확인", 
                cancel_text=None, 
                icon="⚠️"
            )
            dialog.exec()
            return
        
        # 설정 파일에 저장
        try:
            self._save_prompt_to_config(custom_content)
            
            # 성공 메시지
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, 
                "저장 완료", 
                "사용자 정의 프롬프트가 저장되었습니다.\\n\\n"
                "다음에 다이얼로그를 열 때도 자동으로 불러와집니다.",
                confirm_text="확인", 
                cancel_text=None, 
                icon="✅"
            )
            dialog.exec()
            
        except Exception as e:
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, 
                "저장 실패", 
                f"프롬프트 저장 중 오류가 발생했습니다:\\n\\n{str(e)}",
                confirm_text="확인", 
                cancel_text=None, 
                icon="❌"
            )
            dialog.exec()
    
    def _save_prompt_to_config(self, prompt_content: str):
        """프롬프트를 설정 파일에 저장"""
        try:
            from src.foundation.config import config_manager
            
            # 앱 설정 로드
            app_config = config_manager.load_app_config()
            
            # 네이버 상품명 생성기 설정 섹션
            if 'naver_product_title_generator' not in app_config:
                app_config['naver_product_title_generator'] = {}
            
            app_config['naver_product_title_generator']['custom_prompt'] = prompt_content
            
            # 설정 저장
            success = config_manager.save_app_config(app_config)
            if not success:
                raise Exception("설정 저장 실패")
            
        except Exception as e:
            raise Exception(f"설정 저장 실패: {e}")
    
    def _load_prompt_from_config(self) -> str:
        """설정 파일에서 프롬프트 로드"""
        try:
            from src.foundation.config import config_manager
            app_config = config_manager.load_app_config()
            
            return app_config.get('naver_product_title_generator', {}).get('custom_prompt', '')
            
        except Exception as e:
            pass  # 로드 실패시 빈 문자열 반환
        
        return ""
    
    def copy_prompt_to_clipboard(self, content):
        """프롬프트 내용을 클립보드에 복사"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        
        # 성공 메시지 (임시로 버튼 텍스트 변경)
        sender = self.sender()
        if sender:
            original_text = sender.text()
            sender.setText("✅ 복사됨!")
            # 1.5초 후 원래 텍스트로 복원
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: sender.setText(original_text))
    
    def validate_and_accept(self):
        """프롬프트 선택 검증 후 확인"""
        # 사용자 정의 프롬프트를 선택한 경우
        if self.custom_radio.isChecked():
            custom_content = self.custom_prompt_edit.toPlainText().strip()
            
            # 사용자 정의 프롬프트가 비어있는 경우
            if not custom_content:
                from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                dialog = ModernConfirmDialog(
                    self, 
                    "사용자 정의 프롬프트 필요", 
                    "사용자 정의 프롬프트를 선택하셨지만 내용이 비어있습니다.\n\n"
                    "프롬프트 내용을 입력하거나 기본 프롬프트를 선택해주세요.",
                    confirm_text="확인", 
                    cancel_text=None, 
                    icon="⚠️"
                )
                dialog.exec()
                return  # 다이얼로그를 닫지 않고 사용자가 수정하도록 함
            
            # 사용자 정의 프롬프트가 있으면 자동 저장
            try:
                self._save_prompt_to_config(custom_content)
            except Exception as e:
                # 저장 실패해도 다이얼로그는 계속 진행 (사용자에게는 알리지 않음)
                pass
        
        # 검증 통과 시 다이얼로그 닫기
        self.accept()
    
    def get_selected_type(self):
        """선택된 프롬프트 타입 반환"""
        return "custom" if self.custom_radio.isChecked() else "default"
    
    def get_selected_content(self):
        """선택된 프롬프트 내용 반환"""
        if self.custom_radio.isChecked():
            return self.custom_prompt_edit.toPlainText().strip()
        else:
            return DEFAULT_AI_PROMPT
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="dialog_title"] {{
                font-size: 20px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
            QLabel[objectName="dialog_desc"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 10px;
            }}
            QRadioButton[objectName="prompt_radio"] {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin: 10px 0;
            }}
            QFrame[objectName="prompt_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            QLabel[objectName="prompt_card_title"] {{
                font-size: 14px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QLabel[objectName="prompt_content"] {{
                font-size: 12px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.4;
            }}
            QTextEdit[objectName="custom_prompt_edit"] {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTextEdit[objectName="custom_prompt_edit"]:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QPushButton[objectName="save_button"] {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: 1px solid {ModernStyle.COLORS['primary']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton[objectName="save_button"]:hover {{
                background-color: {ModernStyle.COLORS['success']};
                border-color: {ModernStyle.COLORS['success']};
            }}
            QPushButton[objectName="save_button"]:disabled {{
                opacity: 0.5;
            }}
            QPushButton[objectName="copy_button"] {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 500;
                min-width: 60px;
            }}
            QPushButton[objectName="copy_button"]:hover {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QPushButton[objectName="copy_button"]:pressed {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """)


class AIAnalysisDialog(QDialog):
    """AI 분석 실시간 내용 다이얼로그 (5탭)"""
    
    def __init__(self, parent=None, analysis_data=None, product_names=None):
        super().__init__(parent)
        self.analysis_data = analysis_data or {}
        self.product_names = product_names or []
        self.setup_ui()
        self.load_analysis_data()
    
    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("🤖 AI 분석 실시간 내용")
        self.setModal(True)
        self.resize(1000, 700)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 제목
        title_label = QLabel("🔍 AI 키워드 분석 상세 결과")
        title_label.setObjectName("dialog_title")
        layout.addWidget(title_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 5개 탭 생성
        self.create_prompt_tab()        # 1번 탭: 입력 프롬프트
        self.create_ai_output_tab()     # 2번 탭: AI 출력
        self.create_search_volume_tab() # 3번 탭: 월검색량 조회
        self.create_filtered_tab()      # 4번 탭: 필터링된 키워드 (100 이상)
        self.create_final_keywords_tab() # 5번 탭: 최종 키워드
        
        layout.addWidget(self.tab_widget)
        
        # 하단 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = ModernPrimaryButton("닫기")
        close_button.setMinimumWidth(80)
        close_button.setMinimumHeight(40)
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def create_prompt_tab(self):
        """1번 탭: 입력 프롬프트"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 설명
        desc_label = QLabel("AI에게 전송된 최종 프롬프트입니다.")
        desc_label.setObjectName("tab_desc")
        layout.addWidget(desc_label)
        
        # 프롬프트 내용
        self.prompt_text = QPlainTextEdit()
        self.prompt_text.setReadOnly(True)
        self.prompt_text.setMinimumHeight(500)
        layout.addWidget(self.prompt_text)
        
        self.tab_widget.addTab(tab, "📝 입력 프롬프트")
    
    def create_ai_output_tab(self):
        """2번 탭: AI 출력"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 설명
        desc_label = QLabel("AI가 응답한 원본 텍스트입니다.")
        desc_label.setObjectName("tab_desc")
        layout.addWidget(desc_label)
        
        # AI 응답 내용
        self.ai_response_text = QPlainTextEdit()
        self.ai_response_text.setReadOnly(True)
        self.ai_response_text.setMinimumHeight(500)
        layout.addWidget(self.ai_response_text)
        
        self.tab_widget.addTab(tab, "🤖 AI 출력")
    
    def create_search_volume_tab(self):
        """3번 탭: 월검색량 조회"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 설명
        desc_label = QLabel("AI가 추출한 키워드들의 네이버 월검색량 조회 결과입니다.")
        desc_label.setObjectName("tab_desc")
        layout.addWidget(desc_label)
        
        # 테이블
        self.search_volume_table = QTableWidget()
        self.search_volume_table.setColumnCount(3)
        self.search_volume_table.setHorizontalHeaderLabels(["키워드", "월검색량", "카테고리"])
        layout.addWidget(self.search_volume_table)
        
        self.tab_widget.addTab(tab, "📊 월검색량 조회")
    
    def create_filtered_tab(self):
        """4번 탭: 필터링된 키워드 (100 이상)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 설명
        desc_label = QLabel("월검색량 100 이상인 키워드들입니다.")
        desc_label.setObjectName("tab_desc")
        layout.addWidget(desc_label)
        
        # 테이블
        self.filtered_table = QTableWidget()
        self.filtered_table.setColumnCount(3)
        self.filtered_table.setHorizontalHeaderLabels(["키워드", "월검색량", "카테고리"])
        layout.addWidget(self.filtered_table)
        
        self.tab_widget.addTab(tab, "✅ 필터링된 키워드")
    
    def create_final_keywords_tab(self):
        """5번 탭: 최종 키워드"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 설명
        desc_label = QLabel("최종적으로 선별된 키워드 목록입니다.")
        desc_label.setObjectName("tab_desc")
        layout.addWidget(desc_label)
        
        # 테이블
        self.final_table = QTableWidget()
        self.final_table.setColumnCount(3)
        self.final_table.setHorizontalHeaderLabels(["키워드", "월검색량", "카테고리"])
        layout.addWidget(self.final_table)
        
        self.tab_widget.addTab(tab, "🎯 최종 키워드")
    
    def load_analysis_data(self):
        """분석 데이터 로드"""
        # 1번 탭: 입력 프롬프트
        prompt = self.analysis_data.get('input_prompt', '아직 분석이 시작되지 않았습니다.')
        self.prompt_text.setPlainText(prompt)
        
        # 2번 탭: AI 응답
        ai_response = self.analysis_data.get('ai_response', '아직 AI 응답이 없습니다.')
        self.ai_response_text.setPlainText(ai_response)
        
        # 3-5번 탭: 테이블 데이터
        self.populate_tables()
    
    def populate_tables(self):
        """테이블에 데이터 채우기"""
        # 3번 탭: 전체 키워드 (월검색량 포함)
        analyzed_keywords = self.analysis_data.get('analyzed_keywords', [])
        self.populate_keyword_table(self.search_volume_table, analyzed_keywords)
        
        # 4번 탭: 필터링된 키워드 (100 이상)
        filtered_keywords = self.analysis_data.get('filtered_keywords', [])
        self.populate_keyword_table(self.filtered_table, filtered_keywords)
        
        # 5번 탭: 최종 키워드 (동일)
        self.populate_keyword_table(self.final_table, filtered_keywords)
    
    def populate_keyword_table(self, table, keywords):
        """키워드 테이블 채우기"""
        table.setRowCount(len(keywords))
        
        for row, keyword_data in enumerate(keywords):
            if hasattr(keyword_data, 'keyword'):
                # KeywordBasicData 객체인 경우
                table.setItem(row, 0, QTableWidgetItem(keyword_data.keyword))
                table.setItem(row, 1, QTableWidgetItem(str(keyword_data.search_volume)))
                table.setItem(row, 2, QTableWidgetItem(keyword_data.category or ""))
            elif isinstance(keyword_data, dict):
                # dict인 경우
                table.setItem(row, 0, QTableWidgetItem(keyword_data.get('keyword', '')))
                table.setItem(row, 1, QTableWidgetItem(str(keyword_data.get('search_volume', 0))))
                table.setItem(row, 2, QTableWidgetItem(keyword_data.get('category', '')))
            else:
                # 문자열인 경우
                table.setItem(row, 0, QTableWidgetItem(str(keyword_data)))
                table.setItem(row, 1, QTableWidgetItem("조회 중"))
                table.setItem(row, 2, QTableWidgetItem("조회 중"))
        
        # 테이블 크기 조정
        table.resizeColumnsToContents()
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="dialog_title"] {{
                font-size: 18px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 15px;
            }}
            QLabel[objectName="tab_desc"] {{
                font-size: 13px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 10px;
            }}
            QTabWidget::pane {{
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 4px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {ModernStyle.COLORS['bg_tertiary']};
            }}
            QPlainTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTableWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 4px;
                gridline-color: {ModernStyle.COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 8px;
                border: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
            }}
        """)