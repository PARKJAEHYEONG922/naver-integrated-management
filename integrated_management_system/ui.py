"""
네이버 상품명 생성기 UI - DPI 스케일링 대응 버전
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QScrollArea, QCheckBox, QFrame, QProgressBar,
    QGridLayout, QFormLayout, QSizePolicy, QSplitter, QDialog, QTabWidget,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFontMetrics
from ...ui.modern_style import ModernStyle
from ...ui.common_log import log_manager

class ProductTitleGeneratorWidget(QWidget):
    """네이버 상품명 생성기 메인 위젯"""
    
    def __init__(self):
        super().__init__()
        # AI 분석 디버깅용 데이터 저장 변수들 (확장)
        self.analysis_debug_data = {
            'original_titles': [],     # 원본 상품명 100개
            'title_stats': {},        # 상품명 글자수 통계
            'ai_tokens': [],          # AI가 추출한 토큰들  
            'ai_prompt': '',          # AI에게 보낸 프롬프트
            'ai_response': '',        # AI 응답 원문
            'keyword_combinations': [], # 프로그램이 생성한 조합들
            'combinations_stats': {},  # 조합 통계 정보
            'search_volumes': {},     # 각 키워드별 검색량
            'filtered_keywords': [],  # 검색량 필터링 후 남은 키워드들
            'category_matches': {},   # 카테고리 일치 결과
            'final_keywords': []      # 최종 선별된 키워드들
        }
        self.debug_dialog = None  # 디버그 창 참조
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 제목
        title_label = QLabel("🏷️ 네이버 상품명 생성기")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
        """)
        main_layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("AI와 네이버 API를 활용하여 SEO 최적화된 상품명을 자동 생성합니다.")
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 20px;
            }}
        """)
        main_layout.addWidget(desc_label)
        
        # 입력 섹션 (고정 높이)
        input_group = self.create_input_section()
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameStyle(QFrame.Sunken)
        
        # 상단 컨테이너 (입력 + 구분선)
        top_container = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setSpacing(0)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(input_group)
        top_layout.addWidget(line)
        top_container.setLayout(top_layout)
        
        # 스크롤 가능한 결과 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 스크롤 컨텐츠
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        # 진행상황
        scroll_layout.addWidget(self.create_progress_section())
        # 키워드 선택
        scroll_layout.addWidget(self.create_token_selection_section())
        # 결과
        scroll_layout.addWidget(self.create_result_section())
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        # QSplitter로 위/아래 비율 고정
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        splitter.addWidget(top_container)
        splitter.addWidget(scroll_area)
        
        # 초깃값 비율(위=220px, 아래=나머지)
        splitter.setSizes([220, 1200])
        # 아래쪽을 계속 넓게: 아래 패널에 스트레치
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
        self.apply_styles()
        
        # 입력 그룹이 레이아웃 계산된 후, sizeHint 높이로 상한 고정
        QTimer.singleShot(0, lambda: input_group.setMaximumHeight(input_group.sizeHint().height()))
        
    def create_input_section(self):
        """입력 섹션 - 5개 필드를 2x3 그리드로 배치"""
        group = QGroupBox("📝 기본 정보 입력")
        
        # 폰트 기반 최소 높이 계산
        fm = QFontMetrics(self.font())
        line_h = max(32, fm.height() + 14)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 15)
        main_layout.setSpacing(15)
        
        # 입력 필드 그리드 레이아웃 (2열 x 3행)
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(12)
        
        # 왼쪽 열
        # 브랜드명 (0,0)
        brand_label = QLabel("브랜드명:")
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("예: 수퍼츄")
        self.brand_input.setMinimumHeight(line_h)
        self.brand_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(brand_label, 0, 0)
        grid_layout.addWidget(self.brand_input, 0, 1)
        
        # 핵심제품명 (1,0)
        keyword_label = QLabel("핵심제품명:")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("예: 터키츄")
        self.keyword_input.setMinimumHeight(line_h)
        self.keyword_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(keyword_label, 1, 0)
        grid_layout.addWidget(self.keyword_input, 1, 1)
        
        # 카테고리 (2,0)
        category_label = QLabel("카테고리:")
        self.keyword_category_display = QLineEdit("")
        self.keyword_category_display.setPlaceholderText("분석 후 자동 표시")
        self.keyword_category_display.setReadOnly(True)
        self.keyword_category_display.setMinimumHeight(line_h)
        self.keyword_category_display.setTextMargins(8, 4, 8, 4)
        self.keyword_category_display.setObjectName("category_display")
        grid_layout.addWidget(category_label, 2, 0)
        grid_layout.addWidget(self.keyword_category_display, 2, 1)
        
        # 오른쪽 열
        # 재질/원재료 (0,2)
        material_label = QLabel("재질/원재료:")
        self.material_input = QLineEdit()
        self.material_input.setPlaceholderText("예: 칠면조, 힘줄")
        self.material_input.setMinimumHeight(line_h)
        self.material_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(material_label, 0, 2)
        grid_layout.addWidget(self.material_input, 0, 3)
        
        # 사이즈 (1,2)
        size_label = QLabel("사이즈:")
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("예: S, M, L")
        self.size_input.setMinimumHeight(line_h)
        self.size_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(size_label, 1, 2)
        grid_layout.addWidget(self.size_input, 1, 3)
        
        # 수량/구성 (2,2)
        quantity_label = QLabel("수량/구성:")
        self.spec_input = QLineEdit()
        self.spec_input.setPlaceholderText("예: 20개, 300g")
        self.spec_input.setMinimumHeight(line_h)
        self.spec_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(quantity_label, 2, 2)
        grid_layout.addWidget(self.spec_input, 2, 3)
        
        main_layout.addLayout(grid_layout)
        
        # 버튼 영역 (오른쪽 정렬)
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 왼쪽 공간 채우기
        
        # 상품 분석 시작 버튼
        self.analyze_button = QPushButton("🔍 상품분석시작")
        self.analyze_button.setObjectName("primary_button")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setMinimumWidth(130)
        button_layout.addWidget(self.analyze_button)
        
        # 분석 정지 버튼 (같은 크기)
        self.stop_button = QPushButton("⏹️ 분석정지")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)  # 처음엔 비활성화
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setMinimumWidth(130)
        button_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(button_layout)
        
        group.setLayout(main_layout)
        
        # SizePolicy 설정
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        group.setObjectName("input_group")
        
        return group
        
    def create_progress_section(self):
        """진행상황 섹션 - AI 분석 확인 버튼 포함"""
        group = QGroupBox("2️⃣ 분석 진행 상황")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 15)
        main_layout.setSpacing(15)
        
        # 상단: 제목과 AI 분석 확인 버튼
        header_layout = QHBoxLayout()
        
        # 왼쪽: 분석 진행상황 텍스트
        progress_title = QLabel("분석 진행상황")
        progress_title.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(progress_title)
        
        header_layout.addStretch()  # 공간 채우기
        
        # 오른쪽: AI 분석 확인 버튼
        self.ai_debug_button = QPushButton("🤖 AI 분석 확인")
        self.ai_debug_button.setObjectName("debug_button")
        self.ai_debug_button.clicked.connect(self.show_ai_analysis_debug)
        self.ai_debug_button.setEnabled(True)
        self.ai_debug_button.setMinimumHeight(35)
        self.ai_debug_button.setMinimumWidth(120)
        header_layout.addWidget(self.ai_debug_button)
        
        main_layout.addLayout(header_layout)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"color: {ModernStyle.COLORS['border']};")
        main_layout.addWidget(line)
        
        # 진행바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 상태 메시지 영역
        self.status_label = QLabel("분석을 시작하려면 위의 정보를 입력하고 '상품 분석 시작' 버튼을 클릭하세요.")
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(2, 2, 2, 2)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ModernStyle.COLORS['bg_input']};
                padding: 15px;
                border-radius: 8px;
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 14px;
                min-height: 60px;
            }}
        """)
        main_layout.addWidget(self.status_label)
        
        group.setLayout(main_layout)
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        return group
        
    def create_token_selection_section(self):
        """키워드 선택 섹션 - 반응형 그리드"""
        self.token_group = QGroupBox("3️⃣ 키워드 선택")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 설명 - 줄바꿈 지원
        info_label = QLabel("AI가 분석한 키워드 중에서 사용하고 싶은 키워드를 선택하세요.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        layout.addWidget(info_label)
        
        # 키워드 체크박스 영역 - MaxHeight 제거
        self.token_scroll = QScrollArea()
        self.token_scroll.setWidgetResizable(True)
        self.token_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.token_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.token_widget = QWidget()
        self.token_layout = QGridLayout()
        self.token_layout.setSpacing(10)
        self.token_widget.setLayout(self.token_layout)
        self.token_scroll.setWidget(self.token_widget)
        
        # 폰트 기반 최소 높이 - 키워드 선택 칸 두 배로 증가
        fm = QFontMetrics(self.font())
        min_scroll_height = fm.height() * 6 + 60  # 6줄 정도 (기존 3줄의 두 배)
        self.token_scroll.setMinimumHeight(min_scroll_height)
        
        layout.addWidget(self.token_scroll)
        
        # 생성 버튼
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("✨ 상품명 생성")
        self.generate_button.setEnabled(False)
        self.generate_button.setObjectName("success_button")
        button_layout.addWidget(self.generate_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.token_group.setLayout(layout)
        
        # SizePolicy 설정: 키워드 선택 영역에 더 많은 공간 할당
        self.token_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # 스크롤 영역도 Expanding으로 설정하여 가용 공간 최대 활용
        self.token_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        return self.token_group
        
    def create_result_section(self):
        """결과 섹션 - Expanding 지원"""
        self.result_group = QGroupBox("4️⃣ 생성된 상품명")
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 결과 텍스트 - MaxHeight 제거
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("생성된 상품명이 여기에 표시됩니다...")
        self.result_text.document().setDocumentMargin(10)  # 문서 마진 추가
        
        # 폰트 기반 최소 높이 - 상품명 생성 칸 줄임
        fm = QFontMetrics(self.font())
        min_text_height = fm.height() * 2 + 20  # 2줄 정도 (기존 4줄에서 절반으로)
        self.result_text.setMinimumHeight(min_text_height)
        # 최대 높이도 제한하여 너무 커지지 않도록
        max_text_height = fm.height() * 3 + 30  # 최대 3줄
        self.result_text.setMaximumHeight(max_text_height)
        
        layout.addWidget(self.result_text)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        self.copy_button = QPushButton("📋 클립보드에 복사")
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        self.export_button = QPushButton("💾 엑셀로 저장")
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.result_group.setLayout(layout)
        
        # SizePolicy 설정: 상품명 결과 영역은 고정 크기로 설정
        self.result_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        # 텍스트 위젯도 Fixed로 설정하여 크기 제한
        self.result_text.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        return self.result_group
        
    def set_input_compact(self, compact: bool):
        """입력 섹션 컴팩트 모드 토글"""
        if compact:
            # 더 작게 만들기
            for w in (self.brand_input, self.keyword_input, self.spec_input):
                w.setMinimumHeight(24)
        else:
            # 원래 크기로 복원
            fm = QFontMetrics(self.font())
            line_h = max(28, fm.height() + 8)
            for w in (self.brand_input, self.keyword_input, self.spec_input):
                w.setMinimumHeight(line_h)
        
    def setup_connections(self):
        """시그널 연결"""
        self.analyze_button.clicked.connect(self.start_analysis)
        self.stop_button.clicked.connect(self.stop_analysis)
        self.generate_button.clicked.connect(self.generate_titles)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.export_button.clicked.connect(self.export_to_excel)
        
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 10px;
                margin: 15px 0;
                padding-top: 18px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                top: 0px;
            }}
            QLineEdit {{
                padding: 6px 10px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: {ModernStyle.COLORS['bg_input']};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QTextEdit {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_input']};
                font-size: 14px;
                padding: 15px;
            }}
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                min-width: 140px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                color: {ModernStyle.COLORS['text_muted']};
            }}
            QPushButton#primary_button {{
                background-color: {ModernStyle.COLORS['primary']};
                font-size: 14px;
                padding: 10px 18px;
                min-width: 160px;
            }}
            QPushButton#compact_primary_button {{
                background-color: {ModernStyle.COLORS['primary']};
                font-size: 13px;
                padding: 10px 20px;
                min-width: 144px;
                border-radius: 6px;
            }}
            QPushButton#compact_primary_button:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
            QPushButton#success_button {{
                background-color: {ModernStyle.COLORS['success']};
                font-size: 14px;
                padding: 12px 20px;
                min-width: 140px;
            }}
            QPushButton#success_button:hover {{
                background-color: {ModernStyle.COLORS['secondary_hover']};
            }}
            QCheckBox {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_primary']};
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_input']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ModernStyle.COLORS['primary']};
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QPushButton#debug_button {{
                background-color: #9ca3af;
                color: white;
                font-size: 13px;
                padding: 12px 16px;
                min-width: 120px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton#debug_button:hover {{
                background-color: #6b7280;
            }}
            QPushButton#debug_button:disabled {{
                background-color: #d1d5db;
                color: white;
            }}
            QLineEdit#category_display {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_muted']};
                border: 2px solid {ModernStyle.COLORS['border']};
            }}
            QPushButton#stop_button {{
                background-color: #ef4444;
                color: white;
                font-size: 13px;
                padding: 12px 16px;
                min-width: 120px;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton#stop_button:hover {{
                background-color: #dc2626;
            }}
            QPushButton#stop_button:disabled {{
                background-color: #d1d5db;
                color: #9ca3af;
            }}
        """)
        
        # 입력 그룹만 슬림 오버라이드
        self.setStyleSheet(self.styleSheet() + f"""
            QGroupBox#input_group {{
                padding-top: 16px;
                margin: 6px 0;
            }}
            QGroupBox#input_group QLineEdit {{
                min-height: 18px;
                padding: 4px 8px;
            }}
        """)
        
    def start_analysis(self):
        """분석 시작"""
        brand = self.brand_input.text().strip()
        keyword = self.keyword_input.text().strip()
        spec = self.spec_input.text().strip()
        
        # 새로 추가된 필드들 (선택사항이므로 검증에서 제외)
        material = self.material_input.text().strip() if hasattr(self, 'material_input') else ""
        size = self.size_input.text().strip() if hasattr(self, 'size_input') else ""
        
        # 필수 필드만 검사 (브랜드, 핵심제품명, 수량/구성)
        if not all([brand, keyword, spec]):
            log_manager.add_log("❌ 브랜드명, 핵심제품명, 수량/구성 필드를 모두 입력해주세요.", "error")
            return
        
        # API 설정 확인
        from .services import naver_shopping_service, ai_tokenizer_service
        
        if not naver_shopping_service.is_configured():
            log_manager.add_log("❌ 네이버 쇼핑 API가 설정되지 않았습니다. API 설정에서 설정해주세요.", "error")
            return
        
        if not ai_tokenizer_service.get_available_provider():
            log_manager.add_log("❌ AI API가 설정되지 않았습니다. API 설정에서 AI API를 설정해주세요.", "error")
            return
            
        # UI 상태 변경
        self.analyze_button.setEnabled(False)  # 분석 시작 버튼 비활성화
        self.stop_button.setEnabled(True)      # 정지 버튼 활성화 (항상 보임)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 카테고리 입력창 초기화 및 표시
        self.keyword_category_display.setText("분석 중...")
        self.keyword_category_display.setVisible(True)
        
        log_manager.add_log(f"🔍 상품 분석 시작: {brand} - {keyword} ({spec})", "info")
        
        # 분석 데이터 초기화 (실시간 업데이트 준비)
        self.analysis_debug_data = {
            'original_titles': [],
            'title_stats': {},
            'ai_tokens': [],
            'ai_prompt': '',
            'ai_response': '',
            'keyword_combinations': [],
            'combinations_stats': {},
            'search_volumes': {},
            'filtered_keywords': [],
            'category_matches': {},
            'final_keywords': []
        }
        
        # 분석 시작과 함께 상단 컴팩트 모드
        self.set_input_compact(True)
        
        # 실제 분석 시작
        self.start_real_analysis()
    
    def stop_analysis(self):
        """분석 정지"""
        if hasattr(self, 'analysis_worker') and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            self.analysis_worker.wait()  # 워커 종료까지 대기
            log_manager.add_log("⏹️ 분석이 중단되었습니다.", "warning")
            
            # 버튼 상태 복원
            self.stop_button.setEnabled(False)
            self.analyze_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            
            # 상태 메시지 초기화
            self.status_label.setText("분석을 시작하려면 위의 정보를 입력하고 '상품 분석 시작' 버튼을 클릭하세요.")
    
    def start_real_analysis(self):
        """실제 분석 시작"""
        from .worker import AnalysisWorker
        
        brand = self.brand_input.text().strip()
        keyword = self.keyword_input.text().strip()
        spec = self.spec_input.text().strip()
        
        # 워커 스레드 시작
        self.analysis_worker = AnalysisWorker(brand, keyword, spec)
        self.analysis_worker.progress_updated.connect(self.on_progress_updated)
        self.analysis_worker.category_found.connect(self.on_category_found)  # 카테고리 즉시 표시용
        self.analysis_worker.debug_step_updated.connect(self.on_debug_step_updated)  # 실시간 디버그 데이터
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.start()
    
    def stop_analysis(self):
        """분석 정지"""
        if hasattr(self, 'analysis_worker') and self.analysis_worker and self.analysis_worker.isRunning():
            # 워커 스레드 취소 요청
            self.analysis_worker.cancel()
            
            # UI 상태 복원
            self.stop_button.setEnabled(False)
            self.analyze_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.status_label.setText("분석이 중단되었습니다.")
            
            from ...ui.common_log import log_manager
            log_manager.add_log("⏹️ 분석이 사용자에 의해 중단되었습니다.", "warning")
    
    def on_progress_updated(self, progress: int, message: str):
        """진행률 업데이트"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def on_category_found(self, category: str):
        """카테고리 발견 즉시 UI 업데이트"""
        print(f"DEBUG: on_category_found 호출됨 - 카테고리: '{category}'")
        self.show_keyword_category(category)
    
    def on_debug_step_updated(self, step_name: str, data):
        """실시간 디버그 단계 업데이트"""
        print(f"DEBUG: {step_name} 단계 데이터 수신")
        
        if step_name == "original_titles":
            # 새로운 형식의 데이터 처리
            if isinstance(data, dict) and 'titles' in data:
                self.analysis_debug_data['original_titles'] = data['titles']
                self.analysis_debug_data['title_stats'] = {
                    'count': data['count'],
                    'avg_length': data['avg_length'],
                    'min_length': data['min_length'],
                    'max_length': data['max_length']
                }
            else:
                # 기존 형식 호환성 유지
                self.analysis_debug_data['original_titles'] = data
        elif step_name == "ai_analysis":
            # 새로운 키 이름과 하위 호환성 지원
            self.analysis_debug_data['ai_keywords'] = data.get('ai_keywords', data.get('ai_tokens', []))
            self.analysis_debug_data['ai_tokens'] = data.get('ai_keywords', data.get('ai_tokens', []))  # 하위 호환성
            self.analysis_debug_data['ai_prompt'] = data.get('ai_prompt', '')
            self.analysis_debug_data['ai_response'] = data.get('ai_response', '')
            self.analysis_debug_data['provider'] = data.get('provider', '')
            self.analysis_debug_data['total_keywords'] = data.get('total_keywords', 0)
        elif step_name == "combinations":
            self.analysis_debug_data['keyword_combinations'] = data['combinations']
            self.analysis_debug_data['combinations_stats'] = {
                'single_count': data['single_count'],
                'two_word_count': data['two_word_count'],
                'three_word_count': data['three_word_count'],
                'all_keywords': data.get('all_keywords', [])
            }
        elif step_name == "search_volumes":
            self.analysis_debug_data['search_volumes'] = data
        elif step_name == "volume_filtered":
            self.analysis_debug_data['filtered_keywords'] = list(data['filtered_combinations'].keys())
        elif step_name == "category_filtered":
            self.analysis_debug_data['category_matches'] = data['category_matches']
            self.analysis_debug_data['final_keywords'] = list(data['final_combinations'].keys())
        elif step_name == "final_result":
            # 최종 결과 데이터 저장
            self.analysis_debug_data['final_filtered_keywords'] = data['final_filtered_keywords']
            self.analysis_debug_data['final_tokens'] = data['final_tokens']
            self.analysis_debug_data['removed_by_category'] = data['removed_by_category']
            self.analysis_debug_data['total_processed'] = data['total_processed']
            self.analysis_debug_data['after_volume_filter'] = data['after_volume_filter']
            self.analysis_debug_data['final_count'] = data['final_count']
            
            # 모든 중간 데이터 영구 저장 (데이터 지속성 보장)
            if 'search_volumes' in data:
                self.analysis_debug_data['search_volumes'] = data['search_volumes']
            if 'volume_filtered_combinations' in data:
                self.analysis_debug_data['volume_filtered_combinations'] = data['volume_filtered_combinations']
                self.analysis_debug_data['filtered_keywords'] = list(data['volume_filtered_combinations'].keys())
            if 'category_matches' in data:
                self.analysis_debug_data['category_matches'] = data['category_matches']
            
            # 분석 완료 플래그 설정 (디버그 다이얼로그에서 완전한 데이터 표시용)
            self.analysis_debug_data['analysis_completed'] = True
            
            print(f"DEBUG: final_result에서 영구 저장된 데이터:")
            print(f"  - search_volumes: {len(self.analysis_debug_data.get('search_volumes', {}))}")
            print(f"  - volume_filtered_combinations: {len(self.analysis_debug_data.get('volume_filtered_combinations', {}))}")
            print(f"  - category_matches: {len(self.analysis_debug_data.get('category_matches', {}))}")
            print(f"  - final_filtered_keywords: {len(self.analysis_debug_data.get('final_filtered_keywords', {}))}")
        
        # 디버그 창이 열려있으면 실시간 업데이트
        if self.debug_dialog and self.debug_dialog.isVisible():
            self.debug_dialog.update_step(step_name, data)
    
    def on_analysis_completed(self, tokens: list, search_volumes: dict, category_info: dict, keyword_categories: dict, main_keyword_category: str):
        """분석 완료"""
        print(f"DEBUG: on_analysis_completed 호출됨")
        print(f"DEBUG: tokens 개수: {len(tokens)}")
        print(f"DEBUG: search_volumes 타입: {type(search_volumes)}, 개수: {len(search_volumes) if isinstance(search_volumes, dict) else 'N/A'}")
        print(f"DEBUG: tokens 내용: {tokens[:5] if tokens else 'None'}...")
        print(f"DEBUG: search_volumes 샘플: {dict(list(search_volumes.items())[:3]) if isinstance(search_volumes, dict) else search_volumes}")
        
        self.search_volumes = search_volumes  # 나중에 상품명 생성에서 사용
        self.category_info = category_info
        self.keyword_categories = keyword_categories  # 각 키워드별 카테고리 정보
        
        # 카테고리는 이미 on_category_found에서 표시했으므로 생략
        
        # 토큰 체크박스 추가 (카테고리 정보 포함)
        self.add_token_checkboxes(tokens)
        
        # 버튼 상태 복원
        self.stop_button.setEnabled(False)    # 정지 버튼 비활성화
        self.analyze_button.setEnabled(True)  # 분석 시작 버튼 활성화
        
        log_manager.add_log("✅ 분석 완료! 키워드를 선택해주세요.", "success")
        log_manager.add_log(f"📂 메인 카테고리: {category_info['main_category']} ({category_info['ratio']:.1f}%)", "info")
        log_manager.add_log(f"🎯 핵심키워드 카테고리: {main_keyword_category}", "info")
    
    def on_analysis_error(self, error_message: str):
        """분석 오류"""
        log_manager.add_log(f"❌ {error_message}", "error")
        
        # 버튼 상태 복원
        self.stop_button.setEnabled(False)
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
    def simulate_analysis(self):
        """분석 시뮬레이션"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        self.timer.start(100)
        
    def update_progress(self):
        """진행상황 업데이트"""
        self.progress_value += 2
        self.progress_bar.setValue(self.progress_value)
        
        if self.progress_value == 20:
            self.status_label.setText("📊 네이버 쇼핑에서 상위 100위 상품 데이터를 수집하는 중...")
        elif self.progress_value == 40:
            self.status_label.setText("🤖 AI가 상품명을 토큰화하는 중...")
        elif self.progress_value == 60:
            self.status_label.setText("🔍 월검색량 및 카테고리 정보를 조회하는 중...")
        elif self.progress_value == 80:
            self.status_label.setText("✨ 키워드 필터링 및 정리하는 중...")
        elif self.progress_value >= 100:
            self.timer.stop()
            self.analysis_complete()
            
    def analysis_complete(self):
        """분석 완료"""
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ 분석 완료! 아래에서 사용할 키워드를 선택하세요.")
        
        # 샘플 키워드들
        sample_tokens = [
            "강아지", "간식", "수제", "대용량", "오래먹는", 
            "프리미엄", "터키", "닭가슴살", "무첨가", "천연"
        ]
        
        self.add_token_checkboxes(sample_tokens)
        self.analyze_button.setEnabled(True)
        log_manager.add_log("✅ 분석 완료! 키워드를 선택해주세요.", "success")
        
    def show_keyword_category(self, main_keyword_category: str):
        """핵심 키워드 카테고리 표시"""
        print(f"DEBUG: show_keyword_category 호출됨 - 카테고리: '{main_keyword_category}'")  # 디버깅용
        
        if main_keyword_category and main_keyword_category.strip() and main_keyword_category != "미분류(0%)":
            try:
                # 카테고리에서 전체 경로와 퍼센트 추출
                if '(' in main_keyword_category and ')' in main_keyword_category:
                    category_part = main_keyword_category.split('(')[0].strip()
                    percentage_part = main_keyword_category.split('(')[1].split(')')[0]
                    display_text = f"{category_part} ({percentage_part})"
                else:
                    display_text = main_keyword_category
                
                print(f"DEBUG: 카테고리 표시 - 텍스트: '{display_text}'")  # 디버깅용
                self.keyword_category_display.setText(display_text)
                self.keyword_category_display.setVisible(True)
                
                # 강제로 UI 업데이트
                self.keyword_category_display.update()
                
            except Exception as e:
                print(f"DEBUG: 카테고리 표시 오류: {e}")  # 디버깅용
                self.keyword_category_display.setText("분석 오류")
                self.keyword_category_display.setVisible(True)
        else:
            print(f"DEBUG: 카테고리 숨김 - 값: '{main_keyword_category}'")  # 디버깅용
            self.keyword_category_display.setText("분석 중...")
            self.keyword_category_display.setVisible(True)  # 일단 표시하도록 변경
    
    def add_token_checkboxes(self, tokens):
        """키워드 체크박스 추가 - 카테고리 정보 포함"""
        print(f"DEBUG: add_token_checkboxes 호출됨, tokens 개수: {len(tokens) if tokens else 0}")
        print(f"DEBUG: tokens 내용: {tokens[:10] if tokens else 'None'}...")
        
        # 기존 체크박스들 제거
        for i in reversed(range(self.token_layout.count())):
            item = self.token_layout.itemAt(i)
            if item:
                item.widget().deleteLater()
        
        # 뷰포트 폭 기반으로 컬럼 수 계산 (검색량 + 카테고리 정보로 더 넓게)
        viewport_width = self.token_scroll.viewport().width()
        checkbox_width = 250  # 검색량과 카테고리 정보 포함으로 더 넓게
        max_cols = max(1, min(3, viewport_width // checkbox_width))
        
        # 새 체크박스들 추가
        self.token_checkboxes = []
        row, col = 0, 0
        
        for token in tokens:
            # 해당 토큰의 검색량 정보 찾기
            search_volume = ""
            if hasattr(self, 'search_volumes') and token in self.search_volumes:
                volume = self.search_volumes[token]
                search_volume = f"월 {volume:,}회"
            
            # 해당 토큰의 카테고리 정보 찾기
            token_category = ""
            if hasattr(self, 'keyword_categories'):
                if token in self.keyword_categories:
                    category_info = self.keyword_categories[token]
                    if category_info and category_info != "미분류(0%)":
                        # 카테고리에서 마지막 카테고리명과 퍼센트 추출
                        if '(' in category_info and ')' in category_info:
                            category_path = category_info.split('(')[0].strip()
                            percentage = category_info.split('(')[1].split(')')[0]
                            
                            # 카테고리 경로에서 마지막 카테고리명 추출
                            # 다양한 구분자 지원: >, /, \, -
                            separators = ['>', '/', '\\', '-', '|']
                            last_category = category_path
                            for separator in separators:
                                if separator in category_path:
                                    last_category = category_path.split(separator)[-1].strip()
                                    break
                            
                            # 빈 카테고리명이면 전체 경로 사용
                            if not last_category:
                                last_category = category_path
                            
                            token_category = f"{last_category}({percentage})"
                        else:
                            # 퍼센트 정보가 없는 경우 그대로 표시
                            token_category = category_info
            
            # 체크박스 텍스트를 명확하게 구분하여 표시
            # 형식: "키워드 / 월1,000 (카테고리70%)"
            checkbox_text = token
            
            if search_volume or token_category:
                additional_info = []
                if search_volume:
                    additional_info.append(search_volume)
                if token_category:
                    additional_info.append(f"({token_category})")
                
                if additional_info:
                    checkbox_text += f" / {' '.join(additional_info)}"
            checkbox = QCheckBox(checkbox_text)
            
            # 툴팁에 상세 정보 추가
            tooltip_parts = [f"키워드: {token}"]
            if search_volume:
                tooltip_parts.append(f"검색량: {search_volume}")
            if token_category:
                tooltip_parts.append(f"카테고리 일치율: {token_category}")
            checkbox.setToolTip("\n".join(tooltip_parts))
            checkbox.toggled.connect(self.on_token_selection_changed)
            self.token_checkboxes.append(checkbox)
            
            self.token_layout.addWidget(checkbox, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def on_token_selection_changed(self):
        """키워드 선택 변경"""
        selected_count = sum(1 for cb in self.token_checkboxes if cb.isChecked())
        self.generate_button.setEnabled(selected_count > 0)
        
    def generate_titles(self):
        """상품명 생성"""
        # 체크박스 텍스트에서 키워드 부분만 추출
        # 새 형식: "키워드 / 월1,000 (카테고리70%)"
        selected_tokens = []
        for cb in self.token_checkboxes:
            if cb.isChecked():
                text = cb.text()
                # '/' 앞의 키워드 부분만 추출
                if ' / ' in text:
                    keyword_part = text.split(' / ')[0].strip()
                else:
                    # '/' 가 없으면 전체 텍스트가 키워드
                    keyword_part = text.strip()
                
                if keyword_part:
                    selected_tokens.append(keyword_part)
        
        if not selected_tokens:
            log_manager.add_log("❌ 키워드를 선택해주세요.", "error")
            return
            
        log_manager.add_log(f"✨ 선택된 키워드로 상품명 생성 중: {', '.join(selected_tokens)}", "info")
        
        # 실제 생성
        self.start_title_generation(selected_tokens)
    
    def start_title_generation(self, selected_tokens: list):
        """실제 상품명 생성 시작"""
        from .worker import TitleGenerationWorker
        
        brand = self.brand_input.text().strip()
        keyword = self.keyword_input.text().strip()
        spec = self.spec_input.text().strip()
        search_volumes = getattr(self, 'search_volumes', {})
        
        # 버튼 비활성화
        self.generate_button.setEnabled(False)
        
        # 워커 스레드 시작
        self.title_worker = TitleGenerationWorker(brand, keyword, spec, selected_tokens, search_volumes)
        self.title_worker.titles_generated.connect(self.on_titles_generated)
        self.title_worker.progress_updated.connect(self.on_progress_updated)  # 진행률 업데이트 연결
        self.title_worker.error_occurred.connect(self.on_title_generation_error)
        self.title_worker.start()
    
    def on_titles_generated(self, titles: list):
        """상품명 생성 완료"""
        self.generate_button.setEnabled(True)
        
        # 생성된 데이터 저장 (엑셀 저장용)
        self.generated_titles_data = titles
        
        # 결과 텍스트 구성
        result_text = "🏆 SEO 최적화 상품명 (점수순):\n\n"
        
        for i, title_data in enumerate(titles, 1):
            title = title_data['title']
            score = title_data['score']
            volume = title_data['search_volume']
            char_count = title_data['char_count']
            
            result_text += f"{i}. {title}\n"
            result_text += f"   📊 SEO점수: {score:.1f} | 예상검색량: {volume}회 | 글자수: {char_count}자\n\n"
        
        # 추가 정보
        if hasattr(self, 'category_info'):
            result_text += f"\n📂 분석 카테고리: {self.category_info['main_category']}\n"
            result_text += f"🎯 카테고리 일치율: {self.category_info['ratio']:.1f}%\n"
        
        self.result_text.setPlainText(result_text)
        
        # 버튼 활성화
        self.copy_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        log_manager.add_log("🎉 상품명 생성 완료!", "success")
    
    def on_title_generation_error(self, error_message: str):
        """상품명 생성 오류"""
        self.generate_button.setEnabled(True)
        log_manager.add_log(f"❌ 상품명 생성 오류: {error_message}", "error")
        
    def simulate_generation(self, tokens):
        """상품명 생성 시뮬레이션"""
        brand = self.brand_input.text().strip()
        spec = self.spec_input.text().strip()
        
        # 샘플 상품명들 생성
        sample_titles = [
            f"{brand} {' '.join(tokens[:3])} {spec}",
            f"{brand} {tokens[0]} {' '.join(tokens[1:4])} {spec}",
            f"{brand} {''.join(tokens[:2])} {' '.join(tokens[2:4])} {spec}",
        ]
        
        result_text = "🏆 추천 상품명 (SEO 점수순):\\n\\n"
        for i, title in enumerate(sample_titles, 1):
            result_text += f"{i}. {title}\\n"
            result_text += f"   📊 예상 월검색량: {1000-i*200}회 | 글자수: {len(title)}자\\n\\n"
        
        self.result_text.setPlainText(result_text)
        
        # 버튼 활성화
        self.copy_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        log_manager.add_log("🎉 상품명 생성 완료!", "success")
        
    def copy_to_clipboard(self):
        """클립보드 복사"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_text.toPlainText())
        log_manager.add_log("📋 클립보드에 복사되었습니다.", "success")
        
    def export_to_excel(self):
        """엑셀 저장"""
        if not hasattr(self, 'generated_titles_data'):
            log_manager.add_log("❌ 저장할 데이터가 없습니다.", "error")
            return
        
        try:
            from PySide6.QtWidgets import QFileDialog
            from datetime import datetime
            import pandas as pd
            
            # 파일 저장 위치 선택
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            brand = self.brand_input.text().strip()
            keyword = self.keyword_input.text().strip()
            
            default_filename = f"상품명생성_{brand}_{keyword}_{timestamp}.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "결과 저장 (엑셀)",
                default_filename,
                "Excel 파일 (*.xlsx);;모든 파일 (*)"
            )
            
            if file_path:
                # 엑셀 데이터 구성
                excel_data = []
                
                # 상품명 데이터 추가
                for i, title_data in enumerate(self.generated_titles_data, 1):
                    excel_data.append({
                        '순위': i,
                        '상품명': title_data['title'],
                        'SEO점수': title_data['score'],
                        '예상검색량': title_data['search_volume'],
                        '글자수': title_data['char_count']
                    })
                
                # DataFrame 생성
                df = pd.DataFrame(excel_data)
                
                # 분석 정보 시트용 데이터
                category_info = getattr(self, 'category_info', {})
                selected_tokens = [cb.text()[1:] for cb in self.token_checkboxes if cb.isChecked()]
                
                analysis_info = pd.DataFrame([
                    ['브랜드명', brand],
                    ['핵심키워드', keyword],
                    ['규격/수량', self.spec_input.text().strip()],
                    ['분석시간', timestamp],
                    ['메인카테고리', category_info.get('main_category', '')],
                    ['카테고리일치율(%)', f"{category_info.get('ratio', 0):.1f}"],
                    ['선택된토큰', ', '.join(selected_tokens)]
                ], columns=['항목', '값'])
                
                # 엑셀로 저장 (여러 시트)
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    # 상품명 시트
                    df.to_excel(writer, sheet_name='생성된상품명', index=False)
                    
                    # 분석 정보 시트
                    analysis_info.to_excel(writer, sheet_name='분석정보', index=False)
                    
                    # 워크시트 스타일링
                    workbook = writer.book
                    
                    # 상품명 시트 스타일링
                    titles_sheet = writer.sheets['생성된상품명']
                    titles_sheet.column_dimensions['B'].width = 50  # 상품명 열 너비 확장
                    
                    # 분석정보 시트 스타일링
                    info_sheet = writer.sheets['분석정보']
                    info_sheet.column_dimensions['A'].width = 15
                    info_sheet.column_dimensions['B'].width = 40
                
                log_manager.add_log(f"📊 엑셀 파일이 저장되었습니다: {file_path}", "success")
            
        except ImportError:
            log_manager.add_log("❌ pandas 라이브러리가 필요합니다. 'pip install pandas openpyxl'을 실행해주세요.", "error")
        except Exception as e:
            log_manager.add_log(f"❌ 엑셀 저장 오류: {str(e)}", "error")
    
    def show_ai_analysis_debug(self):
        """실시간 분석 과정 디버그 창 표시"""
        # 디버그 창이 이미 열려있다면 앞으로 가져오기
        if self.debug_dialog and self.debug_dialog.isVisible():
            self.debug_dialog.raise_()
            self.debug_dialog.activateWindow()
            return
        
        # 디버그 창 생성 (실시간 업데이트용)
        self.debug_dialog = RealTimeDebugDialog(self, self.analysis_debug_data)
        self.debug_dialog.show()


