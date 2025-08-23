"""
네이버 상품명 생성기 메인 UI
스텝 네비게이션 + 사이드바 + 메인 영역 구조
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QFrame, QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernCancelButton, ModernHelpButton, ModernCard, ModernProgressBar
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
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
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(20)
        
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
        layout.setContentsMargins(15, 15, 15, 15)
        
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 입력 필드 (확장된 크기)
        self.product_input = QTextEdit()
        self.product_input.setPlaceholderText("키워드를 입력해주세요 (엔터 또는 , 로 구분)")
        self.product_input.setMinimumHeight(150)
        self.product_input.setMaximumHeight(180)
        
        # 자동 줄바꿈 설정
        self.product_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.product_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.product_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.product_input)
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.start_button = ModernPrimaryButton("🔍 분석시작")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.on_start_analysis)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = ModernCancelButton("⏹ 정지")
        self.stop_button.setMinimumHeight(40)
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
        
        # 진행률 바 업데이트 (단계 완료 기준)
        if step == 1:
            step_progress = progress  # 1단계는 직접 progress 값 사용
        else:
            # 2단계부터는 이전 단계 완료분 + 현재 단계 진행률
            step_progress = ((step - 1) * 25) + (progress // 4)
        self.progress_bar.setValue(min(step_progress, 100))
        
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
                font-size: 18px;
                font-weight: 600;
                color: {ModernStyle.COLORS['primary']};
                margin: 4px 0px;
            }}
            QLabel[objectName="status_info"] {{
                font-size: 13px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin: 6px 0px;
            }}
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 상단 네비게이션 버튼들
        nav_layout = QHBoxLayout()
        
        self.prev_button = ModernCancelButton("◀ 이전")
        self.prev_button.setMinimumHeight(40)
        self.prev_button.setMinimumWidth(100)
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.previous_step.emit)
        nav_layout.addWidget(self.prev_button)
        
        nav_layout.addStretch()
        
        self.next_button = ModernPrimaryButton("다음 ▶")
        self.next_button.setMinimumHeight(40)
        self.next_button.setMinimumWidth(100)
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
        reset_layout.addStretch()
        
        self.reset_button = ModernCancelButton("🔄 초기화")
        self.reset_button.setMinimumHeight(40)
        self.reset_button.clicked.connect(self.reset_all.emit)
        reset_layout.addWidget(self.reset_button)
        
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
        
        # 3단계: 심화 분석 결과
        self.step3_widget = Step3AdvancedAnalysisWidget()
        self.content_stack.addWidget(self.step3_widget)
        
        # 4단계: 최종 결과
        self.step4_widget = Step4ResultWidget()
        self.content_stack.addWidget(self.step4_widget)
        
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
        self.cached_product_names = []    # 캐시된 상품명 결과
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI 구성 - 새로운 레이아웃"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 헤더 섹션 (제목 + 사용법)
        self.setup_header(main_layout)
        
        # 콘텐츠 레이아웃 (왼쪽: 진행상황+입력, 오른쪽: 결과+네비게이션)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # 왼쪽 패널 (진행상황 + 핵심제품명 입력)
        self.left_panel = LeftPanel()
        self.left_panel.setFixedWidth(350)
        content_layout.addWidget(self.left_panel)
        
        # 오른쪽 패널 (이전/다음 + 결과 + 초기화)
        self.right_panel = RightPanel()
        content_layout.addWidget(self.right_panel, 1)  # 확장 가능
        
        main_layout.addLayout(content_layout)
        self.apply_styles()
        
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법) - 파워링크와 동일"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("🏷️ 네이버 상품명 생성기")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 버튼 (공용 컴포넌트 사용)
        self.help_button = ModernHelpButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()
        
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
        
    def setup_connections(self):
        """시그널 연결 - 새로운 레이아웃"""
        # 왼쪽 패널 시그널
        self.left_panel.analysis_started.connect(self.on_analysis_started)
        self.left_panel.analysis_stopped.connect(self.on_analysis_stopped)
        
        # 오른쪽 패널 시그널  
        self.right_panel.previous_step.connect(self.go_previous_step)
        self.right_panel.next_step.connect(self.go_next_step)
        self.right_panel.reset_all.connect(self.reset_all_steps)
        
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
        
        # 다음 단계 활성화
        self.right_panel.set_next_enabled(True)
    
    def on_collection_error(self, error_message: str):
        """상품명 수집 에러 처리"""
        log_manager.add_log(f"❌ 상품명 수집 실패: {error_message}", "error")
        
        # 진행상황 초기화
        self.left_panel.update_progress(2, "상품명 수집 실패", 0)
        
    def go_to_step(self, step: int):
        """특정 단계로 이동"""
        if 1 <= step <= 4:
            self.current_step = step
            self.right_panel.go_to_step(step)
            
            # 진행상황 업데이트
            step_names = ["키워드 분석", "키워드 선택", "심화분석", "상품명생성"]
            self.left_panel.update_progress(step, f"{step_names[step-1]} 단계")
            
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
                    # 키워드가 동일함 → 기존 결과 재사용
                    log_manager.add_log(f"✅ 동일한 키워드, 기존 결과 재사용", "info")
                    self.go_to_step(2)
                    self.right_panel.step2_widget.display_product_names(self.cached_product_names)
                    self.right_panel.set_next_enabled(True)
                    return
            
            self.go_to_step(self.current_step + 1)
        
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
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)