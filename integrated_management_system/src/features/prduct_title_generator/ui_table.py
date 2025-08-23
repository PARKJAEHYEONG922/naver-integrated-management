"""
네이버 상품명 생성기 UI - 결과 표시 위젯
진행상황 표시와 생성된 상품명 결과를 관리
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QTextEdit, QProgressBar, QFrame, QSizePolicy,
    QDialog, QTabWidget, QPlainTextEdit, QScrollArea, QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernButton, ModernSuccessButton, ModernProgressBar
from src.desktop.common_log import log_manager


class ProductTitleResultWidget(QWidget):
    """상품명 생성기 결과 표시 위젯"""
    
    # 시그널 정의
    copy_requested = Signal()  # 클립보드 복사 요청
    export_requested = Signal()  # 엑셀 저장 요청
    debug_requested = Signal()  # AI 분석 디버그 창 표시 요청
    generate_requested = Signal(list)  # 상품명 생성 요청 (선택된 토큰 리스트)
    
    def __init__(self):
        super().__init__()
        self.generated_titles_data = []
        self.category_info = {}
        self.token_checkboxes = []
        self.search_volumes = {}
        self.keyword_categories = {}
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # 진행상황 섹션
        self.progress_group = self.create_progress_section()
        layout.addWidget(self.progress_group)
        
        # 키워드 선택 섹션
        self.token_group = self.create_token_selection_section()
        layout.addWidget(self.token_group)
        
        # 결과 섹션
        self.result_group = self.create_result_section()
        layout.addWidget(self.result_group)
        
        self.setLayout(layout)
        self.apply_styles()
        
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
        
        # 오른쪽: AI 분석 확인 버튼 (공용 컴포넌트)
        self.ai_debug_button = ModernButton("🤖 AI 분석 확인", "secondary")
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
        
        # 진행바 (공용 컴포넌트)
        self.progress_bar = ModernProgressBar()
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
        
        # 키워드 체크박스 영역
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
        min_scroll_height = fm.height() * 6 + 60  # 6줄 정도
        self.token_scroll.setMinimumHeight(min_scroll_height)
        
        layout.addWidget(self.token_scroll)
        
        # 생성 버튼 (공용 컴포넌트)
        button_layout = QHBoxLayout()
        self.generate_button = ModernSuccessButton("✨ 상품명 생성")
        self.generate_button.setEnabled(False)
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
        
        # 결과 텍스트
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("생성된 상품명이 여기에 표시됩니다...")
        self.result_text.document().setDocumentMargin(10)  # 문서 마진 추가
        
        # 폰트 기반 최소 높이 - 상품명 생성 칸 줄임
        fm = QFontMetrics(self.font())
        min_text_height = fm.height() * 2 + 20  # 2줄 정도
        self.result_text.setMinimumHeight(min_text_height)
        # 최대 높이도 제한하여 너무 커지지 않도록
        max_text_height = fm.height() * 3 + 30  # 최대 3줄
        self.result_text.setMaximumHeight(max_text_height)
        
        layout.addWidget(self.result_text)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        self.copy_button = ModernButton("📋 클립보드에 복사", "info")
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        self.export_button = ModernSuccessButton("💾 엑셀로 저장")
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
        
    def setup_connections(self):
        """시그널 연결"""
        self.ai_debug_button.clicked.connect(self.debug_requested.emit)
        self.copy_button.clicked.connect(self.on_copy_clicked)
        self.export_button.clicked.connect(self.export_requested.emit)
        self.generate_button.clicked.connect(self.on_generate_clicked)
        
    def on_copy_clicked(self):
        """클립보드 복사"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_text.toPlainText())
        log_manager.add_log("📋 클립보드에 복사되었습니다.", "success")
        
    def update_progress(self, value: int, message: str):
        """진행상황 업데이트"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
    def set_progress_visible(self, visible: bool):
        """진행바 표시/숨기기"""
        self.progress_bar.setVisible(visible)
        if visible:
            self.progress_bar.setValue(0)
            
    def reset_status(self):
        """상태 초기화"""
        self.status_label.setText("분석을 시작하려면 위의 정보를 입력하고 '상품 분석 시작' 버튼을 클릭하세요.")
        self.progress_bar.setVisible(False)
        
    def display_results(self, titles_data: list, category_info: dict = None):
        """결과 표시 (DTO/dict 모두 지원)"""
        self.generated_titles_data = titles_data
        self.category_info = category_info or {}
        
        def get_field(obj, key, fallback_key=None, default=None):
            """dict 또는 DTO 객체에서 안전하게 필드 값 추출"""
            if isinstance(obj, dict):
                return obj.get(key, obj.get(fallback_key, default) if fallback_key else default)
            return getattr(obj, key, getattr(obj, fallback_key, default) if fallback_key else default)
        
        # 결과 텍스트 구성
        result_text = "🏆 SEO 최적화 상품명 (점수순):\n\n"
        
        for i, title_data in enumerate(titles_data, 1):
            title = get_field(title_data, "title", default="")
            # score/seo_score, search_volume/estimated_volume 모두 지원
            score = get_field(title_data, "score", "seo_score", 0.0)
            volume = get_field(title_data, "search_volume", "estimated_volume", 0)
            char_count = get_field(title_data, "char_count", default=len(title) if title else 0)
            
            result_text += f"{i}. {title}\n"
            result_text += f"   📊 SEO점수: {float(score):.1f} | 예상검색량: {int(volume):,}회 | 글자수: {int(char_count)}자\n\n"
        
        # 추가 정보
        if category_info:
            result_text += f"\n📂 분석 카테고리: {category_info.get('main_category', '')}\n"
            result_text += f"🎯 카테고리 일치율: {category_info.get('ratio', 0):.1f}%\n"
        
        self.result_text.setPlainText(result_text)
        
        # 버튼 활성화
        self.copy_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
    def get_results_data(self):
        """결과 데이터 반환 (어댑터 호환 스키마로 정규화)"""
        # DTO/dict 모두 어댑터 호환 형식으로 변환
        normalized_titles = []
        for item in self.generated_titles_data:
            if isinstance(item, dict):
                # dict 형태
                normalized_titles.append({
                    "title": item.get("title", ""),
                    "score": item.get("score", item.get("seo_score", 0.0)),
                    "search_volume": item.get("search_volume", item.get("estimated_volume", 0)),
                    "char_count": item.get("char_count", len(item.get("title", "")))
                })
            else:
                # DTO 형태
                title = getattr(item, "title", "")
                normalized_titles.append({
                    "title": title,
                    "score": getattr(item, "seo_score", 0.0),
                    "search_volume": getattr(item, "estimated_volume", 0),
                    "char_count": getattr(item, "char_count", len(title))
                })
        
        return {
            'titles': normalized_titles,
            'category_info': self.category_info,
            'result_text': self.result_text.toPlainText()
        }
        
    def on_generate_clicked(self):
        """상품명 생성 버튼 클릭 처리"""
        # 선택된 키워드 추출
        selected_tokens = []
        for cb in self.token_checkboxes:
            if cb.isChecked():
                text = cb.text()
                # '/' 앞의 키워드 부분만 추출
                if ' / ' in text:
                    keyword_part = text.split(' / ')[0].strip()
                else:
                    keyword_part = text.strip()
                
                if keyword_part:
                    selected_tokens.append(keyword_part)
        
        if not selected_tokens:
            log_manager.add_log("❌ 키워드를 선택해주세요.", "error")
            return
            
        # 생성 요청 시그널 발생
        self.generate_requested.emit(selected_tokens)
        
    def add_token_checkboxes(self, tokens: list, search_volumes: dict = None, keyword_categories: dict = None):
        """키워드 체크박스 추가"""
        # 기존 체크박스들 제거 (메모리 정리 개선)
        for i in reversed(range(self.token_layout.count())):
            item = self.token_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                self.token_layout.removeItem(item)  # 레이아웃 아이템도 제거
        
        # 데이터 저장
        self.search_volumes = search_volumes or {}
        self.keyword_categories = keyword_categories or {}
        
        # 뷰포트 폭 기반으로 컨럼 수 계산
        viewport_width = self.token_scroll.viewport().width()
        checkbox_width = 250  # 검색량과 카테고리 정보 포함으로 더 넓게
        max_cols = max(1, min(3, viewport_width // checkbox_width))
        
        # 새 체크박스들 추가
        self.token_checkboxes = []
        row, col = 0, 0
        
        for token in tokens:
            # 해당 토큰의 검색량 정보 찾기
            search_volume = ""
            if token in self.search_volumes:
                volume = self.search_volumes[token]
                search_volume = f"월 {volume:,}회"
            
            # 해당 토큰의 카테고리 정보 찾기
            token_category = ""
            if token in self.keyword_categories:
                category_info = self.keyword_categories[token]
                if category_info and category_info != "미분류(0%)":
                    # 카테고리에서 마지막 카테고리명과 퍼센트 추출
                    if '(' in category_info and ')' in category_info:
                        category_path = category_info.split('(')[0].strip()
                        percentage = category_info.split('(')[1].split(')')[0]
                        
                        # 카테고리 경로에서 마지막 카테고리명 추출
                        separators = ['>', '/', '\\', '-', '|']
                        last_category = category_path
                        for separator in separators:
                            if separator in category_path:
                                last_category = category_path.split(separator)[-1].strip()
                                break
                        
                        if not last_category:
                            last_category = category_path
                        
                        token_category = f"{last_category}({percentage})"
                    else:
                        token_category = category_info
            
            # 체크박스 텍스트 구성
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
            QTextEdit {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_input']};
                font-size: 14px;
                padding: 15px;
            }}
        """)