class RealTimeDebugDialog(QDialog):
    """실시간 분석 과정 디버그 창"""
    
    def __init__(self, parent, debug_data):
        super().__init__(parent)
        self.debug_data = debug_data
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("실시간 분석 과정 확인")
        self.setModal(False)  # 모달 없이 띄우기
        self.resize(1000, 700)
        
        layout = QVBoxLayout()
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        
        # 각 탭 생성
        self.create_titles_tab()
        self.create_ai_tab()
        self.create_combinations_tab()
        self.create_search_volumes_tab()
        self.create_category_tab()
        self.create_filtering_tab()
        self.create_final_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 닫기 버튼
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.close)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_titles_tab(self):
        """1단계: 원본 상품명 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("1단계: 네이버에서 수집한 상품명들")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        self.titles_text = QPlainTextEdit()
        self.titles_text.setReadOnly(True)
        layout.addWidget(self.titles_text)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "1. 상품명 수집")
        
        # 데이터 있으면 초기화
        if self.debug_data['original_titles']:
            self.update_titles_tab()
    
    def create_ai_tab(self):
        """2단계: AI 분석 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("2단계: AI 토큰화 분석")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        # 서브 탭 위젯
        ai_tab_widget = QTabWidget()
        
        # AI 추출 키워드
        tokens_tab = QWidget()
        tokens_layout = QVBoxLayout()
        tokens_layout.addWidget(QLabel("AI가 추출한 키워드:"))
        self.ai_tokens_text = QPlainTextEdit()
        self.ai_tokens_text.setReadOnly(True)
        tokens_layout.addWidget(self.ai_tokens_text)
        tokens_tab.setLayout(tokens_layout)
        ai_tab_widget.addTab(tokens_tab, "추출 키워드")
        
        # AI 프롬프트
        prompt_tab = QWidget()
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(QLabel("AI에게 보낸 프롬프트:"))
        self.ai_prompt_text = QPlainTextEdit()
        self.ai_prompt_text.setReadOnly(True)
        prompt_layout.addWidget(self.ai_prompt_text)
        prompt_tab.setLayout(prompt_layout)
        ai_tab_widget.addTab(prompt_tab, "프롬프트")
        
        # AI 응답
        response_tab = QWidget()
        response_layout = QVBoxLayout()
        response_layout.addWidget(QLabel("AI 응답 원문:"))
        self.ai_response_text = QPlainTextEdit()
        self.ai_response_text.setReadOnly(True)
        response_layout.addWidget(self.ai_response_text)
        response_tab.setLayout(response_layout)
        ai_tab_widget.addTab(response_tab, "AI 응답")
        
        layout.addWidget(ai_tab_widget)
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "2. AI 분석")
        
        # 데이터 있으면 초기화
        self.update_ai_tab()
    
    def get_current_debug_data(self):
        """현재 유효한 디버그 데이터 반환 (실시간 또는 저장된 데이터)"""
        # 부모 창의 실시간 데이터 우선 사용
        if hasattr(self.parent(), 'analysis_debug_data'):
            return self.parent().analysis_debug_data
        return self.debug_data
    
    def create_combinations_tab(self):
        """3단계: 키워드 조합 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("3단계: 프로그램이 생성한 키워드 조합들")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        self.combinations_stats = QLabel("조합 통계: 계산 중...")
        layout.addWidget(self.combinations_stats)
        
        self.combinations_text = QPlainTextEdit()
        self.combinations_text.setReadOnly(True)
        layout.addWidget(self.combinations_text)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "3. 키워드 조합")
        
        # 데이터 있으면 초기화
        self.update_combinations_tab()
    
    def create_search_volumes_tab(self):
        """4단계: 검색량 조회 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("4단계: 네이버 검색광고 API 검색량 조회")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        self.search_volumes_text = QPlainTextEdit()
        self.search_volumes_text.setReadOnly(True)
        layout.addWidget(self.search_volumes_text)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "4. 검색량 조회")
        
        # 저장된 데이터가 있으면 초기화 (파라미터 없이 호출하면 내부에서 저장된 데이터 사용)
        self.update_search_volumes_tab(None)
    
    def create_category_tab(self):
        """5단계: 카테고리 조회 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("5단계: 각 키워드별 카테고리 조회")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        self.category_text = QPlainTextEdit()
        self.category_text.setReadOnly(True)
        layout.addWidget(self.category_text)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "5. 카테고리 조회")
        
        # 저장된 데이터가 있으면 초기화 (파라미터 없이 호출하면 내부에서 저장된 데이터 사용)
        self.update_category_tab(None)
    
    def create_filtering_tab(self):
        """6단계: 필터링 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("6단계: 검색량 & 카테고리 필터링")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        self.filtering_text = QPlainTextEdit()
        self.filtering_text.setReadOnly(True)
        layout.addWidget(self.filtering_text)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "6. 필터링")
        
        # 저장된 데이터가 있으면 초기화
        current_data = self.get_current_debug_data()
        if current_data.get('volume_filtered_combinations'):
            filter_data = {
                'filtered_combinations': current_data['volume_filtered_combinations'],
                'removed_count': current_data.get('volume_removed_count', 0)
            }
            self.update_filtering_tab(filter_data)
    
    def create_final_tab(self):
        """7단계: 최종 결과 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("7단계: 최종 선별된 키워드들")
        label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(label)
        
        self.final_text = QPlainTextEdit()
        self.final_text.setReadOnly(True)
        layout.addWidget(self.final_text)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "7. 최종 결과")
        
        # 저장된 데이터가 있으면 초기화
        current_data = self.get_current_debug_data()
        if current_data.get('final_filtered_keywords'):
            final_data = {
                'final_filtered_keywords': current_data['final_filtered_keywords'],
                'category_matches': current_data.get('category_matches', {})
            }
            self.update_final_tab(final_data)
    
    def update_step(self, step_name: str, data):
        """단계별 실시간 업데이트"""
        print(f"DEBUG: DebugDialog.update_step 호출됨 - 단계: {step_name}")
        try:
            if step_name == "original_titles":
                self.update_titles_tab()
            elif step_name == "ai_analysis":
                self.update_ai_tab()
            elif step_name == "combinations":
                self.update_combinations_tab(data)
            elif step_name == "search_volumes":
                print(f"DEBUG: 검색량 조회 탭 업데이트 - 데이터 개수: {len(data) if isinstance(data, dict) else 'N/A'}")
                self.update_search_volumes_tab(data)
            elif step_name == "category_check":
                print(f"DEBUG: 카테고리 조회 탭 업데이트")
                self.update_category_tab(data)
            elif step_name == "volume_filtered":
                self.update_filtering_tab(data)
            elif step_name == "category_filtered":
                self.update_final_tab(data)
            elif step_name == "final_result":
                # 최종 결과에서 모든 탭 업데이트
                if 'search_volumes' in data:
                    print(f"DEBUG: final_result에서 검색량 탭 업데이트 - 개수: {len(data['search_volumes'])}")
                    self.update_search_volumes_tab(data['search_volumes'])
                if 'volume_filtered_combinations' in data:
                    filter_data = {
                        'filtered_combinations': data['volume_filtered_combinations'],
                        'removed_count': data.get('volume_removed_count', 0)
                    }
                    self.update_filtering_tab(filter_data)
                self.update_final_tab(data)
        except Exception as e:
            print(f"DEBUG: update_step 오류 - {step_name}: {e}")
            import traceback
            print(f"DEBUG: 상세 오류: {traceback.format_exc()}")
    
    def update_titles_tab(self):
        """상품명 탭 업데이트"""
        # 현재 유효한 데이터 가져오기
        parent_data = self.get_current_debug_data()
        titles = parent_data.get('original_titles', [])
        
        if titles:
            # 통계 정보 표시
            text = f"수집된 상품명 ({len(titles)}개):\n"
            
            # 글자수 통계가 있다면 표시
            if 'title_stats' in parent_data and parent_data['title_stats']:
                stats = parent_data['title_stats']
                text += f"📊 글자수 통계: 평균 {stats['avg_length']:.1f}자 (최소 {stats['min_length']}자, 최대 {stats['max_length']}자)\n"
            
            text += "\n"
            text += "\n".join([f"{i+1:3d}. {title} ({len(title)}자)" for i, title in enumerate(titles)])
            self.titles_text.setPlainText(text)
    
    def update_ai_tab(self):
        """AI 분석 탭 업데이트"""
        # 현재 유효한 데이터 가져오기
        parent_data = self.get_current_debug_data()
        
        print(f"DEBUG: AI 탭 업데이트 - ai_tokens: {len(parent_data.get('ai_tokens', []))}개")
        print(f"DEBUG: AI 탭 업데이트 - ai_prompt 길이: {len(parent_data.get('ai_prompt', ''))}")
        print(f"DEBUG: AI 탭 업데이트 - ai_response 길이: {len(parent_data.get('ai_response', ''))}")
        
        # 새로운 키 이름 'ai_keywords' 사용
        if parent_data.get('ai_keywords'):
            tokens_text = f"추출된 키워드 ({len(parent_data['ai_keywords'])}개):\n\n" + ", ".join(parent_data['ai_keywords'])
            self.ai_tokens_text.setPlainText(tokens_text)
            print(f"DEBUG: AI 토큰 텍스트 업데이트됨: {tokens_text[:100]}...")
        elif parent_data.get('ai_tokens'):  # 하위 호환성
            tokens_text = f"추출된 키워드 ({len(parent_data['ai_tokens'])}개):\n\n" + ", ".join(parent_data['ai_tokens'])
            self.ai_tokens_text.setPlainText(tokens_text)
            print(f"DEBUG: AI 토큰 텍스트 업데이트됨: {tokens_text[:100]}...")
        else:
            self.ai_tokens_text.setPlainText("AI 키워드 분석을 기다리는 중...")
        
        if parent_data.get('ai_prompt'):
            self.ai_prompt_text.setPlainText(parent_data['ai_prompt'])
            print(f"DEBUG: AI 프롬프트 업데이트됨: {len(parent_data['ai_prompt'])}자")
        else:
            self.ai_prompt_text.setPlainText("AI 프롬프트를 기다리는 중...")
        
        if parent_data.get('ai_response'):
            self.ai_response_text.setPlainText(parent_data['ai_response'])
            print(f"DEBUG: AI 응답 업데이트됨: {len(parent_data['ai_response'])}자")
        else:
            self.ai_response_text.setPlainText("AI 응답을 기다리는 중...")
    
    def update_combinations_tab(self, data=None):
        """키워드 조합 탭 업데이트"""
        # 현재 유효한 데이터 가져오기
        parent_data = self.get_current_debug_data()
        
        # 실시간 호출시 data 매개변수 사용, 초기화시에는 저장된 데이터 사용
        if data:
            combinations = data['combinations']
            single_count = data['single_count']
            two_word_count = data['two_word_count'] 
            three_word_count = data['three_word_count']
        else:
            combinations = parent_data.get('keyword_combinations', [])
            stats = parent_data.get('combinations_stats', {})
            single_count = stats.get('single_count', 0)
            two_word_count = stats.get('two_word_count', 0)
            three_word_count = stats.get('three_word_count', 0)
        
        if not combinations:
            self.combinations_stats.setText("조합 통계: 키워드 조합을 기다리는 중...")
            self.combinations_text.setPlainText("키워드 조합 생성을 기다리는 중...")
            return
        
        stats_text = f"조합 통계: 총 {len(combinations)}개 (단일: {single_count}, 2단어: {two_word_count}, 3단어: {three_word_count})"
        self.combinations_stats.setText(stats_text)
        
        # 조합들을 카테고리별로 분류해서 표시
        singles = [c for c in combinations if " " not in c]
        two_words = [c for c in combinations if c.count(" ") == 1] 
        three_words = [c for c in combinations if c.count(" ") == 2]
        
        text = f"=== 단일 키워드 ({len(singles)}개) ===\n"
        text += ", ".join(singles)
        text += f"\n\n=== 2단어 조합 ({len(two_words)}개) ===\n"
        text += "\n".join(two_words[:50])  # 상위 50개만
        if len(two_words) > 50:
            text += f"\n... 외 {len(two_words) - 50}개"
        text += f"\n\n=== 3단어 조합 ({len(three_words)}개) ===\n"
        text += "\n".join(three_words[:30])  # 상위 30개만
        if len(three_words) > 30:
            text += f"\n... 외 {len(three_words) - 30}개"
        
        self.combinations_text.setPlainText(text)
    
    def update_search_volumes_tab(self, search_volumes):
        """검색량 조회 탭 업데이트"""
        print(f"DEBUG: update_search_volumes_tab 호출됨")
        print(f"DEBUG: search_volumes 타입: {type(search_volumes)}")
        print(f"DEBUG: search_volumes 개수: {len(search_volumes) if isinstance(search_volumes, dict) else 'N/A'}")
        
        # 입력 파라미터가 없으면 저장된 데이터에서 가져오기
        if not search_volumes:
            current_data = self.get_current_debug_data()
            search_volumes = current_data.get('search_volumes', {})
            print(f"DEBUG: 저장된 데이터에서 search_volumes 로드 - 개수: {len(search_volumes)}")
        
        if search_volumes and isinstance(search_volumes, dict):
            # 검색량 높은 순으로 정렬
            sorted_volumes = sorted(search_volumes.items(), key=lambda x: x[1], reverse=True)
            
            text = f"검색량 조회 결과 ({len(sorted_volumes)}개):\n\n"
            for keyword, volume in sorted_volumes[:100]:  # 상위 100개만
                text += f"{keyword} → {volume:,}회\n"
            
            if len(sorted_volumes) > 100:
                text += f"\n... 외 {len(sorted_volumes) - 100}개 키워드"
            
            print(f"DEBUG: 검색량 탭에 표시할 텍스트 길이: {len(text)}")
            print(f"DEBUG: 검색량 탭 텍스트 샘플: {text[:200]}...")
            
            self.search_volumes_text.setPlainText(text)
            
            # 강제로 UI 업데이트
            self.search_volumes_text.update()
            print(f"DEBUG: 검색량 탭 업데이트 완료")
        else:
            print(f"DEBUG: 검색량 데이터가 없거나 잘못된 형식")
            self.search_volumes_text.setPlainText("검색량 조회를 기다리는 중...")
    
    def update_category_tab(self, data):
        """카테고리 조회 탭 업데이트"""
        print(f"DEBUG: update_category_tab 호출됨")
        print(f"DEBUG: data 타입: {type(data)}")
        
        # 입력 파라미터가 없으면 저장된 데이터에서 가져오기
        if not data:
            # keyword_categories는 부모 객체에 저장됨
            if hasattr(self.parent(), 'keyword_categories'):
                data = self.parent().keyword_categories
                print(f"DEBUG: 부모에서 keyword_categories 로드 - 개수: {len(data) if data else 0}")
        
        if isinstance(data, dict) and data:
            text = f"키워드별 카테고리 조회 결과 ({len(data)}개):\n\n"
            
            for keyword, category in data.items():
                text += f"{keyword} → {category}\n"
            
            print(f"DEBUG: 카테고리 탭에 표시할 텍스트 길이: {len(text)}")
            self.category_text.setPlainText(text)
            
            # 강제로 UI 업데이트
            self.category_text.update()
            print(f"DEBUG: 카테고리 탭 업데이트 완료")
        else:
            print(f"DEBUG: 카테고리 데이터가 없거나 잘못된 형식")
            self.category_text.setPlainText("카테고리 조회를 기다리는 중...")
    
    def update_filtering_tab(self, data):
        """필터링 탭 업데이트"""
        filtered = data['filtered_combinations']
        removed = data['removed_count']
        
        text = f"검색량 100 이상 키워드들 ({len(filtered)}개, 제거: {removed}개):\n\n"
        
        # 검색량 높은 순으로 정렬
        sorted_filtered = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        
        for keyword, volume in sorted_filtered:
            text += f"{keyword} → {volume:,}회\n"
        
        self.filtering_text.setPlainText(text)
    
    def update_final_tab(self, data):
        """최종 결과 탭 업데이트"""
        print(f"DEBUG: update_final_tab 호출됨")
        print(f"DEBUG: data 키들: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        # 데이터 키 확인 및 처리
        final = data.get('final_combinations', data.get('final_filtered_keywords', {}))
        category_matches = data.get('category_matches', {})
        
        if not final:
            print(f"DEBUG: final 데이터가 없음")
            self.final_text.setPlainText("최종 결과를 기다리는 중...")
            return
        
        text = f"최종 선별된 키워드들 ({len(final)}개):\n\n"
        
        # 검색량 높은 순으로 정렬
        sorted_final = sorted(final.items(), key=lambda x: x[1], reverse=True)
        
        for keyword, volume in sorted_final:
            match_status = "✅" if category_matches.get(keyword, True) else "❌"
            text += f"{match_status} {keyword} → {volume:,}회\n"
        
        print(f"DEBUG: 최종 결과 탭 업데이트 완료 - 키워드 수: {len(final)}")
        self.final_text.setPlainText(text)
    
    
    def update_final_result_tab(self, data):
        """최종 검색량 필터링 결과 탭 업데이트"""
        try:
            text = "🎯 최종 검색량 필터링 결과:\n\n"
            
            # 개별 키워드 검색량 조회 결과
            individual_keywords = data.get('individual_keywords', [])
            individual_volumes = data.get('individual_volumes', {})
            
            if individual_keywords:
                text += f"📊 개별 키워드 검색량 조회 ({len(individual_keywords)}개):\n"
                for keyword in individual_keywords:
                    volume = individual_volumes.get(keyword, 0)
                    text += f"  {keyword} → {volume:,}회\n"
                text += "\n"
            
            # 전체 검색량 통합 결과
            all_final_volumes = data.get('all_final_volumes', {})
            text += f"🔗 통합된 전체 검색량 ({len(all_final_volumes)}개):\n"
            sorted_all = sorted(all_final_volumes.items(), key=lambda x: x[1], reverse=True)
            for keyword, volume in sorted_all[:20]:  # 상위 20개만
                text += f"  {keyword} → {volume:,}회\n"
            if len(sorted_all) > 20:
                text += f"  ... 외 {len(sorted_all) - 20}개\n"
            text += "\n"
            
            # 최종 필터링 결과 (100 이상)
            final_volume_filtered = data.get('final_volume_filtered', {})
            removed_final = data.get('removed_final', 0)
            
            text += f"✂️ 검색량 100 미만 제거 후 최종 결과 ({len(final_volume_filtered)}개, 제거: {removed_final}개):\n"
            sorted_final = sorted(final_volume_filtered.items(), key=lambda x: x[1], reverse=True)
            for keyword, volume in sorted_final:
                text += f"  ✅ {keyword} → {volume:,}회\n"
            
            # 기존 final_tab을 최종 결과로 업데이트
            self.final_text.setPlainText(text)
            
        except Exception as e:
            print(f"DEBUG: update_final_result_tab 오류: {e}")
            self.final_text.setPlainText(f"최종 결과 업데이트 오류: {str(e)}")