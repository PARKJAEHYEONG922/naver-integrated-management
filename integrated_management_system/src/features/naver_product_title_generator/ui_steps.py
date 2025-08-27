"""
네이버 상품명 생성기 단계별 UI 컴포넌트
4개 단계별 위젯들을 정의
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QCheckBox, QPushButton, QDialog,
    QLineEdit, QRadioButton, QButtonGroup, QTextEdit, QGroupBox,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernCancelButton, ModernCard
from src.toolbox.ui_kit import tokens
from src.toolbox.formatters import format_int


def create_step_header(title: str, subtitle: str = None) -> QVBoxLayout:
    """공용 단계 헤더 생성 메서드
    모든 단계가 동일한 레이아웃과 스타일을 사용
    """
    header_layout = QVBoxLayout()
    header_layout.setSpacing(tokens.GAP_8)
    header_layout.setContentsMargins(0, 0, 0, tokens.GAP_15)
    
    # 메인 제목
    title_label = QLabel(title)
    title_label.setObjectName("step_title")
    header_layout.addWidget(title_label)
    
    # 부제목 (선택적)
    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("step_subtitle")
        header_layout.addWidget(subtitle_label)
    
    return header_layout


def get_common_step_styles() -> str:
    """공용 단계 스타일 반환
    모든 step 위젯에서 동일한 헤더 스타일 사용
    """
    return f"""
        QWidget#step_root {{
            background-color: {ModernStyle.COLORS['bg_primary']};
        }}
        QWidget#step_root QLabel[objectName="step_title"] {{
            font-size: {tokens.get_font_size('title')}px;
            font-weight: 600;
            color: {ModernStyle.COLORS['text_primary']};
            margin-bottom: {tokens.GAP_8}px;
        }}
        QWidget#step_root QLabel[objectName="step_subtitle"] {{
            font-size: {tokens.get_font_size('normal')}px;
            color: {ModernStyle.COLORS['text_secondary']};
            margin-bottom: {tokens.GAP_15}px;
        }}
    """


def create_keyword_card(keyword_data, category_colors=None, use_radio=False, button_group=None, use_checkbox=True):
    """공용 키워드 카드 생성 함수 - 기존 KeywordCard와 동일한 구조 및 스타일 사용
    
    Args:
        keyword_data: 키워드 데이터
        category_colors: 카테고리 색상 매핑 (1단계용)
        use_radio: True면 라디오 버튼, False면 체크박스
        button_group: 라디오 버튼 그룹 (라디오 사용시 필수)
        use_checkbox: 체크박스 사용 여부
    """
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QCheckBox, QRadioButton, QLabel
    from src.toolbox.ui_kit.modern_style import ModernStyle
    from src.toolbox.ui_kit import tokens
    from src.toolbox.formatters import format_int
    
    # QFrame 생성 (기존 KeywordCard와 동일)
    card = QFrame()
    card.setObjectName("keyword_card")
    
    # 기존 KeywordCard와 동일한 레이아웃
    layout = QHBoxLayout()
    margin_h = tokens.GAP_15
    margin_v = tokens.GAP_12
    spacing = tokens.GAP_15
    layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
    layout.setSpacing(spacing)
    
    # 선택 버튼 (체크박스 또는 라디오버튼)
    if use_checkbox:
        selection_button = QCheckBox()
    elif use_radio:
        selection_button = QRadioButton()
        if button_group:
            button_group.addButton(selection_button)
    else:
        selection_button = None
    
    if selection_button:
        layout.addWidget(selection_button)
    
    # 키워드 정보 레이아웃 
    info_layout = QVBoxLayout()
    info_spacing = tokens.GAP_4
    info_layout.setSpacing(info_spacing)
    
    # 상세 정보 (전체상품수는 3단계에서만 표시)
    has_total_products = hasattr(keyword_data, 'total_products') and keyword_data.total_products > 0
    has_category_info = hasattr(keyword_data, 'category') and keyword_data.category and keyword_data.category != ""
    
    if has_total_products and has_category_info:
        # 3단계: 키워드명과 통계를 같은 줄에 배치
        first_line_layout = QHBoxLayout()
        first_line_layout.setSpacing(tokens.GAP_10)
        
        # 키워드명
        keyword_label = QLabel(keyword_data.keyword)
        keyword_label.setObjectName("keyword_name")
        first_line_layout.addWidget(keyword_label)
        
        # 월검색량 + 전체상품수
        stats_text = f"월검색량: {format_int(keyword_data.search_volume)} | 전체상품수: {format_int(keyword_data.total_products)}"
        stats_label = QLabel(stats_text)
        stats_label.setObjectName("keyword_details")
        first_line_layout.addWidget(stats_label)
        
        first_line_layout.addStretch()  # 오른쪽 여백
        info_layout.addLayout(first_line_layout)
        
        # 카테고리 (두 번째 줄)
        category_label = QLabel(keyword_data.category)
        category_label.setObjectName("keyword_category")
        info_layout.addWidget(category_label)
    else:
        # 1-2단계: 기존 방식 (세로 배치)
        keyword_label = QLabel(keyword_data.keyword)
        keyword_label.setObjectName("keyword_name")
        info_layout.addWidget(keyword_label)
        
        if has_category_info:
            details = f"월검색량: {format_int(keyword_data.search_volume)} | 카테고리: {keyword_data.category}"
        else:
            details = f"월검색량: {format_int(keyword_data.search_volume)}"
        details_label = QLabel(details)
        details_label.setObjectName("keyword_details")
        info_layout.addWidget(details_label)
    
    layout.addLayout(info_layout, 1)
    card.setLayout(layout)
    
    # 기존 KeywordCard와 동일한 스타일 적용
    apply_original_keyword_card_style(card, keyword_data, category_colors)
    
    # 호환성을 위한 속성 추가
    card.keyword_data = keyword_data
    card.selection_button = selection_button
    
    # 메서드 추가
    def is_checked():
        return selection_button.isChecked() if selection_button else False
    
    def set_checked(checked):
        if selection_button:
            selection_button.setChecked(checked)
    
    card.is_checked = is_checked
    card.set_checked = set_checked
    
    return card


def apply_original_keyword_card_style(card, keyword_data, category_colors):
    """기존 KeywordCard와 동일한 스타일 적용"""
    from src.toolbox.ui_kit.modern_style import ModernStyle
    from src.toolbox.ui_kit import tokens
    
    # 카테고리별 색상 결정 (기존 KeywordCard의 get_category_color 로직)
    category = keyword_data.category
    
    if not category or category in ["카테고리 없음", "분석 실패"]:
        category_color = category_colors.get("default", "#6b7280") if category_colors else "#6b7280"
    else:
        # 전체 카테고리 경로 사용 (% 부분만 제거)
        clean_category = category.split(" (")[0] if " (" in category else category
        category_color = category_colors.get(clean_category, category_colors.get("default", "#6b7280")) if category_colors else "#6b7280"
    
    # 기존 KeywordCard와 동일한 스타일
    border_radius = tokens.GAP_8
    margin = 2
    name_font_size = tokens.get_font_size('large')
    details_font_size = tokens.get_font_size('normal')
    checkbox_size = 18
    checkbox_border_radius = tokens.GAP_4
    
    card.setStyleSheet(f"""
        QFrame[objectName="keyword_card"] {{
            background-color: {ModernStyle.COLORS['bg_card']};
            border: 2px solid {category_color};
            border-radius: {border_radius}px;
            margin: {margin}px 0;
        }}
        QFrame[objectName="keyword_card"]:hover {{
            background-color: {ModernStyle.COLORS['bg_secondary']};
            border-color: {category_color};
        }}
        QLabel[objectName="keyword_name"] {{
            font-size: {name_font_size}px;
            font-weight: 600;
            color: {ModernStyle.COLORS['text_primary']};
        }}
        QLabel[objectName="keyword_details"] {{
            font-size: {details_font_size}px;
            color: {ModernStyle.COLORS['text_secondary']};
        }}
        QLabel[objectName="keyword_category"] {{
            font-size: {details_font_size}px;
            color: {ModernStyle.COLORS['text_secondary']};
        }}
        QCheckBox::indicator {{
            width: {checkbox_size}px;
            height: {checkbox_size}px;
            border: 2px solid {category_color};
            border-radius: {checkbox_border_radius}px;
            background-color: white;
        }}
        QCheckBox::indicator:checked {{
            background-color: {category_color};
            border-color: {category_color};
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
        }}
        QRadioButton::indicator {{
            width: {checkbox_size}px;
            height: {checkbox_size}px;
            border: 2px solid {category_color};
            border-radius: {checkbox_size//2}px;
            background-color: white;
        }}
        QRadioButton::indicator:checked {{
            background-color: {category_color};
            border-color: {category_color};
        }}
    """)


# KeywordCard 클래스는 create_keyword_card() 공용 함수로 대체되었습니다.


class Step1ResultWidget(QWidget):
    """1단계: 키워드 분석 결과 표시 (오른쪽 패널용)"""
    
    # 시그널
    keywords_selected = Signal(list)  # 선택된 키워드들
    
    def __init__(self):
        super().__init__()
        self.setObjectName("step_root")
        self.keyword_cards = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        margin = tokens.GAP_20
        spacing = tokens.GAP_15
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 헤더
        header_layout = create_step_header(
            "1️⃣ 키워드 분석 결과",
            "판매하려는 상품과 같은 카테고리의 키워드를 선택해주세요. (중복가능)"
        )
        layout.addLayout(header_layout)
        
        # 전체선택 버튼 (왼쪽으로 이동)
        button_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("전체선택")
        self.select_all_button.setObjectName("select_all_btn")
        self.select_all_button.clicked.connect(self.toggle_all_selection)
        self.select_all_button.setMaximumWidth(80)
        button_layout.addWidget(self.select_all_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 스크롤 가능한 키워드 카드 리스트
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(300)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.addStretch()
        
        scroll_area.setWidget(self.cards_container)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def display_results(self, results):
        """분석 결과 표시"""
        self.clear_cards()
        
        # 카테고리별 색상 할당
        category_colors = self.assign_category_colors(results)
        
        self.keyword_cards = []
        for keyword_data in results:
            # 공용 키워드 카드 사용 (체크박스 모드, 카테고리 색상 적용)
            card = create_keyword_card(
                keyword_data=keyword_data,
                category_colors=category_colors,
                use_radio=False,
                use_checkbox=True
            )
            
            # 이벤트 연결
            if hasattr(card, 'selection_button') and card.selection_button:
                card.selection_button.stateChanged.connect(self.on_selection_changed)
            
            self.keyword_cards.append(card)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
    
    def assign_category_colors(self, results):
        """카테고리별 색상 할당 (키워드 개수 기준)"""
        
        # 카테고리별 키워드 개수와 총 검색량 계산 (전체 카테고리 경로 기준)
        category_stats = {}
        for keyword_data in results:
            category = keyword_data.category
            if category and category != "카테고리 없음" and category != "분석 실패":
                # 전체 카테고리 경로 사용 (% 부분만 제거)
                clean_category = category.split(" (")[0] if " (" in category else category
                
                if clean_category not in category_stats:
                    category_stats[clean_category] = {'count': 0, 'total_volume': 0}
                
                category_stats[clean_category]['count'] += 1
                category_stats[clean_category]['total_volume'] += keyword_data.search_volume
        
        # 개수 기준 우선, 동점이면 총 검색량 기준으로 정렬 (많은 순)
        sorted_categories = sorted(
            category_stats.items(), 
            key=lambda x: (-x[1]['count'], -x[1]['total_volume'])
        )
        
        # 색상 할당
        category_colors = {}
        
        if len(sorted_categories) >= 1:
            # 가장 많은 카테고리 → 초록색
            category_colors[sorted_categories[0][0]] = "#10b981"  # 초록색
        
        if len(sorted_categories) >= 2:
            # 두 번째로 많은 카테고리 → 파란색
            category_colors[sorted_categories[1][0]] = "#3b82f6"  # 파란색
        
        # 나머지 모든 카테고리 → 빨간색
        for category, stats in sorted_categories[2:]:
            category_colors[category] = "#ef4444"  # 빨간색
        
        # 기본 색상 (카테고리 없음/분석 실패)
        category_colors["default"] = "#6b7280"  # 회색
        
        return category_colors
            
    def clear_cards(self):
        """기존 카드들 제거"""
        if hasattr(self, 'keyword_cards'):
            for card in self.keyword_cards:
                card.setParent(None)
                card.deleteLater()
        self.keyword_cards = []
        
    def toggle_all_selection(self):
        """전체 선택/해제 토글"""
        if not hasattr(self, 'keyword_cards'):
            return
            
        selected_count = sum(1 for card in self.keyword_cards 
                           if hasattr(card, 'selection_button') and card.selection_button and card.selection_button.isChecked())
        total_count = len(self.keyword_cards)
        
        new_state = selected_count < total_count
        
        for card in self.keyword_cards:
            if hasattr(card, 'selection_button') and card.selection_button:
                card.selection_button.setChecked(new_state)
            
        self.select_all_button.setText("전체해제" if new_state else "전체선택")
        self.on_selection_changed()
    
    def on_selection_changed(self):
        """선택 상태 변경"""
        if hasattr(self, 'keyword_cards'):
            selected_count = sum(1 for card in self.keyword_cards 
                               if hasattr(card, 'selection_button') and card.selection_button and card.selection_button.isChecked())
            total_count = len(self.keyword_cards)
            
            if selected_count == total_count and total_count > 0:
                self.select_all_button.setText("전체해제")
            else:
                self.select_all_button.setText("전체선택")
                
        # 선택된 키워드 시그널 발송
        selected_keywords = self.get_selected_keywords()
        self.keywords_selected.emit(selected_keywords)
    
    def get_selected_keywords(self) -> list:
        """선택된 키워드들 반환"""
        if not hasattr(self, 'keyword_cards'):
            return []
        
        selected = []
        for card in self.keyword_cards:
            if hasattr(card, 'selection_button') and card.selection_button and card.selection_button.isChecked():
                selected.append(card.keyword_data)
        return selected
    
    def get_selected_category(self):
        """선택된 키워드들의 주요 카테고리 반환"""
        selected_keywords = self.get_selected_keywords()
        if not selected_keywords:
            return ""
        
        # 선택된 키워드들의 카테고리 통계 (미분류 제외)
        category_count = {}
        for keyword_data in selected_keywords:
            category = keyword_data.category
            if category and category.strip() and category != "미분류":
                # % 부분 제거 (예: "생활/건강 > 반려동물 (85%)" -> "생활/건강 > 반려동물")
                category_clean = category.split('(')[0].strip()
                category_count[category_clean] = category_count.get(category_clean, 0) + 1
        
        # 가장 많이 선택된 카테고리 반환
        if category_count:
            selected_category = max(category_count.items(), key=lambda x: x[1])[0]
            return selected_category
        
        # 유효한 카테고리가 없으면 빈 문자열 반환 (모든 키워드 표시)
        return ""
        
    def validate_category_consistency(self) -> bool:
        """선택된 키워드들의 카테고리 일치 검증"""
        selected_keywords = self.get_selected_keywords()
        
        if not selected_keywords:
            # 아무것도 선택하지 않은 경우
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, "키워드 선택", 
                "분석할 키워드를 최소 1개 이상 선택해주세요.",
                confirm_text="확인", cancel_text=None, icon="⚠️"
            )
            dialog.exec()
            return False
        
        # 카테고리 추출 (전체 카테고리 경로 비교, % 부분만 제거)
        categories = set()
        for keyword_data in selected_keywords:
            category = keyword_data.category
            if category and category != "카테고리 없음" and category != "분석 실패":
                # "디지털/가전 > 휴대폰 > 스마트폰 (85%)" -> "디지털/가전 > 휴대폰 > 스마트폰" 추출
                clean_category = category.split(" (")[0] if " (" in category else category
                categories.add(clean_category)
        
        # 카테고리 없는 키워드들은 무시하고 진행
        if len(categories) <= 1:
            return True  # 같은 카테고리이거나 카테고리 없음
        
        # 서로 다른 카테고리가 선택된 경우
        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
        
        category_list = list(categories)
        message = (
            f"서로 다른 카테고리의 키워드가 선택되었습니다:\n\n"
        )
        
        for i, cat in enumerate(category_list, 1):
            message += f"• {cat}\n"
        
        message += (
            f"\n같은 카테고리의 키워드들만 선택해주세요.\n"
            f"더 정확한 분석을 위해 동일한 카테고리 내에서\n"
            f"키워드를 선택하는 것을 권장합니다."
        )
        
        dialog = ModernConfirmDialog(
            self, "카테고리 불일치", message,
            confirm_text="확인", cancel_text=None, icon="⚠️"
        )
        dialog.exec()
        return False
        
    def apply_styles(self):
        common_styles = get_common_step_styles()
        step1_specific = f"""
            QPushButton[objectName="select_all_btn"] {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton[objectName="select_all_btn"]:hover {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """
        self.setStyleSheet(common_styles + step1_specific)


class Step2BasicAnalysisWidget(QWidget):
    """2단계: 수집된 상품명 표시 및 AI 분석 시작"""
    
    # 시그널
    prompt_selected = Signal(str, str)  # (prompt_type, prompt_content) - 프롬프트 선택됨
    
    def __init__(self):
        super().__init__()
        self.setObjectName("step_root")
        self.product_names = []
        self.current_prompt_type = "default"  # "default" or "custom"  
        self.current_prompt_content = ""      # 선택된 프롬프트 내용
        self.prompt_selected_by_user = False  # 사용자가 프롬프트를 선택했는지 여부
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        margin = tokens.GAP_20
        spacing = tokens.GAP_15
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 헤더
        header_layout = create_step_header(
            "2️⃣ 상품명 수집 결과",
            "상위 상품명들을 수집하였습니다. AI프롬프트 변경을 원하시면 변경하시고 다음으로 넘어가주세요."
        )
        layout.addLayout(header_layout)
        
        # 통계 정보 카드
        self.stats_card = self.create_stats_card()
        layout.addWidget(self.stats_card)
        
        # 상품명 목록 (스크롤 가능)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_min_height = 250
        scroll_area.setMinimumHeight(scroll_min_height)
        
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        content_spacing = 5
        content_margin = tokens.GAP_10
        self.content_layout.setSpacing(content_spacing)
        self.content_layout.setContentsMargins(content_margin, content_margin, content_margin, content_margin)
        
        # 초기 플레이스홀더
        self.placeholder_label = QLabel("수집된 상품명이 여기에 표시됩니다.")
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 2px dashed {ModernStyle.COLORS['border']};
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 14px;
            }}
        """)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.placeholder_label)
        
        self.content_layout.addStretch()
        scroll_area.setWidget(self.content_container)
        layout.addWidget(scroll_area, 1)
        
        # 액션 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ai_prompt_button = ModernPrimaryButton("📝 AI 프롬프트")
        self.ai_prompt_button.setMinimumHeight(45)
        self.ai_prompt_button.setMinimumWidth(150)
        self.ai_prompt_button.clicked.connect(self.show_prompt_dialog)
        button_layout.addWidget(self.ai_prompt_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def create_stats_card(self):
        """통계 정보 카드"""
        card = QFrame()
        card.setObjectName("stats_card")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(8)
        
        # 첫 번째 줄: 검색 키워드, 수집된 상품명, 중복 제거
        first_row = QHBoxLayout()
        first_row.setSpacing(15)
        
        self.keyword_count_label = QLabel("검색 키워드: 0개")
        self.keyword_count_label.setObjectName("stats_label")
        first_row.addWidget(self.keyword_count_label)
        
        self.total_count_label = QLabel("수집된 상품명: 0개")
        self.total_count_label.setObjectName("stats_label")
        first_row.addWidget(self.total_count_label)
        
        self.duplicate_count_label = QLabel("중복 제거: 0개")
        self.duplicate_count_label.setObjectName("stats_label")
        first_row.addWidget(self.duplicate_count_label)
        
        first_row.addStretch()
        main_layout.addLayout(first_row)
        
        # 두 번째 줄: 길이 통계들
        second_row = QHBoxLayout()
        second_row.setSpacing(15)
        
        self.avg_length_label = QLabel("평균 길이(공백포함): 0자")
        self.avg_length_label.setObjectName("stats_label")
        second_row.addWidget(self.avg_length_label)
        
        self.min_length_label = QLabel("최소 길이(공백포함): 0자")
        self.min_length_label.setObjectName("stats_label")
        second_row.addWidget(self.min_length_label)
        
        self.max_length_label = QLabel("최대 길이(공백포함): 0자")
        self.max_length_label.setObjectName("stats_label")
        second_row.addWidget(self.max_length_label)
        
        second_row.addStretch()
        main_layout.addLayout(second_row)
        
        card.setLayout(main_layout)
        return card
        
    def display_product_names(self, product_names: list):
        """상품명 목록 표시"""
        self.product_names = product_names
        
        # 통계 정보 업데이트
        self.update_stats()
        
        # 기존 콘텐츠 제거
        self.clear_content()
        
        if not product_names:
            self.placeholder_label.setText("수집된 상품명이 없습니다.")
            self.content_layout.addWidget(self.placeholder_label)
            return
        
        # 상품명 카드들 생성 (전체 표시)
        for i, product in enumerate(product_names):
            card = self.create_product_card(product, i + 1)
            self.content_layout.insertWidget(i, card)
            
        self.content_layout.addStretch()
        
        # AI 프롬프트 버튼 활성화
        self.ai_prompt_button.setEnabled(True)
    
    def create_product_card(self, product: dict, display_rank: int) -> QFrame:
        """상품명 카드 생성"""
        card = QFrame()
        card.setObjectName("product_card")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # 순위
        rank_label = QLabel(f"{display_rank}")
        rank_label.setObjectName("rank_label")
        rank_label.setMinimumWidth(30)
        rank_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(rank_label)
        
        # 상품명
        title_label = QLabel(product.get('title', ''))
        title_label.setObjectName("title_label")
        title_label.setWordWrap(True)
        layout.addWidget(title_label, 1)
        
        # 키워드 정보
        keywords = product.get('keywords_found_in', [])
        keyword_text = f"키워드: {', '.join(keywords[:2])}" + ("..." if len(keywords) > 2 else "")
        keyword_label = QLabel(keyword_text)
        keyword_label.setObjectName("keyword_label")
        layout.addWidget(keyword_label)
        
        card.setLayout(layout)
        return card
    
    def update_stats(self):
        """통계 정보 업데이트"""
        if not self.product_names:
            self.keyword_count_label.setText("검색 키워드: 0개")
            self.total_count_label.setText("수집된 상품명: 0개")
            self.duplicate_count_label.setText("중복 제거: 0개")
            self.avg_length_label.setText("평균 길이(공백포함): 0자")
            self.min_length_label.setText("최소 길이(공백포함): 0자")
            self.max_length_label.setText("최대 길이(공백포함): 0자")
            return
        
        total_count = len(self.product_names)
        
        # 검색에 사용된 키워드 개수 계산
        unique_keywords = set()
        for product in self.product_names:
            keywords_found_in = product.get('keywords_found_in', [])
            unique_keywords.update(keywords_found_in)
        keyword_count = len(unique_keywords)
        
        # 중복 제거 개수 계산 (키워드 개수 합계에서 최종 개수 차이)
        total_keyword_results = sum(p.get('keyword_count', 1) for p in self.product_names)
        duplicate_removed = total_keyword_results - total_count if total_keyword_results > total_count else 0
        
        # 상품명 길이 통계 계산
        lengths = [len(p.get('title', '')) for p in self.product_names]
        
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            min_length = min(lengths)
            max_length = max(lengths)
        else:
            avg_length = min_length = max_length = 0
        
        # 첫 번째 줄
        self.keyword_count_label.setText(f"검색 키워드: {keyword_count}개")
        self.total_count_label.setText(f"수집된 상품명: {total_count}개")
        self.duplicate_count_label.setText(f"중복 제거: {duplicate_removed}개")
        
        # 두 번째 줄
        self.avg_length_label.setText(f"평균 길이(공백포함): {avg_length:.1f}자")
        self.min_length_label.setText(f"최소 길이(공백포함): {min_length}자")
        self.max_length_label.setText(f"최대 길이(공백포함): {max_length}자")
        
        # 4단계에서 사용할 수 있도록 통계를 속성으로 저장
        self.product_name_stats = {
            'average_length': avg_length,
            'min_length': min_length,
            'max_length': max_length,
            'keyword_count': keyword_count,
            'total_count': total_count,
            'duplicate_removed': duplicate_removed
        }
    
    def clear_content(self):
        """콘텐츠 영역 정리"""
        try:
            # 기존 위젯들 제거
            for i in reversed(range(self.content_layout.count())):
                item = self.content_layout.takeAt(i)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.deleteLater()
                    else:
                        # 위젯이 없는 경우 (스페이서 등)
                        del item
        except Exception as e:
            # 예외가 발생하면 로그만 남기고 계속 진행
            print(f"clear_content 에러 (무시됨): {e}")
    
    def show_prompt_dialog(self):
        """프롬프트 선택 다이얼로그 표시"""
        from .ai_dialog import PromptSelectionDialog
        
        dialog = PromptSelectionDialog(
            self,
            current_type=self.current_prompt_type,
            current_content=self.current_prompt_content
        )
        
        if dialog.exec() == QDialog.Accepted:
            self.current_prompt_type = dialog.get_selected_type()
            self.current_prompt_content = dialog.get_selected_content()
            self.prompt_selected_by_user = True  # 사용자가 직접 선택함
            
            # 시그널 발생
            self.prompt_selected.emit(self.current_prompt_type, self.current_prompt_content)
    
    def ensure_prompt_selected(self):
        """프롬프트가 선택되지 않았으면 자동으로 기본 프롬프트 선택"""
        if not self.prompt_selected_by_user:
            # 기본 프롬프트 자동 선택
            from .engine_local import DEFAULT_AI_PROMPT
            self.current_prompt_type = "default"
            self.current_prompt_content = DEFAULT_AI_PROMPT
            self.prompt_selected_by_user = True  # 자동 선택됨으로 표시
            
            # 시그널 발생 (3단계에 알림)
            self.prompt_selected.emit(self.current_prompt_type, self.current_prompt_content)
            
            return True
        return True
    
    def apply_styles(self):
        common_styles = get_common_step_styles()
        step2_specific = f"""
            QFrame[objectName="stats_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                margin: 10px 0;
            }}
            QLabel[objectName="stats_label"] {{
                font-size: 13px;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                padding: 5px 10px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-radius: 4px;
                margin-right: 10px;
            }}
            QFrame[objectName="product_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                margin: 2px 0;
            }}
            QFrame[objectName="product_card"]:hover {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_secondary']};
            }}
            QLabel[objectName="rank_label"] {{
                font-size: 14px;
                font-weight: 600;
                color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-radius: 4px;
                padding: 4px;
            }}
            QLabel[objectName="title_label"] {{
                font-size: 13px;
                color: {ModernStyle.COLORS['text_primary']};
                font-weight: 500;
            }}
            QLabel[objectName="keyword_label"] {{
                font-size: 12px;
                color: {ModernStyle.COLORS['text_secondary']};
            }}
        """
        self.setStyleSheet(common_styles + step2_specific)


class Step3AdvancedAnalysisWidget(QWidget):
    """3단계: AI 상품명분석 위젯"""
    
    # 시그널  
    ai_analysis_started = Signal(str, str)  # (prompt_type, prompt_content) AI 분석 시작
    analysis_stopped = Signal()             # 분석 중단
    keywords_selected_for_step4 = Signal(list)  # 선택된 키워드를 4단계로 전달
    
    def __init__(self):
        super().__init__()
        self.setObjectName("step_root")
        self.product_names = []       # 2단계에서 받은 상품명들
        self.selected_prompt_type = "default"    # 2단계에서 선택된 프롬프트 타입
        self.selected_prompt_content = ""        # 2단계에서 선택된 프롬프트 내용
        self.is_analysis_running = False
        
        # AI 분석 데이터 저장
        self.analysis_data = {
            'input_prompt': '',
            'ai_response': '',
            'extracted_keywords': [],
            'analyzed_keywords': [],
            'filtered_keywords': []
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header_layout = create_step_header(
            "3️⃣ AI 분석 결과",
            "선택된 프롬프트로 상품명을 AI 분석하여 키워드를 추출합니다. AI 분석 시작 버튼을 눌러주세요."
        )
        layout.addLayout(header_layout)
        
        # 분석 설정 요약 카드
        self.summary_card = self.create_summary_card()
        layout.addWidget(self.summary_card)
        
        # AI 분석 결과 표시 영역
        self.result_area = self.create_result_area()
        layout.addWidget(self.result_area, 1)  # 확장 가능
        
        
        self.setLayout(layout)
        self.apply_styles()
    
    
    def create_summary_card(self):
        """분석 설정 요약 카드"""
        from src.toolbox.ui_kit.components import ModernCard
        
        card = ModernCard()
        card.setObjectName("summary_card")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 헤더 (제목 + 버튼들)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        title = QLabel("📋 분석 설정 요약")
        title.setObjectName("summary_title")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # AI 분석 버튼들을 헤더에 배치
        self.analyze_button = ModernPrimaryButton("🤖 AI 분석 시작")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setMinimumWidth(130)
        self.analyze_button.clicked.connect(self.start_ai_analysis)
        header_layout.addWidget(self.analyze_button)
        
        self.stop_button = ModernCancelButton("⏹ 정지")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setMinimumWidth(70)
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        header_layout.addWidget(self.stop_button)
        
        layout.addLayout(header_layout)
        
        # 설정 정보
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        self.product_count_label = QLabel("상품명: 0개")
        self.product_count_label.setObjectName("summary_stat")
        info_layout.addWidget(self.product_count_label)
        
        self.prompt_type_label = QLabel("프롬프트: 미설정")
        self.prompt_type_label.setObjectName("summary_stat")
        info_layout.addWidget(self.prompt_type_label)
        
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        card.setLayout(layout)
        return card
    
    def create_result_area(self):
        """분석 결과 표시 영역"""
        from src.toolbox.ui_kit.components import ModernCard
        
        card = ModernCard()
        card.setObjectName("result_card")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 헤더 (제목 + 실시간 분석내용 버튼)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        title = QLabel("📊 분석 결과")
        title.setObjectName("result_title")
        header_layout.addWidget(title)
        
        # 안내 메시지 추가
        guide_label = QLabel("사용가능한 모든 키워드를 선택해주세요")
        guide_label.setObjectName("guide_text")
        guide_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('large')}px;
                font-weight: 700;
                margin-left: 15px;
            }}
        """)
        guide_label.setVisible(False)  # 초기에는 숨김
        self.guide_label = guide_label
        header_layout.addWidget(guide_label)
        
        header_layout.addStretch()
        
        # 실시간 분석내용 버튼을 결과 카드 오른쪽 위에 배치
        from src.toolbox.ui_kit.components import ModernButton
        self.analysis_log_button = ModernButton("📊 실시간 분석 내용", "secondary")
        self.analysis_log_button.setMinimumHeight(35)
        self.analysis_log_button.setMinimumWidth(130)
        self.analysis_log_button.clicked.connect(self.show_analysis_log)
        self.analysis_log_button.setEnabled(False)  # 분석 시작 후 활성화
        header_layout.addWidget(self.analysis_log_button)
        
        layout.addLayout(header_layout)
        
        # 전체선택 버튼 (왼쪽으로 이동)
        select_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("전체선택")
        self.select_all_button.setObjectName("select_all_btn")
        self.select_all_button.clicked.connect(self.toggle_all_selection)
        self.select_all_button.setMaximumWidth(80)
        self.select_all_button.setEnabled(False)  # 분석 완료 후 활성화
        select_layout.addWidget(self.select_all_button)
        
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # 분석 진행 상황 표시
        self.analysis_status_label = QLabel("AI 분석 결과가 여기에 표시됩니다.\n\n상단의 'AI 분석 시작' 버튼을 클릭하여 시작하세요.")
        self.analysis_status_label.setAlignment(Qt.AlignCenter)
        self.analysis_status_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 14px;
                padding: 20px;
                border: 2px dashed {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
            }}
        """)
        layout.addWidget(self.analysis_status_label)
        
        
        # AI 키워드 선택 영역 (KeywordCard 형태, 초기에는 숨김)
        from PySide6.QtWidgets import QScrollArea
        
        self.keyword_selection_scroll = QScrollArea()
        self.keyword_selection_scroll.setWidgetResizable(True)
        self.keyword_selection_scroll.setMaximumHeight(400)  # 최대 높이 제한
        self.keyword_selection_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.keyword_selection_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.keyword_selection_widget = QWidget()
        self.keyword_selection_layout = QVBoxLayout(self.keyword_selection_widget)
        self.keyword_selection_layout.setContentsMargins(5, 5, 5, 5)
        self.keyword_selection_layout.setSpacing(3)
        
        self.keyword_selection_scroll.setWidget(self.keyword_selection_widget)
        self.keyword_selection_scroll.hide()  # 초기에는 숨김
        layout.addWidget(self.keyword_selection_scroll)
        
        # 선택된 키워드 추적용
        self.keyword_checkboxes = []
        
        card.setLayout(layout)
        return card
    
    def display_keyword_checkboxes(self, keyword_results):
        """AI 분석 완료 후 키워드 체크박스 표시 (1단계와 동일한 KeywordCard 사용)"""
        # 기존 카드들 정리
        self.clear_keyword_checkboxes()
        
        # 새로운 키워드 카드들 생성 (공용 함수 사용)
        for keyword_data in keyword_results:
            # AI 키워드는 모두 초록색으로 표시 (카테고리와 상관없이)
            ai_category_colors = {keyword_data.category: "#10b981", "default": "#10b981"}  # 초록색
            
            # 공용 키워드 카드 사용 (체크박스 모드)
            keyword_card = create_keyword_card(
                keyword_data=keyword_data,
                category_colors=ai_category_colors,
                use_radio=False,
                use_checkbox=True
            )
            
            # 초기 상태는 체크 해제
            if hasattr(keyword_card, 'selection_button') and keyword_card.selection_button:
                keyword_card.selection_button.setChecked(False)
                keyword_card.selection_button.stateChanged.connect(self.on_selection_changed)
            
            # 레이아웃에 추가
            self.keyword_selection_layout.addWidget(keyword_card)
            
            # 카드 저장
            self.keyword_checkboxes.append(keyword_card)
        
        # 하단 여백 추가 (키워드들이 위쪽에 붙도록)
        self.keyword_selection_layout.addStretch()
        
        # 스크롤 영역 표시
        self.keyword_selection_scroll.show()
        self.analysis_status_label.hide()
        
        # 안내 메시지 표시
        if hasattr(self, 'guide_label'):
            self.guide_label.setVisible(True)
        
        # 전체선택 버튼 활성화
        self.select_all_button.setEnabled(True)
    
    
    def get_selected_keywords(self):
        """선택된 키워드 리스트 반환"""
        selected = []
        for card in self.keyword_checkboxes:
            if hasattr(card, 'selection_button') and card.selection_button and card.selection_button.isChecked():
                selected.append(card.keyword_data)
        return selected
    
    def toggle_all_selection(self):
        """전체 선택/해제 토글"""
        if not hasattr(self, 'keyword_checkboxes') or not self.keyword_checkboxes:
            return
            
        selected_count = sum(1 for card in self.keyword_checkboxes 
                           if hasattr(card, 'selection_button') and card.selection_button and card.selection_button.isChecked())
        total_count = len(self.keyword_checkboxes)
        
        new_state = selected_count < total_count
        
        for card in self.keyword_checkboxes:
            if hasattr(card, 'selection_button') and card.selection_button:
                card.selection_button.setChecked(new_state)
            
        self.select_all_button.setText("전체해제" if new_state else "전체선택")
        
        # 선택된 키워드를 4단계로 전달
        selected_keywords = self.get_selected_keywords()
        self.keywords_selected_for_step4.emit(selected_keywords)
    
    def on_selection_changed(self):
        """선택 상태 변경 시 버튼 텍스트 업데이트 및 4단계로 키워드 전달"""
        if hasattr(self, 'keyword_checkboxes') and self.keyword_checkboxes:
            selected_count = sum(1 for card in self.keyword_checkboxes 
                               if hasattr(card, 'selection_button') and card.selection_button and card.selection_button.isChecked())
            total_count = len(self.keyword_checkboxes)
            
            if selected_count == total_count and total_count > 0:
                self.select_all_button.setText("전체해제")
            else:
                self.select_all_button.setText("전체선택")
                
            # 선택된 키워드를 4단계로 전달
            selected_keywords = self.get_selected_keywords()
            self.keywords_selected_for_step4.emit(selected_keywords)
    
    def get_selected_category(self):
        """선택된 키워드들의 주요 카테고리 반환"""
        selected_keywords = self.get_selected_keywords()
        if not selected_keywords:
            return ""
        
        # 선택된 키워드들의 카테고리 통계
        category_count = {}
        for keyword_data in selected_keywords:
            category = keyword_data.category or "미분류"
            category_count[category] = category_count.get(category, 0) + 1
        
        # 가장 많이 선택된 카테고리 반환
        if category_count:
            return max(category_count.items(), key=lambda x: x[1])[0]
        
        return ""
    
    def show_analysis_log(self):
        """실시간 분석 내용 다이얼로그 표시"""
        from .ai_dialog import AIAnalysisDialog
        
        dialog = AIAnalysisDialog(
            parent=self,
            analysis_data=self.analysis_data,
            product_names=self.product_names
        )
        dialog.exec()
    
    def set_product_names(self, product_names):
        """2단계에서 수집된 상품명 설정"""
        self.product_names = product_names
        self.product_count_label.setText(f"상품명: {len(product_names)}개")
    
    def set_prompt_info(self, prompt_type, prompt_content):
        """2단계에서 선택된 프롬프트 정보 설정"""
        self.selected_prompt_type = prompt_type
        self.selected_prompt_content = prompt_content
        
        if prompt_type == "custom":
            self.prompt_type_label.setText("프롬프트: 사용자 정의")
        else:
            self.prompt_type_label.setText("프롬프트: 기본 프롬프트")
    
    def start_ai_analysis(self):
        """AI 분석 시작"""
        if not self.product_names:
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, "분석할 상품명 없음", 
                "분석할 상품명이 없습니다.\n2단계에서 먼저 상품명을 수집해주세요.",
                confirm_text="확인", cancel_text=None, icon="⚠️"
            )
            dialog.exec()
            return
            
        if not self.selected_prompt_content:
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, "프롬프트 미설정", 
                "프롬프트가 설정되지 않았습니다.\n2단계에서 먼저 프롬프트를 선택해주세요.",
                confirm_text="확인", cancel_text=None, icon="⚠️"
            )
            dialog.exec()
            return
        
        # 새로운 분석 시작 전에 이전 분석 데이터 초기화
        self.reset_analysis_data()
        
        # 버튼 상태 변경
        self.is_analysis_running = True
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("분석 중...")
        self.stop_button.setEnabled(True)
        self.analysis_log_button.setEnabled(True)  # 분석 로그 버튼 활성화
        
        # 결과 영역을 초기 상태로 되돌리기
        self.analysis_status_label.setText("🤖 AI 분석 중입니다...\n잠시만 기다려주세요.")
        self.analysis_status_label.setAlignment(Qt.AlignCenter)
        self.analysis_status_label.show()
        self.keyword_selection_scroll.hide()
        
        # AI 분석 시작 시그널 발송
        self.ai_analysis_started.emit(self.selected_prompt_type, self.selected_prompt_content)
    
    def stop_analysis(self):
        """분석 중단"""
        self.is_analysis_running = False
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🤖 AI 분석 시작")
        self.stop_button.setEnabled(False)
        
        self.analysis_status_label.setText("⏹️ 분석이 중단되었습니다.")
        self.keyword_selection_scroll.hide()
        
        # 안내 메시지 숨기기
        if hasattr(self, 'guide_label'):
            self.guide_label.setVisible(False)
        
        # 분석 중단 시그널 발송
        self.analysis_stopped.emit()
        
    def on_analysis_completed(self, results):
        """AI 분석 완료 처리"""
        self.is_analysis_running = False
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🤖 AI 분석 시작")
        self.stop_button.setEnabled(False)
        
        # 결과 표시
        if isinstance(results, list) and len(results) > 0:
            self.analysis_status_label.setText(f"✅ AI 분석 완료!\n키워드를 선택하세요.")
            
            # 체크박스 키워드 결과 표시
            self.display_keyword_checkboxes(results)
        else:
            self.analysis_status_label.setText("⚠️ AI 분석 완료되었으나 유효한 키워드가 없습니다.")
        
    def on_analysis_error(self, error_msg):
        """AI 분석 에러 처리"""
        self.is_analysis_running = False
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🤖 AI 분석 시작")
        self.stop_button.setEnabled(False)
        
        self.analysis_status_label.setText(f"❌ 분석 실패:\n{error_msg}")
        self.keyword_selection_scroll.hide()
        
        # 안내 메시지 숨기기
        if hasattr(self, 'guide_label'):
            self.guide_label.setVisible(False)
        
        # 전체선택 버튼 비활성화
        self.select_all_button.setEnabled(False)
        self.select_all_button.setText("전체선택")
        
    def update_analysis_data(self, data_updates):
        """실시간 분석 데이터 업데이트"""
        # analysis_data 딕셔너리 업데이트
        for key, value in data_updates.items():
            self.analysis_data[key] = value
        
        # AI 응답이 있으면 상태만 업데이트 (텍스트는 다이얼로그에서만 표시)
        if 'ai_response' in data_updates:
            ai_response = data_updates['ai_response']
            if ai_response and ai_response.strip():
                self.analysis_status_label.setText("🤖 AI 분석 응답 수신 완료!\n키워드 추출 및 월검색량 조회 중...")
    
    def clear_keyword_checkboxes(self):
        """기존 체크박스 카드들 모두 제거"""
        while self.keyword_selection_layout.count():
            item = self.keyword_selection_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.keyword_checkboxes.clear()
    
    def reset_analysis_data(self):
        """분석 데이터 초기화 (AI 분석 시작 시 호출)"""
        # 분석 데이터 초기화
        self.analysis_data = {
            'input_prompt': '',
            'ai_response': '',
            'extracted_keywords': [],
            'analyzed_keywords': [],
            'filtered_keywords': []
        }
        
        # 키워드 선택 영역만 초기화 (헤더 레이아웃은 유지)
        self.clear_keyword_checkboxes()
        self.keyword_selection_scroll.hide()
        
        # 안내 메시지 숨기기
        if hasattr(self, 'guide_label'):
            self.guide_label.setVisible(False)
        
        # 전체선택 버튼 비활성화
        self.select_all_button.setEnabled(False)
        self.select_all_button.setText("전체선택")
        
    def apply_styles(self):
        common_styles = get_common_step_styles()
        step3_specific = f"""
            QFrame[objectName="summary_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                margin: 10px 0;
            }}
            QLabel[objectName="summary_title"] {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
            QLabel[objectName="summary_stat"] {{
                font-size: 13px;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                padding: 5px 10px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-radius: 4px;
                margin-right: 10px;
            }}
            QLabel[objectName="result_title"] {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
            QFrame[objectName="result_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                margin: 10px 0;
            }}
        """
        self.setStyleSheet(common_styles + step3_specific)


