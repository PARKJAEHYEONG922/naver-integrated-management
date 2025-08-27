"""
네이버 상품명 생성기 메인 UI
스텝 네비게이션 + 사이드바 + 메인 영역 구조
"""
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QFrame, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernCancelButton, ModernHelpButton, ModernCard, ModernProgressBar
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit import tokens
from src.desktop.common_log import log_manager

from .ui_steps import (
    Step1ResultWidget,
    Step2BasicAnalysisWidget,
    Step3AdvancedAnalysisWidget,
    Step4ResultWidget
)
from .service import product_title_service



class LeftPanel(QWidget):
    """왼쪽 패널: 진행상황 + 핵심제품명 입력"""
    
    # 시그널 정의
    analysis_started = Signal(str)  # 제품명으로 분석 시작
    analysis_stopped = Signal()    # 분석 정지
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        margin_h = tokens.GAP_12
        margin_v = tokens.GAP_16
        spacing = tokens.GAP_16
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        layout.setSpacing(spacing)
        
        # 진행상황 카드
        self.progress_card = self.create_progress_card()
        layout.addWidget(self.progress_card)
        
        # 핵심제품명 입력 카드
        self.input_card = self.create_input_card()
        layout.addWidget(self.input_card)
        
        layout.addStretch()
        self.setLayout(layout)
        self.apply_styles()
        
    def create_progress_card(self):
        """진행상황 표시 카드"""
        card = ModernCard("📊 진행상황")
        layout = QVBoxLayout(card)
        margin = tokens.GAP_12
        layout.setContentsMargins(margin, margin, margin, margin)
        
        # 현재 단계
        self.current_step_label = QLabel("1/4 단계")
        self.current_step_label.setObjectName("step_info")
        layout.addWidget(self.current_step_label)
        
        # 상태 메시지
        self.status_label = QLabel("제품명 입력 대기 중")
        self.status_label.setObjectName("status_info")
        layout.addWidget(self.status_label)
        
        # 진행률 바 (공용 컴포넌트 사용)
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)  # 초기값 0%
        layout.addWidget(self.progress_bar)
        
        return card
        
    def create_input_card(self):
        """핵심제품명 입력 카드"""
        from PySide6.QtWidgets import QTextEdit
        
        card = ModernCard("📝 핵심제품명 입력")
        layout = QVBoxLayout(card)
        margin = tokens.GAP_12
        spacing = tokens.GAP_10
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 입력 필드 (확장된 크기)
        self.product_input = QTextEdit()
        self.product_input.setPlaceholderText("키워드를 입력해주세요 (엔터 또는 , 로 구분)")
        min_height = 120
        max_height = 150
        self.product_input.setMinimumHeight(min_height)
        self.product_input.setMaximumHeight(max_height)
        
        # 자동 줄바꿈 설정
        self.product_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.product_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.product_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.product_input)
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_spacing = tokens.GAP_8
        button_layout.setSpacing(button_spacing)
        
        self.start_button = ModernPrimaryButton("🔍 분석시작")
        button_height = tokens.GAP_40
        self.start_button.setMinimumHeight(button_height)
        self.start_button.clicked.connect(self.on_start_analysis)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = ModernCancelButton("⏹ 정지")
        self.stop_button.setMinimumHeight(button_height)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.analysis_stopped.emit)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        return card
        
    def on_start_analysis(self):
        """분석 시작"""
        text = self.product_input.toPlainText().strip()
        if not text:
            return
            
        self.start_button.setEnabled(False)
        self.start_button.setText("분석 중...")
        self.stop_button.setEnabled(True)
        
        self.analysis_started.emit(text)
        
    def on_analysis_completed(self):
        """분석 완료 시 버튼 상태 복원"""
        self.start_button.setEnabled(True)
        self.start_button.setText("🔍 분석시작")  # 원래대로 유지
        self.stop_button.setEnabled(False)
        
    def on_analysis_stopped(self):
        """분석 중지 시 버튼 상태 복원"""
        self.start_button.setEnabled(True)
        self.start_button.setText("🔍 분석시작")
        self.stop_button.setEnabled(False)
        
    def update_progress(self, step: int, status: str, progress: int = 0):
        """진행상황 업데이트"""
        self.current_step_label.setText(f"{step}/4 단계")
        self.status_label.setText(status)
        
        # 진행률 바 업데이트 (각 단계별 독립적으로)
        self.progress_bar.setValue(min(progress, 100))
        
    def set_navigation_enabled(self, prev: bool, next_: bool):
        """네비게이션 버튼 활성화 설정"""
        self.prev_button.setEnabled(prev)
        self.next_button.setEnabled(next_)
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="step_info"] {{
                font-size: {tokens.get_font_size('large')}px;
                font-weight: 600;
                color: {ModernStyle.COLORS['primary']};
                margin: {tokens.GAP_4}px 0px;
            }}
            QLabel[objectName="status_info"] {{
                font-size: {tokens.get_font_size('normal')}px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin: {tokens.GAP_6}px 0px;
            }}
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.GAP_8}px;
                padding: {tokens.GAP_16}px;
                font-size: {tokens.get_font_size('normal')}px;
                color: {ModernStyle.COLORS['text_primary']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """)


class RightPanel(QWidget):
    """오른쪽 패널: 이전/다음 버튼 + 결과 화면 + 초기화"""
    
    # 시그널 정의
    previous_step = Signal()
    next_step = Signal()
    reset_all = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_step = 1
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        margin = tokens.GAP_20
        spacing = tokens.GAP_15
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 상단 네비게이션 버튼들
        nav_layout = QHBoxLayout()
        
        self.prev_button = ModernCancelButton("◀ 이전")
        button_height = tokens.GAP_40
        button_width = 120
        self.prev_button.setFixedHeight(button_height)
        self.prev_button.setFixedWidth(button_width)
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.previous_step.emit)
        nav_layout.addWidget(self.prev_button)
        
        nav_layout.addStretch()
        
        self.next_button = ModernPrimaryButton("다음 ▶")
        self.next_button.setFixedHeight(button_height)
        self.next_button.setFixedWidth(button_width)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_step.emit)
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        # 메인 결과 영역 (스택 방식)
        self.content_stack = QStackedWidget()
        self.setup_step_widgets()
        layout.addWidget(self.content_stack, 1)  # 확장
        
        # 하단 초기화 버튼
        reset_layout = QHBoxLayout()
        
        self.reset_button = ModernCancelButton("🔄 초기화")
        reset_button_height = tokens.GAP_40
        self.reset_button.setMinimumHeight(reset_button_height)
        self.reset_button.clicked.connect(self.reset_all.emit)
        reset_layout.addWidget(self.reset_button)
        
        reset_layout.addStretch()
        
        layout.addLayout(reset_layout)
        
        self.setLayout(layout)
        self.apply_styles()
        
    def setup_step_widgets(self):
        """각 단계별 위젯 생성 (수정된 버전)"""
        
        # 1단계: 분석 결과 표시 (입력은 왼쪽에서)
        self.step1_widget = Step1ResultWidget()
        self.content_stack.addWidget(self.step1_widget)
        
        # 2단계: 기초 분석 결과
        self.step2_widget = Step2BasicAnalysisWidget()
        self.content_stack.addWidget(self.step2_widget)
        
        # 3단계: AI 상품명 분석
        self.step3_widget = Step3AdvancedAnalysisWidget()
        self.content_stack.addWidget(self.step3_widget)
        
        # 4단계: 최종 결과
        self.step4_widget = Step4ResultWidget()
        self.content_stack.addWidget(self.step4_widget)
        
        # 단계간 시그널 연결
        self.setup_step_connections()
        
    def setup_step_connections(self):
        """단계간 시그널 연결 설정"""
        # 3단계 → 4단계: 선택된 키워드 전달
        self.step3_widget.keywords_selected_for_step4.connect(
            self.step4_widget.set_selected_keywords
        )
        
        # 2단계 → 4단계: 상품명 통계 전달 (추후 구현)
        # self.step2_widget.product_stats_updated.connect(
        #     self.step4_widget.set_product_name_stats
        # )
        
        # 4단계: AI 상품명 생성 요청 (추후 구현)
        # self.step4_widget.generate_product_names.connect(
        #     self.handle_ai_generation_request
        # )
        
    def go_to_step(self, step: int):
        """특정 단계로 이동"""
        if 1 <= step <= 4:
            self.current_step = step
            self.content_stack.setCurrentIndex(step - 1)
            
            # 네비게이션 버튼 상태 업데이트
            self.prev_button.setEnabled(step > 1)
            self.next_button.setEnabled(step < 4)
            
    def set_next_enabled(self, enabled: bool):
        """다음 버튼 활성화 설정"""
        self.next_button.setEnabled(enabled)
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)


class NaverProductTitleGeneratorWidget(QWidget):
    """네이버 상품명 생성기 메인 위젯 - 새로운 레이아웃"""
    
    def __init__(self):
        super().__init__()
        self.current_step = 1
        self.last_selected_keywords = []  # 마지막으로 상품명 수집한 키워드들
        self.last_selected_category = ""  # 1단계에서 선택한 카테고리
        self.cached_product_names = []    # 캐시된 상품명 결과
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI 구성 - 새로운 레이아웃"""
        main_layout = QVBoxLayout(self)
        margin = tokens.GAP_20
        spacing = tokens.GAP_20
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 헤더 섹션 (제목 + 사용법)
        self.setup_header(main_layout)
        
        # 콘텐츠 레이아웃 (왼쪽: 진행상황+입력, 오른쪽: 결과+네비게이션)
        content_layout = QHBoxLayout()
        content_spacing = tokens.GAP_20
        content_layout.setSpacing(content_spacing)
        
        # 왼쪽 패널 (진행상황 + 핵심제품명 입력)
        self.left_panel = LeftPanel()
        left_panel_width = 320
        self.left_panel.setFixedWidth(left_panel_width)
        content_layout.addWidget(self.left_panel)
        
        # 오른쪽 패널 (이전/다음 + 결과 + 초기화)
        self.right_panel = RightPanel()
        content_layout.addWidget(self.right_panel, 1)  # 확장 가능
        
        main_layout.addLayout(content_layout)
        self.apply_styles()
        
        # 초기 상태를 1단계로 설정
        self.go_to_step(1)
        
        # 현재 AI 모델 정보 로드
        self.load_current_ai_model()
        
        # API 설정 상태 확인
        self.check_api_status()
        
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법) - 파워링크와 동일"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("🏷️ 네이버 상품명 생성기")
        title_font_size = tokens.get_font_size('title')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 버튼 (공용 컴포넌트 사용)
        self.help_button = ModernHelpButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        header_layout.addWidget(self.help_button)
        
        # 스트레치로 공간 확보 (AI 모델 표시를 제일 오른쪽으로)
        header_layout.addStretch()
        
        # 현재 AI 모델 표시 (제일 오른쪽)
        self.ai_model_label = QLabel("AI 모델: 설정 중...")
        model_font_size = tokens.get_font_size('normal')
        model_padding_v = tokens.GAP_6
        model_padding_h = 12
        model_border_radius = tokens.GAP_6
        self.ai_model_label.setStyleSheet(f"""
            QLabel {{
                font-size: {model_font_size}px;
                color: {ModernStyle.COLORS['text_secondary']};
                background-color: {ModernStyle.COLORS['bg_secondary']};
                padding: {model_padding_v}px {model_padding_h}px;
                border-radius: {model_border_radius}px;
                border: 1px solid {ModernStyle.COLORS['border']};
            }}
        """)
        header_layout.addWidget(self.ai_model_label)
        
        layout.addLayout(header_layout)
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = (
            "🎯 새로운 워크플로우:\n\n"
            
            "📝 왼쪽 패널 - 제품명 입력 및 진행상황:\n"
            "• 핵심 제품명을 입력하고 '분석시작' 버튼을 클릭하세요\n"
            "• 진행상황을 실시간으로 확인할 수 있습니다\n"
            "• '정지' 버튼으로 분석을 중단할 수 있습니다\n\n"
            
            "🔍 오른쪽 패널 - 분석 결과 및 네비게이션:\n"
            "• 각 단계별 분석 결과가 표시됩니다\n"
            "• 상단 '이전/다음' 버튼으로 단계 이동 가능\n"
            "• 하단 '초기화' 버튼으로 처음부터 다시 시작\n\n"
            
            "🚀 4단계 프로세스:\n"
            "1️⃣ 키워드 분석 - 월검색량과 카테고리 확인\n"
            "2️⃣ 키워드 선택 - 같은 카테고리 키워드들 선택\n" 
            "3️⃣ AI 심화분석 - 상위 상품명 AI 분석\n"
            "4️⃣ 상품명 생성 - SEO 최적화 상품명 자동생성\n\n"
            
            "💡 사용 팁:\n"
            "• 구체적인 제품명일수록 정확한 분석 가능\n"
            "• 같은 카테고리 키워드 여러 개 선택 가능\n"
            "• 각 단계를 자유롭게 이동하며 수정 가능"
        )
        
        dialog = ModernConfirmDialog(
            self, "네이버 상품명 생성기 사용법", help_text, 
            confirm_text="확인", cancel_text=None, icon="💡"
        )
        dialog.exec()
        
    def load_current_ai_model(self):
        """현재 설정된 AI 모델 정보 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            current_model = getattr(api_config, 'current_ai_model', '')
            if current_model and current_model != "AI 제공자를 선택하세요":
                # 모델명 간소화 표시
                if "무료" in current_model or "최신" in current_model:
                    self.ai_model_label.setText(f"🤖 AI: {current_model}")
                    success_font_size = tokens.get_font_size('normal')
                    success_padding_v = tokens.GAP_6
                    success_padding_h = 12
                    success_border_radius = tokens.GAP_6
                    self.ai_model_label.setStyleSheet(f"""
                        QLabel {{
                            font-size: {success_font_size}px;
                            color: {ModernStyle.COLORS['success']};
                            background-color: {ModernStyle.COLORS['bg_secondary']};
                            padding: {success_padding_v}px {success_padding_h}px;
                            border-radius: {success_border_radius}px;
                            border: 1px solid {ModernStyle.COLORS['success']};
                            font-weight: 600;
                        }}
                    """)
                elif "유료" in current_model:
                    self.ai_model_label.setText(f"🤖 AI: {current_model}")
                    primary_font_size = tokens.get_font_size('normal')
                    primary_padding_v = tokens.GAP_6
                    primary_padding_h = 12
                    primary_border_radius = tokens.GAP_6
                    self.ai_model_label.setStyleSheet(f"""
                        QLabel {{
                            font-size: {primary_font_size}px;
                            color: {ModernStyle.COLORS['primary']};
                            background-color: {ModernStyle.COLORS['bg_secondary']};
                            padding: {primary_padding_v}px {primary_padding_h}px;
                            border-radius: {primary_border_radius}px;
                            border: 1px solid {ModernStyle.COLORS['primary']};
                            font-weight: 600;
                        }}
                    """)
                else:
                    self.ai_model_label.setText(f"🤖 AI: {current_model}")
                    default_font_size = tokens.get_font_size('normal')
                    default_padding_v = tokens.GAP_6
                    default_padding_h = 12
                    default_border_radius = tokens.GAP_6
                    self.ai_model_label.setStyleSheet(f"""
                        QLabel {{
                            font-size: {default_font_size}px;
                            color: {ModernStyle.COLORS['text_secondary']};
                            background-color: {ModernStyle.COLORS['bg_secondary']};
                            padding: {default_padding_v}px {default_padding_h}px;
                            border-radius: {default_border_radius}px;
                            border: 1px solid {ModernStyle.COLORS['border']};
                        }}
                    """)
            else:
                self.ai_model_label.setText("⚠️ AI 모델 미설정")
                warning_font_size = tokens.get_font_size('normal')
                warning_padding_v = tokens.GAP_6
                warning_padding_h = 12
                warning_border_radius = tokens.GAP_6
                self.ai_model_label.setStyleSheet(f"""
                    QLabel {{
                        font-size: {warning_font_size}px;
                        color: {ModernStyle.COLORS['warning']};
                        background-color: {ModernStyle.COLORS['bg_secondary']};
                        padding: {warning_padding_v}px {warning_padding_h}px;
                        border-radius: {warning_border_radius}px;
                        border: 1px solid {ModernStyle.COLORS['warning']};
                    }}
                """)
                
        except Exception as e:
            self.ai_model_label.setText("❌ AI 모델 로드 실패")
            error_font_size = tokens.get_font_size('normal')
            error_padding_v = tokens.GAP_6
            error_padding_h = 12
            error_border_radius = tokens.GAP_6
            self.ai_model_label.setStyleSheet(f"""
                QLabel {{
                    font-size: {error_font_size}px;
                    color: {ModernStyle.COLORS['danger']};
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                    padding: {error_padding_v}px {error_padding_h}px;
                    border-radius: {error_border_radius}px;
                    border: 1px solid {ModernStyle.COLORS['danger']};
                }}
            """)
            print(f"AI 모델 로드 오류: {e}")
    
    def check_api_status(self):
        """API 설정 상태 확인 - Foundation Config 사용"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            missing_apis = []
            
            # 네이버 쇼핑 API 확인 (Step 2에서 상품명 수집용)
            if not api_config.is_shopping_valid():
                missing_apis.append("네이버 쇼핑 API")
            
            # AI API 확인 (Step 3, 4에서 AI 분석/생성용)  
            if not api_config.current_ai_model or api_config.current_ai_model == "AI 제공자를 선택하세요":
                missing_apis.append("AI API")
            elif api_config.current_ai_model and not any([
                api_config.openai_api_key,
                api_config.claude_api_key, 
                api_config.gemini_api_key
            ]):
                missing_apis.append("AI API 키")
            
            if missing_apis:
                log_manager.add_log(f"⚠️ API 설정 필요: {', '.join(missing_apis)}", "warning")
                log_manager.add_log("💡 상단의 API 설정 버튼을 클릭하여 설정하세요", "info")
            else:
                log_manager.add_log("✅ 모든 API 설정 완료", "success")
                
        except Exception as e:
            log_manager.add_log(f"❌ API 상태 확인 실패: {str(e)}", "error")
            print(f"API 상태 확인 오류: {e}")
        
    def setup_connections(self):
        """시그널 연결 - 새로운 레이아웃"""
        # 왼쪽 패널 시그널
        self.left_panel.analysis_started.connect(self.on_analysis_started)
        self.left_panel.analysis_stopped.connect(self.on_analysis_stopped)
        
        # 오른쪽 패널 시그널  
        self.right_panel.previous_step.connect(self.go_previous_step)
        self.right_panel.next_step.connect(self.go_next_step)
        self.right_panel.reset_all.connect(self.reset_all_steps)
        
        # 2단계 프롬프트 선택 시그널
        self.right_panel.step2_widget.prompt_selected.connect(self.on_prompt_selected)
        
        # 3단계 AI 분석 시그널
        self.right_panel.step3_widget.ai_analysis_started.connect(self.start_ai_analysis)
        self.right_panel.step3_widget.analysis_stopped.connect(lambda: self.stop_ai_analysis())
        
        # 4단계 AI 상품명 생성 시그널
        self.right_panel.step4_widget.ai_generation_started.connect(self.start_ai_product_generation)
        
        # API 설정 변경 시그널 연결 (부모 윈도우에서 받기)
        self.connect_to_api_dialog()
    
    def connect_to_api_dialog(self):
        """API 설정 변경 시그널에 연결 (foundation config manager 사용)"""
        try:
            from src.foundation.config import config_manager
            # 전역 config manager의 API 설정 변경 시그널에 연결
            if hasattr(config_manager, 'api_config_changed'):
                config_manager.api_config_changed.connect(self.on_api_settings_changed)
        except Exception as e:
            pass  # 시그널 연결 실패는 조용히 처리
    
    def on_api_settings_changed(self):
        """API 설정이 변경되었을 때 AI 모델 표시 업데이트"""
        self.load_current_ai_model()
        self.check_api_status()  # API 상태도 다시 확인
        
    def on_analysis_started(self, product_name: str):
        """분석 시작 처리"""
        log_manager.add_log(f"🔍 분석 시작: {product_name}", "info")
        
        # 진행상황 업데이트
        self.left_panel.update_progress(1, "키워드 분석 중...", 10)
        
        # 오른쪽 패널을 1단계로 이동
        self.right_panel.go_to_step(1)
        self.current_step = 1
        
        # 실제 분석 워커 시작
        from .worker import BasicAnalysisWorker, worker_manager
        
        self.current_worker = BasicAnalysisWorker(product_name)
        self.current_worker.progress_updated.connect(self.on_analysis_progress)
        self.current_worker.analysis_completed.connect(self.on_analysis_completed)
        self.current_worker.error_occurred.connect(self.on_analysis_error)
        
        worker_manager.start_worker(self.current_worker)
        
    def on_analysis_progress(self, progress: int, message: str):
        """분석 진행률 업데이트"""
        self.left_panel.update_progress(1, message, progress)
        
    def on_analysis_completed(self, results):
        """분석 완료 처리"""
        log_manager.add_log(f"✅ 키워드 분석 완료: {len(results)}개", "success")
        
        # 왼쪽 패널 버튼 상태 복원 및 입력창 클리어
        self.left_panel.on_analysis_completed()
        self.left_panel.product_input.clear()  # 입력창 클리어
        
        # 진행상황 업데이트
        self.left_panel.update_progress(1, "키워드 분석 완료", 100)
        
        # 오른쪽 패널에 결과 표시 (기존 결과와 병합)
        self.merge_and_display_results(results)
        
        # 다음 단계 활성화
        self.right_panel.set_next_enabled(True)
    
    def merge_and_display_results(self, new_results):
        """기존 결과와 새 결과를 병합하여 표시"""
        # 기존 결과 가져오기
        existing_results = getattr(self, 'all_analysis_results', [])
        
        # 새 결과와 병합 (중복 키워드 제거)
        existing_keywords = {result.keyword for result in existing_results}
        merged_results = existing_results.copy()
        
        for result in new_results:
            if result.keyword not in existing_keywords:
                merged_results.append(result)
        
        # 전체 결과 저장
        self.all_analysis_results = merged_results
        
        # 오른쪽 패널에 병합된 결과 표시
        self.right_panel.step1_widget.display_results(merged_results)
        
    def on_analysis_error(self, error_message: str):
        """분석 에러 처리"""
        log_manager.add_log(f"❌ 분석 실패: {error_message}", "error")
        
        # 왼쪽 패널 버튼 상태 복원
        self.left_panel.on_analysis_stopped()
        
        # 진행상황 초기화
        self.left_panel.update_progress(1, "분석 실패", 0)
        
    def on_analysis_stopped(self):
        """분석 정지 처리"""
        log_manager.add_log("⏹ 분석이 중지되었습니다", "warning")
        
        # 실제 워커 중지
        if hasattr(self, 'current_worker') and self.current_worker:
            self.current_worker.request_stop()
            from .worker import worker_manager
            worker_manager.stop_worker(self.current_worker)
        
        # 왼쪽 패널 버튼 상태 복원
        self.left_panel.on_analysis_stopped()
        
        # 진행상황 초기화
        self.left_panel.update_progress(1, "분석 중지됨", 0)
    
    def start_product_name_collection(self, selected_keywords):
        """상품명 수집 시작"""
        log_manager.add_log(f"🛒 상품명 수집 시작: {len(selected_keywords)}개 키워드", "info")
        
        # 진행상황 업데이트
        self.left_panel.update_progress(2, "상품명 수집 중...", 10)
        
        # 상품명 수집 워커 시작
        from .worker import ProductNameCollectionWorker, worker_manager
        
        self.current_collection_worker = ProductNameCollectionWorker(selected_keywords)
        self.current_collection_worker.progress_updated.connect(self.on_collection_progress)
        self.current_collection_worker.collection_completed.connect(self.on_collection_completed)
        self.current_collection_worker.error_occurred.connect(self.on_collection_error)
        
        worker_manager.start_worker(self.current_collection_worker)
    
    def on_collection_progress(self, progress: int, message: str):
        """상품명 수집 진행률 업데이트"""
        self.left_panel.update_progress(2, message, progress)
    
    def on_collection_completed(self, product_names):
        """상품명 수집 완료 처리"""
        log_manager.add_log(f"✅ 상품명 수집 완료: {len(product_names)}개", "success")
        
        # 진행상황 업데이트
        self.left_panel.update_progress(2, "상품명 수집 완료", 100)
        
        # 캐시 업데이트 (현재 선택된 키워드와 결과 저장)
        current_selected = self.right_panel.step1_widget.get_selected_keywords()
        self.last_selected_keywords = current_selected.copy()
        self.cached_product_names = product_names.copy()
        
        # 2단계로 이동
        self.go_to_step(2)
        
        # 오른쪽 패널에 상품명 표시
        self.right_panel.step2_widget.display_product_names(product_names)
        
        # 3단계에 상품명 데이터 전달
        self.right_panel.step3_widget.set_product_names(product_names)
        
        # 다음 단계 활성화
        self.right_panel.set_next_enabled(True)
    
    def on_collection_error(self, error_message: str):
        """상품명 수집 에러 처리"""
        log_manager.add_log(f"❌ 상품명 수집 실패: {error_message}", "error")
        
        # 진행상황 초기화
        self.left_panel.update_progress(2, "상품명 수집 실패", 0)
        
    def on_prompt_selected(self, prompt_type: str, prompt_content: str):
        """2단계에서 프롬프트가 선택되었을 때"""
        prompt_display = "기본 프롬프트" if prompt_type == "default" else "사용자 정의 프롬프트"
        log_manager.add_log(f"📝 프롬프트 선택됨: {prompt_display}", "info")
        
        # 3단계에 프롬프트 정보 전달
        self.right_panel.step3_widget.set_prompt_info(prompt_type, prompt_content)
        
        # 다음 단계 활성화
        self.right_panel.set_next_enabled(True)
        
    def go_to_step(self, step: int):
        """특정 단계로 이동"""
        if 1 <= step <= 4:
            self.current_step = step
            self.right_panel.go_to_step(step)
            
            # 진행상황 업데이트 (진행률 0%로 초기화)
            step_names = ["키워드 분석", "키워드 선택", "심화분석", "상품명생성"]
            self.left_panel.update_progress(step, f"{step_names[step-1]} 단계", 0)
            
            # 분석시작 버튼은 1단계에서만 활성화
            if step == 1:
                self.left_panel.start_button.setEnabled(True)
                self.left_panel.start_button.show()
                self.left_panel.stop_button.show()
            else:
                self.left_panel.start_button.setEnabled(False)
                self.left_panel.start_button.hide()
                self.left_panel.stop_button.hide()
            
    def go_previous_step(self):
        """이전 단계로"""
        if self.current_step > 1:
            self.go_to_step(self.current_step - 1)
            
    def go_next_step(self):
        """다음 단계로"""
        if self.current_step < 4:
            # Step 1에서 Step 2로 이동할 때 카테고리 일치 검증 및 상품명 수집
            if self.current_step == 1:
                if not self.right_panel.step1_widget.validate_category_consistency():
                    return  # 검증 실패시 다음 단계로 이동하지 않음
                
                # 선택된 키워드 확인
                selected_keywords = self.right_panel.step1_widget.get_selected_keywords()
                if not selected_keywords:
                    return
                
                # 키워드 변경 여부 확인
                if self.keywords_changed(selected_keywords):
                    # 키워드가 변경됨 → 새로 상품명 수집
                    log_manager.add_log(f"🔄 키워드 변경 감지, 새로 상품명 수집", "info")
                    self.start_product_name_collection(selected_keywords)
                    return  # 수집 완료 후 자동으로 다음 단계로 이동
                else:
                    # 키워드가 동일함 → 기존 결과 재사용 (로그 제거)
                    self.go_to_step(2)
                    self.right_panel.step2_widget.display_product_names(self.cached_product_names)
                    self.right_panel.set_next_enabled(True)
                    return
            
            # Step 2에서 Step 3로 넘어갈 때
            elif self.current_step == 2:
                # 프롬프트가 선택되지 않았으면 자동으로 기본 프롬프트 선택
                self.right_panel.step2_widget.ensure_prompt_selected()
                
                # 현재 선택된 프롬프트 정보를 로그로 표시
                prompt_type = self.right_panel.step3_widget.selected_prompt_type
                prompt_display = "기본 프롬프트" if prompt_type == "default" else "사용자 정의 프롬프트"
                log_manager.add_log(f"📝 3단계 진입: {prompt_display} 사용", "info")
                
            # Step 3에서 Step 4로 넘어갈 때
            elif self.current_step == 3:
                # 선택된 키워드 확인
                selected_keywords = self.right_panel.step3_widget.get_selected_keywords()
                if not selected_keywords:
                    # 키워드가 선택되지 않았으면 다이얼로그 표시
                    self.show_keyword_selection_warning()
                    return  # 다음 단계로 이동하지 않음
            
            self.go_to_step(self.current_step + 1)
    
    def show_keyword_selection_warning(self):
        """키워드 선택 경고 다이얼로그 표시"""
        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
        
        dialog = ModernConfirmDialog(
            self,
            "키워드 선택 필요",
            "4단계로 이동하려면 3단계에서 키워드를 최소 1개 이상 선택해주세요.\n\n"
            "키워드를 선택하시면 4단계에서 최적화된 상품명을 생성할 수 있습니다.",
            confirm_text="확인",
            cancel_text=None,
            icon="⚠️"
        )
        dialog.exec()
        
    def reset_all_steps(self):
        """모든 단계 초기화"""
        log_manager.add_log("🔄 모든 단계를 초기화합니다.", "info")
        
        # 서비스 초기화
        product_title_service.reset_session()
        
        # 전체 분석 결과 초기화
        self.all_analysis_results = []
        
        # UI 초기화
        self.go_to_step(1)
        self.left_panel.product_input.clear()
        self.left_panel.on_analysis_stopped()
        
        # 1단계 위젯 초기화
        self.right_panel.step1_widget.clear_cards()
        
        # 캐시 초기화
        self.last_selected_keywords = []
        self.cached_product_names = []
    
    def keywords_changed(self, current_keywords):
        """선택된 키워드가 변경되었는지 확인"""
        if len(current_keywords) != len(self.last_selected_keywords):
            return True
        
        # 키워드 이름으로 비교 (순서는 무시)
        current_names = {kw.keyword for kw in current_keywords}
        last_names = {kw.keyword for kw in self.last_selected_keywords}
        
        return current_names != last_names
    
    def start_ai_analysis(self, prompt_type: str, prompt_content: str):
        """AI 분석 시작 처리"""
        prompt_display = "기본 프롬프트" if prompt_type == "default" else "사용자 정의 프롬프트"
        log_manager.add_log(f"🤖 AI 분석 시작: {prompt_display}", "info")
        
        # 진행상황 업데이트
        self.left_panel.update_progress(3, "AI 키워드 추출 중...", 10)
        
        # 최종 프롬프트 생성 (실시간 로그용)
        from .engine_local import build_ai_prompt
        product_titles = [p.get('title', '') for p in self.cached_product_names if isinstance(p, dict)]
        final_prompt = build_ai_prompt(product_titles, prompt_content if prompt_type == "custom" else None)
        
        # 3단계에 분석 데이터 전달
        self.right_panel.step3_widget.analysis_data['input_prompt'] = final_prompt
        
        # AI 분석 워커 시작 - 상품명과 프롬프트, 1단계 선택 키워드를 함께 전달
        from .worker import AIAnalysisWorker, worker_manager
        
        product_names = self.cached_product_names  # 2단계에서 수집된 상품명들
        
        # 프롬프트 타입에 따라 적절한 값 전달
        worker_prompt = prompt_content if prompt_type == "custom" else None
        
        # 1단계에서 선택한 키워드들을 추출 (문자열 리스트)
        selected_keywords = [kw.keyword for kw in self.last_selected_keywords] if self.last_selected_keywords else []
        
        # 1단계에서 선택한 카테고리 추출
        selected_category = self.right_panel.step1_widget.get_selected_category()
        self.last_selected_category = selected_category  # 저장
        
        
        self.current_ai_worker = AIAnalysisWorker(product_names, worker_prompt, selected_keywords, selected_category)
        self.current_ai_worker.progress_updated.connect(self.on_ai_progress)
        self.current_ai_worker.analysis_completed.connect(self.on_ai_analysis_completed)
        self.current_ai_worker.analysis_data_updated.connect(self.on_analysis_data_updated)
        self.current_ai_worker.error_occurred.connect(self.on_ai_analysis_error)
        
        
        worker_manager.start_worker(self.current_ai_worker)
    
    def on_ai_progress(self, progress: int, message: str):
        """AI 분석 진행률 업데이트"""
        self.left_panel.update_progress(3, message, progress)
    
    def on_analysis_data_updated(self, data: dict):
        """AI 분석 데이터 실시간 업데이트"""
        # 3단계 위젯의 analysis_data 업데이트 (실시간 분석 내용 다이얼로그용)
        self.right_panel.step3_widget.update_analysis_data(data)
    
    def on_ai_analysis_completed(self, keywords):
        """AI 분석 완료 처리"""
        log_manager.add_log(f"✅ AI 분석 완료: {len(keywords)}개 키워드", "success")
        
        # 진행상황 업데이트 - 키워드 개수 포함
        self.left_panel.update_progress(3, f"AI분석 완료 총 {len(keywords)}개 키워드", 100)
        
        # 3단계에 AI 분석 완료 알림
        self.right_panel.step3_widget.on_analysis_completed(keywords)
        
        # 다음 단계 활성화
        self.right_panel.set_next_enabled(True)
    
    
    def on_ai_analysis_error(self, error_message: str):
        """AI 분석 에러 처리"""
        log_manager.add_log(f"❌ AI 분석 실패: {error_message}", "error")
        
        # 진행상황 초기화
        self.left_panel.update_progress(3, "AI 분석 실패", 0)
        
        # 3단계에 에러 알림
        self.right_panel.step3_widget.on_analysis_error(error_message)
    
    def stop_ai_analysis(self):
        """AI 분석 정지 처리"""
        log_manager.add_log("⏹ AI 분석이 중지되었습니다", "warning")
        
        # 실제 워커 중지
        if hasattr(self, 'current_ai_worker') and self.current_ai_worker:
            self.current_ai_worker.request_stop()
            from .worker import worker_manager
            worker_manager.stop_worker(self.current_ai_worker)
        
        # 3단계에 중단 알림
        self.right_panel.step3_widget.stop_analysis()
        
        # 진행상황 초기화
        self.left_panel.update_progress(3, "분석 중지됨", 0)
    
    def start_ai_product_generation(self, generation_data: dict, product_info: dict):
        """Step 4에서 AI 상품명 생성 시작"""
        # 새로운 데이터 구조에서 핵심 키워드와 모든 키워드 추출
        core_keyword_dict = generation_data.get('core_keyword', {})
        all_keywords_data = generation_data.get('all_keywords', [])
        
        # 핵심 키워드를 KeywordBasicData로 변환
        from .models import KeywordBasicData
        core_keyword = KeywordBasicData(
            keyword=core_keyword_dict.get('keyword', 'Unknown'),
            search_volume=core_keyword_dict.get('search_volume', 0),
            total_products=core_keyword_dict.get('total_products', 0),
            category=core_keyword_dict.get('category', '')
        )
        
        log_manager.add_log(f"🤖 AI 상품명 생성 시작: {core_keyword.keyword}", "info")
        
        # 진행상황 업데이트
        self.left_panel.update_progress(4, "AI 상품명 생성 중...", 20)
        
        # engine_local에서 프롬프트 생성
        from .engine_local import generate_product_name_prompt, PRODUCT_NAME_GENERATION_SYSTEM_PROMPT
        
        # 모든 키워드를 KeywordBasicData 객체로 변환
        selected_keywords = []
        for kw_data in all_keywords_data:
            if isinstance(kw_data, dict):
                selected_keywords.append(KeywordBasicData(
                    keyword=kw_data.get('keyword', ''),
                    search_volume=kw_data.get('search_volume', 0),
                    total_products=kw_data.get('total_products', 0),
                    category=kw_data.get('category', '')
                ))
        
        # Step 2에서 상품명 길이 통계 가져오기 (있다면)
        length_stats = "통계 정보 없음"
        if hasattr(self.right_panel.step2_widget, 'product_name_stats'):
            stats = self.right_panel.step2_widget.product_name_stats
            if stats:
                avg_length = stats.get('average_length', 0)
                min_length = stats.get('min_length', 0)
                max_length = stats.get('max_length', 0)
                length_stats = f"평균 {avg_length:.0f}자, 최소 {min_length}자, 최대 {max_length}자"
        
        # 실제 product_info에서 데이터 가져오기 (Step4에서 입력한 값들)
        actual_product_info = generation_data.get('product_info', {})
        
        prompt_content = generate_product_name_prompt(
            selected_keywords=selected_keywords,
            core_keyword_data=core_keyword,
            brand=actual_product_info.get('brand'),
            material=actual_product_info.get('material'),
            quantity=actual_product_info.get('quantity'),
            length_stats=length_stats
        )
        
        # 4단계 전용 AI 상품명 생성 워커 사용
        from .worker import ProductNameGenerationWorker, worker_manager
        
        self.current_ai_generation_worker = ProductNameGenerationWorker(
            prompt=prompt_content  # 완성된 프롬프트 전달
        )
        
        # 시그널 연결
        self.current_ai_generation_worker.progress_updated.connect(
            lambda progress, message: self.left_panel.update_progress(4, f"AI 상품명 생성: {message}", progress)
        )
        self.current_ai_generation_worker.generation_completed.connect(self.on_ai_product_generation_completed)
        self.current_ai_generation_worker.error_occurred.connect(self.on_ai_product_generation_error)
        
        # 워커 시작
        worker_manager.start_worker(self.current_ai_generation_worker)
    
    def on_ai_product_generation_completed(self, ai_response: str):
        """AI 상품명 생성 완료 처리"""
        log_manager.add_log("✅ AI 상품명 생성 완료", "success")
        
        # AI 응답에서 상품명들 추출 ("최적화된 상품명:" 라인만 추출)
        product_names = []
        if ai_response and ai_response.strip():
            lines = ai_response.strip().split('\n')
            for line in lines:
                cleaned_line = line.strip()
                # "최적화된 상품명:" 으로 시작하는 라인 찾기
                if cleaned_line.startswith("최적화된 상품명:") or cleaned_line.startswith("1. 최적화된 상품명:"):
                    # "최적화된 상품명:" 부분 제거
                    product_name = re.sub(r'^\d*\.\s*최적화된\s*상품명\s*:\s*', '', cleaned_line)
                    product_name = product_name.strip()
                    if product_name and len(product_name) >= 10:  # 최소 길이 체크
                        product_names.append(product_name)
                # 혹시 다른 패턴의 상품명이 있을 경우를 대비한 백업 로직
                elif not any(x in cleaned_line.lower() for x in ['설명:', '원칙', '최적화', '키워드']) and len(cleaned_line) >= 15:
                    # 번호나 불필요한 문자 제거
                    cleaned_line = re.sub(r'^\d+[\.\)\-\s]*', '', cleaned_line)
                    cleaned_line = re.sub(r'^[\-\*\•\s]*', '', cleaned_line)
                    if cleaned_line and len(cleaned_line) >= 10:
                        product_names.append(cleaned_line)
        
        # 최대 10개까지만 사용
        final_product_names = product_names[:10]
        
        if final_product_names:
            count = len(final_product_names)
            log_manager.add_log(f"✅ AI 상품명 생성 완료: {count}개 생성", "success")
            
            # 진행상황 업데이트
            self.left_panel.update_progress(4, f"AI 상품명 생성 완료 {count}개", 100)
            
            # Step 4에 결과 전달
            self.right_panel.step4_widget.on_generation_completed(final_product_names)
        else:
            # 결과가 없으면 에러 처리
            self.on_ai_product_generation_error("AI가 유효한 상품명을 생성하지 못했습니다.")
    
    def on_ai_product_generation_error(self, error_message: str):
        """AI 상품명 생성 에러 처리"""
        log_manager.add_log(f"❌ AI 상품명 생성 실패: {error_message}", "error")
        
        # 진행상황 초기화
        self.left_panel.update_progress(4, "상품명 생성 실패", 0)
        
        # Step 4의 생성 버튼 상태 복원
        if hasattr(self.right_panel, 'step4_widget'):
            step4_widget = self.right_panel.step4_widget
            if hasattr(step4_widget, 'generate_button'):
                step4_widget.generate_button.setEnabled(True)
                step4_widget.generate_button.setText("🚀 AI 상품명 생성하기")
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)