# ============= 디버그 다이얼로그 =============
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
        
        # 닫기 버튼 (공용 컴포넌트)
        close_button = ModernButton("닫기", "secondary")
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
        
        # 저장된 데이터가 있으면 초기화
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
        
        # 저장된 데이터가 있으면 초기화
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
    
    def get_current_debug_data(self):
        """현재 유효한 디버그 데이터 반환 (실시간 또는 저장된 데이터)"""
        # 부모 창의 실시간 데이터 우선 사용
        if hasattr(self.parent(), 'analysis_debug_data'):
            return self.parent().analysis_debug_data
        return self.debug_data
    
    def update_step(self, step_name: str, data):
        """단계별 실시간 업데이트"""
        try:
            if step_name == "original_titles":
                self.update_titles_tab()
            elif step_name == "ai_analysis":
                self.update_ai_tab()
            elif step_name == "combinations":
                self.update_combinations_tab(data)
            elif step_name == "search_volumes":
                self.update_search_volumes_tab(data)
            elif step_name == "category_check":
                self.update_category_tab(data)
            elif step_name == "volume_filtered":
                self.update_filtering_tab(data)
            elif step_name == "category_filtered":
                self.update_final_tab(data)
            elif step_name == "final_result":
                # 최종 결과에서 모든 탭 업데이트
                if 'search_volumes' in data:
                    self.update_search_volumes_tab(data['search_volumes'])
                if 'volume_filtered_combinations' in data:
                    filter_data = {
                        'filtered_combinations': data['volume_filtered_combinations'],
                        'removed_count': data.get('volume_removed_count', 0)
                    }
                    self.update_filtering_tab(filter_data)
                self.update_final_tab(data)
        except Exception as e:
            import traceback
            print(f"DEBUG: update_step 오류 - {step_name}: {e}")
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
        
        # 새로운 키 이름 'ai_keywords' 사용
        if parent_data.get('ai_keywords'):
            tokens_text = f"추출된 키워드 ({len(parent_data['ai_keywords'])}개):\n\n" + ", ".join(parent_data['ai_keywords'])
            self.ai_tokens_text.setPlainText(tokens_text)
        elif parent_data.get('ai_tokens'):  # 하위 호환성
            tokens_text = f"추출된 키워드 ({len(parent_data['ai_tokens'])}개):\n\n" + ", ".join(parent_data['ai_tokens'])
            self.ai_tokens_text.setPlainText(tokens_text)
        else:
            self.ai_tokens_text.setPlainText("AI 키워드 분석을 기다리는 중...")
        
        if parent_data.get('ai_prompt'):
            self.ai_prompt_text.setPlainText(parent_data['ai_prompt'])
        else:
            self.ai_prompt_text.setPlainText("AI 프롬프트를 기다리는 중...")
        
        if parent_data.get('ai_response'):
            self.ai_response_text.setPlainText(parent_data['ai_response'])
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
        # 입력 파라미터가 없으면 저장된 데이터에서 가져오기
        if not search_volumes:
            current_data = self.get_current_debug_data()
            search_volumes = current_data.get('search_volumes', {})
        
        if search_volumes and isinstance(search_volumes, dict):
            # 검색량 높은 순으로 정렬
            sorted_volumes = sorted(search_volumes.items(), key=lambda x: x[1], reverse=True)
            
            text = f"검색량 조회 결과 ({len(sorted_volumes)}개):\n\n"
            for keyword, volume in sorted_volumes[:100]:  # 상위 100개만
                text += f"{keyword} → {volume:,}회\n"
            
            if len(sorted_volumes) > 100:
                text += f"\n... 외 {len(sorted_volumes) - 100}개 키워드"
            
            self.search_volumes_text.setPlainText(text)
            
            # 강제로 UI 업데이트
            self.search_volumes_text.update()
        else:
            self.search_volumes_text.setPlainText("검색량 조회를 기다리는 중...")
    
    def update_category_tab(self, data):
        """카테고리 조회 탭 업데이트"""
        # 입력 파라미터가 없으면 저장된 데이터에서 가져오기
        if not data:
            # keyword_categories는 부모 객체에 저장됨
            if hasattr(self.parent(), 'keyword_categories'):
                data = self.parent().keyword_categories
        
        if isinstance(data, dict) and data:
            text = f"키워드별 카테고리 조회 결과 ({len(data)}개):\n\n"
            
            for keyword, category in data.items():
                text += f"{keyword} → {category}\n"
            
            self.category_text.setPlainText(text)
            
            # 강제로 UI 업데이트
            self.category_text.update()
        else:
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
        # 데이터 키 확인 및 처리
        final = data.get('final_combinations', data.get('final_filtered_keywords', {}))
        category_matches = data.get('category_matches', {})
        
        if not final:
            self.final_text.setPlainText("최종 결과를 기다리는 중...")
            return
        
        text = f"최종 선별된 키워드들 ({len(final)}개):\n\n"
        
        # 검색량 높은 순으로 정렬
        sorted_final = sorted(final.items(), key=lambda x: x[1], reverse=True)
        
        for keyword, volume in sorted_final:
            match_status = "✅" if category_matches.get(keyword, True) else "❌"
            text += f"{match_status} {keyword} → {volume:,}회\n"
        
        self.final_text.setPlainText(text)