class Step4ResultWidget(QWidget):
    """4단계: SEO 최적화 상품명 생성"""
    
    # 시그널
    export_requested = Signal()
    ai_generation_started = Signal(dict, dict)  # (selected_keyword, product_info) AI 상품명 생성 시작
    
    def __init__(self):
        super().__init__()
        self.setObjectName("step_root")
        self.selected_keywords = []  # 3단계에서 선택된 키워드들
        self.product_name_stats = {}  # 2단계 상품명 통계
        self.generated_results = []  # AI가 생성한 결과들
        self.keyword_checkboxes = []  # 키워드 체크박스들
        self.keyword_cards = []  # 키워드 카드들 추가
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        margin = tokens.GAP_20
        spacing = tokens.GAP_20
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 헤더
        header_layout = create_step_header(
            "4️⃣ SEO 최적화 상품명 생성",
            "추출된 키워드와 필수 정보를 조합하여 최적화된 상품명을 생성합니다"
        )
        layout.addLayout(header_layout)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(tokens.GAP_20)
        
        # 1. 핵심 키워드 선택 영역
        self.core_keyword_card = self.create_core_keyword_selection_card()
        scroll_layout.addWidget(self.core_keyword_card)
        
        # 2. 필수 입력 키워드 영역
        self.required_inputs_card = self.create_required_inputs_card()
        scroll_layout.addWidget(self.required_inputs_card)
        
        # 3. AI 생성 버튼
        self.generate_button_card = self.create_generate_button_card()
        scroll_layout.addWidget(self.generate_button_card)
        
        # 4. 결과 표시 영역
        self.results_card = self.create_results_card()
        scroll_layout.addWidget(self.results_card)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        self.apply_styles()
        
    
    def create_core_keyword_selection_card(self):
        """핵심 키워드 선택 카드"""
        card = ModernCard("⭐ 핵심 키워드 선택")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(tokens.GAP_20, tokens.GAP_15, tokens.GAP_20, tokens.GAP_15)
        layout.setSpacing(tokens.GAP_15)
        
        info_label = QLabel("상품명 생성의 중심이 될 핵심 키워드를 하나 선택해주세요.")
        info_label.setObjectName("info_text")
        layout.addWidget(info_label)
        
        # 스크롤 영역 - 너비와 높이 확장
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 필요시에만 스크롤바 표시
        scroll_area.setMinimumHeight(350)  # 기본 높이 (스크롤 여유 공간)
        scroll_area.setMaximumHeight(450)  # 최대 높이 제한
        
        self.keyword_cards_container = QWidget()
        self.keyword_cards_layout = QVBoxLayout(self.keyword_cards_container)
        self.keyword_cards_layout.setSpacing(tokens.GAP_8)
        self.keyword_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.keyword_cards_layout.setAlignment(Qt.AlignTop)
        
        # 초기 상태 메시지
        self.no_keywords_label = QLabel("먼저 3단계에서 키워드를 선택해주세요.")
        self.no_keywords_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-style: italic;
                text-align: center;
                padding: {tokens.GAP_20}px;
            }}
        """)
        self.keyword_cards_layout.addWidget(self.no_keywords_label)
        
        scroll_area.setWidget(self.keyword_cards_container)
        layout.addWidget(scroll_area)
        
        return card
    
    def create_required_inputs_card(self):
        """필수 입력 키워드 카드"""
        card = ModernCard("📝 필수 정보 입력 (선택사항)")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(tokens.GAP_20, tokens.GAP_15, tokens.GAP_20, tokens.GAP_15)
        layout.setSpacing(tokens.GAP_15)
        
        info_label = QLabel("상품명에 포함될 필수 정보를 입력하세요. 비워두면 해당 정보는 포함되지 않습니다.")
        info_label.setObjectName("info_text")
        layout.addWidget(info_label)
        
        # 입력 필드들
        inputs_layout = QVBoxLayout()
        inputs_layout.setSpacing(tokens.GAP_12)
        
        # 브랜드명
        brand_layout = QVBoxLayout()
        brand_label = QLabel("브랜드명:")
        brand_label.setObjectName("input_label")
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("예: 슈퍼츄, 오리젠 등")
        brand_layout.addWidget(brand_label)
        brand_layout.addWidget(self.brand_input)
        inputs_layout.addLayout(brand_layout)
        
        # 재료(형태)
        material_layout = QVBoxLayout()
        material_label = QLabel("재료(형태):")
        material_label.setObjectName("input_label")
        self.material_input = QLineEdit()
        self.material_input.setPlaceholderText("예: 비프, 연어, 닭고기 등")
        material_layout.addWidget(material_label)
        material_layout.addWidget(self.material_input)
        inputs_layout.addLayout(material_layout)
        
        # 수량(무게)
        quantity_layout = QVBoxLayout()
        quantity_label = QLabel("수량(무게):")
        quantity_label.setObjectName("input_label")
        self.quantity_input = QLineEdit()
        self.quantity_input.setPlaceholderText("예: 1.3kg, 20개, 500g 등")
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        inputs_layout.addLayout(quantity_layout)
        
        layout.addLayout(inputs_layout)
        return card
    
    def create_generate_button_card(self):
        """AI 생성 버튼 카드"""
        card = ModernCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(tokens.GAP_20, tokens.GAP_15, tokens.GAP_20, tokens.GAP_15)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.generate_button = ModernPrimaryButton("🚀 AI 상품명 생성하기")
        self.generate_button.setMinimumHeight(50)
        self.generate_button.setMinimumWidth(200)
        self.generate_button.clicked.connect(self.generate_product_names)
        self.generate_button.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.generate_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return card
    
    def create_results_card(self):
        """생성된 결과 표시 카드"""
        card = ModernCard("✨ AI 생성 결과")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(tokens.GAP_20, tokens.GAP_15, tokens.GAP_20, tokens.GAP_15)
        layout.setSpacing(tokens.GAP_15)
        
        self.results_area = QTextEdit()
        self.results_area.setPlaceholderText("AI가 생성한 최적화된 상품명과 설명이 여기에 표시됩니다.")
        self.results_area.setMinimumHeight(300)
        self.results_area.setReadOnly(True)
        layout.addWidget(self.results_area)
        
        # 액션 버튼들
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.copy_button = ModernCancelButton("📋 결과 복사")
        self.copy_button.clicked.connect(self.copy_results)
        self.copy_button.setEnabled(False)
        action_layout.addWidget(self.copy_button)
        
        self.export_button = ModernPrimaryButton("📊 엑셀 저장")
        self.export_button.setMinimumHeight(40)
        self.export_button.setMinimumWidth(120)
        self.export_button.clicked.connect(self.export_requested.emit)
        self.export_button.setEnabled(False)
        action_layout.addWidget(self.export_button)
        
        layout.addLayout(action_layout)
        return card
    
    def set_selected_keywords(self, keywords: list):
        """선택된 키워드 설정 (3단계에서 호출)"""
        self.selected_keywords = keywords
        
        # 핵심 키워드 선택 옵션 업데이트 (선택된 키워드 표시 제거됨)
        self.update_core_keyword_options()
        
        # 생성 버튼 활성화 체크
        self.check_generate_button_state()
    
    def update_core_keyword_options(self):
        """키워드 표시 업데이트 (단일 선택 체크박스) - Step 3과 동일한 세로 배치"""
        # 기존 카드들 제거
        for i in reversed(range(self.keyword_cards_layout.count())):
            item = self.keyword_cards_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.keyword_checkboxes = []
        self.keyword_cards = []  # 카드 목록 초기화
        
        # 동적 높이 조정 제거 - 고정 높이로 스크롤 보장
        
        if self.selected_keywords:
            for keyword in self.selected_keywords:
                # Step 3와 동일한 체크박스 카드 생성 (AI 키워드는 모두 초록색)
                ai_category_colors = {keyword.category: "#10b981", "default": "#10b981"}  # 초록색
                
                keyword_card = create_keyword_card(
                    keyword_data=keyword,
                    category_colors=ai_category_colors,
                    use_radio=False,
                    use_checkbox=True
                )
                
                # 체크박스 상태 변경 시 이벤트 연결 (단일 선택 로직)
                if hasattr(keyword_card, 'selection_button') and keyword_card.selection_button:
                    keyword_card.selection_button.stateChanged.connect(
                        lambda state, checkbox=keyword_card.selection_button: self.on_checkbox_changed(checkbox, state)
                    )
                    self.keyword_checkboxes.append(keyword_card.selection_button)
                
                # Step 3처럼 세로로 배치
                self.keyword_cards_layout.addWidget(keyword_card)
                
                # 카드 목록에 추가
                self.keyword_cards.append(keyword_card)
                
            # 첫 번째 키워드 기본 선택
            if self.keyword_checkboxes:
                self.keyword_checkboxes[0].setChecked(True)
        else:
            # 새로운 라벨 생성 (기존 라벨이 삭제되었을 수 있음)
            no_keywords_label = QLabel("먼저 3단계에서 키워드를 선택해주세요.")
            no_keywords_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernStyle.COLORS['text_secondary']};
                    font-style: italic;
                    text-align: center;
                    padding: {tokens.GAP_20}px;
                }}
            """)
            self.keyword_cards_layout.addWidget(no_keywords_label)
    
    def on_checkbox_changed(self, clicked_checkbox, state):
        """체크박스 변경 시 단일 선택 로직"""
        if state == 2:  # 체크된 상태 (Qt.Checked)
            # 다른 모든 체크박스 해제
            for checkbox in self.keyword_checkboxes:
                if checkbox != clicked_checkbox:
                    checkbox.setChecked(False)
        
        # 생성 버튼 상태 업데이트
        self.check_generate_button_state()
    
    def set_product_name_stats(self, stats: dict):
        """상품명 통계 정보 설정 (2단계에서 호출)"""
        self.product_name_stats = stats
    
    def check_generate_button_state(self):
        """생성 버튼 활성화 상태 체크 - 단일 선택 체크박스"""
        has_selected_keyword = False
        
        # 체크된 키워드가 있는지 확인 (단일 선택이므로 하나만 체크됨)
        if hasattr(self, 'keyword_checkboxes'):
            has_selected_keyword = any(checkbox.isChecked() for checkbox in self.keyword_checkboxes)
        
        if hasattr(self, 'generate_button'):
            self.generate_button.setEnabled(has_selected_keyword)
    
    def generate_product_names(self):
        """AI 상품명 생성"""
        # 선택된 키워드 찾기 (단일 선택) - 인덱스 취약성 해결
        selected_card = next((c for c in self.keyword_cards
                              if hasattr(c, 'selection_button') and c.selection_button and c.selection_button.isChecked()),
                             None)
        if not selected_card:
            return
        
        selected_keyword = selected_card.keyword_data
        
        # 상품정보 수집
        product_info = {
            'brand': self.brand_input.text().strip() or None,
            'material': self.material_input.text().strip() or None,  
            'quantity': self.quantity_input.text().strip() or None
        }
        
        # 생성 시작 UI 업데이트
        self.generate_button.setEnabled(False)
        self.generate_button.setText("🔄 생성 중...")
        
        # 모든 선택된 키워드 데이터 수집 (3단계에서 선택된 모든 키워드들)
        all_keywords_data = []
        if hasattr(self, 'selected_keywords') and self.selected_keywords:
            for kw in self.selected_keywords:
                if hasattr(kw, '__dict__'):
                    all_keywords_data.append(kw.__dict__)
                else:
                    # 만약 딕셔너리인 경우
                    all_keywords_data.append(kw)
        
        # AI 상품명 생성 시그널 발송 (핵심 키워드 + 모든 키워드 정보)
        generation_data = {
            'core_keyword': selected_keyword.__dict__,  # 핵심 키워드 (단일 선택)
            'all_keywords': all_keywords_data,          # 3단계에서 선택된 모든 키워드들
            'product_info': product_info
        }
        self.ai_generation_started.emit(generation_data, {})
    
    def on_generation_completed(self, results):
        """생성 완료 처리"""
        self.generated_results = results
        
        # UI 상태 복원
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🔄 다시 생성하기")
        
        # 결과 표시
        result_text = "\n".join([f"{i+1}. {result}" for i, result in enumerate(results)])
        if hasattr(self, 'results_area'):
            self.results_area.setPlainText(result_text)
            if hasattr(self, 'copy_button'):
                self.copy_button.setEnabled(True)
            if hasattr(self, 'export_button'):
                self.export_button.setEnabled(True)
    
    def display_ai_results(self, results: str):
        """AI 생성 결과 표시"""
        self.results_area.setPlainText(results)
        self.copy_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # 결과 저장
        self.generated_results.append({
            'timestamp': __import__('datetime').datetime.now(),
            'content': results
        })
    
    def copy_results(self):
        """결과를 클립보드에 복사"""
        content = self.results_area.toPlainText()
        if content:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(content)
            # TODO: 성공 메시지 표시
        
    def apply_styles(self):
        common_styles = get_common_step_styles()
        step4_specific = f"""
            QLabel[objectName="info_text"] {{
                font-size: {tokens.get_font_size('normal')}px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: {tokens.GAP_10}px;
            }}
            QLabel[objectName="input_label"] {{
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: {tokens.GAP_4}px;
            }}
            QLineEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.GAP_6}px;
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                font-size: {tokens.get_font_size('normal')}px;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.GAP_8}px;
                padding: {tokens.GAP_12}px;
                font-size: {tokens.get_font_size('normal')}px;
                color: {ModernStyle.COLORS['text_primary']};
                font-family: 'Segoe UI', monospace;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """
        self.setStyleSheet(common_styles + step4_specific)
