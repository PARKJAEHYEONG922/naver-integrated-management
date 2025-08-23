"""
네이버 상품명 생성기 단계별 UI 컴포넌트
4개 단계별 위젯들을 정의
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QCheckBox, QPushButton, QDialog
)
from PySide6.QtCore import Qt, Signal

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernCancelButton, ModernCard
from src.toolbox.formatters import format_int



class KeywordCard(QFrame):
    """키워드 정보를 표시하는 카드 위젯"""
    
    selection_changed = Signal(bool)  # 체크 상태 변경
    
    def __init__(self, keyword_data, category_colors=None):
        super().__init__()
        self.keyword_data = keyword_data
        self.category_colors = category_colors or {}
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("keyword_card")
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(15)
        
        # 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self._on_check_changed)
        layout.addWidget(self.checkbox)
        
        # 키워드 정보
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 키워드명 (크게)
        keyword_label = QLabel(self.keyword_data.keyword)
        keyword_label.setObjectName("keyword_name")
        info_layout.addWidget(keyword_label)
        
        # 상세 정보 (작게)
        details = f"월검색량: {format_int(self.keyword_data.search_volume)} | 카테고리: {self.keyword_data.category}"
        details_label = QLabel(details)
        details_label.setObjectName("keyword_details")
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout, 1)
        
        self.setLayout(layout)
        self.apply_styles()
        
    def _on_check_changed(self):
        self.selection_changed.emit(self.checkbox.isChecked())
        
    def is_checked(self) -> bool:
        return self.checkbox.isChecked()
        
    def set_checked(self, checked: bool):
        self.checkbox.setChecked(checked)
        
    def apply_styles(self):
        # 카테고리별 색상 결정
        category_color = self.get_category_color()
        
        self.setStyleSheet(f"""
            QFrame[objectName="keyword_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 2px solid {category_color};
                border-radius: 8px;
                margin: 2px 0;
            }}
            QFrame[objectName="keyword_card"]:hover {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-color: {category_color};
            }}
            QLabel[objectName="keyword_name"] {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QLabel[objectName="keyword_details"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {category_color};
                border-radius: 4px;
                background-color: white;
            }}
            QCheckBox::indicator:checked {{
                background-color: {category_color};
                border-color: {category_color};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
        """)
    
    def get_category_color(self):
        """카테고리별 색상 반환"""
        category = self.keyword_data.category
        
        if not category or category in ["카테고리 없음", "분석 실패"]:
            return self.category_colors.get("default", "#6b7280")
        
        # 전체 카테고리 경로 사용 (% 부분만 제거)
        clean_category = category.split(" (")[0] if " (" in category else category
        
        return self.category_colors.get(clean_category, self.category_colors.get("default", "#6b7280"))


class Step1ResultWidget(QWidget):
    """1단계: 키워드 분석 결과 표시 (오른쪽 패널용)"""
    
    # 시그널
    keywords_selected = Signal(list)  # 선택된 키워드들
    
    def __init__(self):
        super().__init__()
        self.keyword_cards = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header_label = QLabel("1️⃣ 키워드 분석 결과")
        header_label.setObjectName("step_title")
        layout.addWidget(header_label)
        
        # 안내 텍스트 + 전체선택 버튼
        header_layout = QHBoxLayout()
        guide_text = QLabel("판매하려는 상품과 같은 카테고리의 키워드를 선택해주세요")
        guide_text.setObjectName("guide_text")
        header_layout.addWidget(guide_text)
        header_layout.addStretch()
        
        self.select_all_button = QPushButton("전체선택")
        self.select_all_button.setObjectName("select_all_btn")
        self.select_all_button.clicked.connect(self.toggle_all_selection)
        self.select_all_button.setMaximumWidth(80)
        header_layout.addWidget(self.select_all_button)
        
        layout.addLayout(header_layout)
        
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
            card = KeywordCard(keyword_data, category_colors)
            card.selection_changed.connect(self.on_selection_changed)
            
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
            
        selected_count = sum(1 for card in self.keyword_cards if card.is_checked())
        total_count = len(self.keyword_cards)
        
        new_state = selected_count < total_count
        
        for card in self.keyword_cards:
            card.set_checked(new_state)
            
        self.select_all_button.setText("전체해제" if new_state else "전체선택")
        self.on_selection_changed()
    
    def on_selection_changed(self):
        """선택 상태 변경"""
        if hasattr(self, 'keyword_cards'):
            selected_count = sum(1 for card in self.keyword_cards if card.is_checked())
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
            if card.is_checked():
                selected.append(card.keyword_data)
        return selected
        
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
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="step_title"] {{
                font-size: 20px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
            QLabel[objectName="guide_text"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 10px;
            }}
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
        """)


class Step2BasicAnalysisWidget(QWidget):
    """2단계: 수집된 상품명 표시 및 AI 분석 시작"""
    
    # 시그널
    prompt_selected = Signal(str, str)  # (prompt_type, prompt_content) - 프롬프트 선택됨
    
    def __init__(self):
        super().__init__()
        self.product_names = []
        self.current_prompt_type = "default"  # "default" or "custom"  
        self.current_prompt_content = ""      # 선택된 프롬프트 내용
        self.prompt_selected_by_user = False  # 사용자가 프롬프트를 선택했는지 여부
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("2️⃣ 상품명 수집 결과")
        title.setObjectName("step_title")
        header_layout.addWidget(title)
        
        subtitle = QLabel("상위 상품명들을 수집했습니다. AI 분석을 시작하세요.")
        subtitle.setObjectName("step_subtitle")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # 통계 정보 카드
        self.stats_card = self.create_stats_card()
        layout.addWidget(self.stats_card)
        
        # 상품명 목록 (스크롤 가능)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(250)
        
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setSpacing(5)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        
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
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="step_title"] {{
                font-size: 22px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 5px;
            }}
            QLabel[objectName="step_subtitle"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 15px;
            }}
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
        """)


class Step3AdvancedAnalysisWidget(QWidget):
    """3단계: AI 상품명분석 위젯"""
    
    # 시그널  
    ai_analysis_started = Signal(str, str)  # (prompt_type, prompt_content) AI 분석 시작
    analysis_stopped = Signal()             # 분석 중단
    
    def __init__(self):
        super().__init__()
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
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("3️⃣ AI 키워드 분석")
        title.setObjectName("step_title")
        header_layout.addWidget(title)
        
        subtitle = QLabel("선택된 프롬프트로 상품명을 AI 분석하여 키워드를 추출합니다.")
        subtitle.setObjectName("step_subtitle")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # 분석 설정 요약 카드
        self.summary_card = self.create_summary_card()
        layout.addWidget(self.summary_card)
        
        # AI 분석 결과 표시 영역
        self.result_area = self.create_result_area()
        layout.addWidget(self.result_area, 1)  # 확장 가능
        
        # 액션 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.analyze_button = ModernPrimaryButton("🤖 AI 분석 시작")
        self.analyze_button.setMinimumHeight(45)
        self.analyze_button.setMinimumWidth(150)
        self.analyze_button.clicked.connect(self.start_ai_analysis)
        button_layout.addWidget(self.analyze_button)
        
        self.stop_button = ModernCancelButton("⏹ 정지")
        self.stop_button.setMinimumHeight(45)
        self.stop_button.setMinimumWidth(80)
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # 실시간 분석 내용 보기 버튼
        from src.toolbox.ui_kit.components import ModernButton
        self.analysis_log_button = ModernButton("📊 실시간 분석 내용", "secondary")
        self.analysis_log_button.setMinimumHeight(45)
        self.analysis_log_button.setMinimumWidth(150)
        self.analysis_log_button.clicked.connect(self.show_analysis_log)
        self.analysis_log_button.setEnabled(False)  # 분석 시작 후 활성화
        button_layout.addWidget(self.analysis_log_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QCheckBox[objectName="keyword_checkbox"] {{
                font-size: 14px;
                spacing: 5px;
            }}
            QCheckBox[objectName="keyword_checkbox"]::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_input']};
            }}
            QCheckBox[objectName="keyword_checkbox"]::indicator:checked {{
                background-color: {ModernStyle.COLORS['primary']};
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QLabel[objectName="keyword_name"] {{
                font-size: 14px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                padding-left: 5px;
            }}
            QLabel[objectName="keyword_detail"] {{
                font-size: 12px;
                color: {ModernStyle.COLORS['text_secondary']};
                padding-left: 5px;
                margin-bottom: 10px;
            }}
        """)
        
    def create_summary_card(self):
        """분석 설정 요약 카드"""
        card = QFrame()
        card.setObjectName("summary_card")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # 제목
        title = QLabel("📋 분석 설정 요약")
        title.setObjectName("summary_title")
        layout.addWidget(title)
        
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
        card = ModernCard("📊 분석 결과")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
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
        
        # AI 응답 표시 영역 (초기에는 숨김)
        from PySide6.QtWidgets import QTextEdit
        self.ai_response_display = QTextEdit()
        self.ai_response_display.setReadOnly(True)
        self.ai_response_display.setMaximumHeight(200)
        self.ai_response_display.setMinimumHeight(150)
        self.ai_response_display.setPlaceholderText("AI 응답이 여기에 실시간으로 표시됩니다...")
        self.ai_response_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 1px solid {ModernStyle.COLORS['success']};
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        self.ai_response_display.hide()  # 초기에는 숨김
        layout.addWidget(self.ai_response_display)
        
        # AI 키워드 선택 영역 (체크박스 형태, 초기에는 숨김)
        from PySide6.QtWidgets import QScrollArea, QGridLayout, QCheckBox
        
        self.keyword_selection_scroll = QScrollArea()
        self.keyword_selection_scroll.setWidgetResizable(True)
        self.keyword_selection_scroll.setMinimumHeight(300)
        self.keyword_selection_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.keyword_selection_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.keyword_selection_widget = QWidget()
        self.keyword_selection_layout = QGridLayout(self.keyword_selection_widget)
        self.keyword_selection_layout.setContentsMargins(10, 10, 10, 10)
        self.keyword_selection_layout.setSpacing(8)
        
        self.keyword_selection_scroll.setWidget(self.keyword_selection_widget)
        self.keyword_selection_scroll.hide()  # 초기에는 숨김
        layout.addWidget(self.keyword_selection_scroll)
        
        # 선택된 키워드 추적용
        self.keyword_checkboxes = []
        
        return card
    
    def display_keyword_checkboxes(self, keyword_results):
        """AI 분석 완료 후 키워드 체크박스 표시"""
        # 기존 체크박스들 정리
        self.clear_keyword_checkboxes()
        
        # 새로운 체크박스들 생성
        for i, keyword_data in enumerate(keyword_results):
            checkbox = QCheckBox()
            checkbox.setChecked(True)  # 기본적으로 선택됨
            checkbox.setObjectName("keyword_checkbox")
            
            # 키워드 정보 레이블
            if hasattr(keyword_data, 'keyword'):
                keyword_text = keyword_data.keyword
                volume_text = f"월검색량: {keyword_data.search_volume:,}" if keyword_data.search_volume else "월검색량: 0"
                category_text = f"카테고리: {keyword_data.category}" if keyword_data.category else "카테고리: 미분류"
            else:
                keyword_text = str(keyword_data)
                volume_text = "월검색량: 조회 중"
                category_text = "카테고리: 조회 중"
            
            # 키워드명 레이블
            keyword_label = QLabel(keyword_text)
            keyword_label.setObjectName("keyword_name")
            
            # 상세 정보 레이블
            detail_label = QLabel(f"{volume_text} | {category_text}")
            detail_label.setObjectName("keyword_detail")
            
            # 그리드에 배치 (체크박스 + 키워드명)
            row = i * 2  # 2줄씩 사용 (키워드명 + 상세정보)
            self.keyword_selection_layout.addWidget(checkbox, row, 0)
            self.keyword_selection_layout.addWidget(keyword_label, row, 1)
            self.keyword_selection_layout.addWidget(detail_label, row + 1, 1)  # 키워드 밑에 상세정보
            
            # 체크박스 저장
            self.keyword_checkboxes.append((checkbox, keyword_data))
        
        # 스크롤 영역 표시
        self.keyword_selection_scroll.show()
        self.analysis_status_label.setText(f"✅ AI 분석 완료! ({len(keyword_results)}개)")
    
    def clear_keyword_checkboxes(self):
        """기존 키워드 체크박스들 정리"""
        # 기존 위젯들 제거
        for i in reversed(range(self.keyword_selection_layout.count())):
            child = self.keyword_selection_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.keyword_checkboxes.clear()
    
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
        
        # 버튼 상태 변경
        self.is_analysis_running = True
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("분석 중...")
        self.stop_button.setEnabled(True)
        self.analysis_log_button.setEnabled(True)  # 분석 로그 버튼 활성화
        
        # 결과 영역 업데이트
        self.analysis_status_label.setText("🤖 AI 분석 중입니다...\n잠시만 기다려주세요.")
        self.ai_response_display.clear()
        self.ai_response_display.hide()
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
        self.ai_response_display.hide()
        self.keyword_selection_scroll.hide()
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
        self.ai_response_display.hide()
        self.keyword_selection_scroll.hide()
        
    def update_analysis_data(self, data_updates):
        """실시간 분석 데이터 업데이트"""
        # analysis_data 딕셔너리 업데이트
        for key, value in data_updates.items():
            self.analysis_data[key] = value
        
        # AI 응답이 있으면 실시간으로 표시
        if 'ai_response' in data_updates:
            ai_response = data_updates['ai_response']
            if ai_response and ai_response.strip():
                self.analysis_status_label.setText("🤖 AI 분석 응답 수신 완료!\n키워드 추출 및 월검색량 조회 중...")
                self.ai_response_display.setPlainText(ai_response)
                self.ai_response_display.show()
        
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="step_title"] {{
                font-size: 22px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 5px;
            }}
            QLabel[objectName="step_subtitle"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 15px;
            }}
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
        """)
    
    def update_analysis_data(self, data_updates):
        """실시간 분석 데이터 업데이트"""
        # analysis_data 딕셔너리 업데이트
        for key, value in data_updates.items():
            self.analysis_data[key] = value
        
        # AI 응답이 있으면 실시간으로 표시
        if 'ai_response' in data_updates:
            ai_response = data_updates['ai_response']
            if ai_response and ai_response.strip():
                self.analysis_status_label.setText("🤖 AI 분석 응답 수신 완료!\n키워드 추출 및 월검색량 조회 중...")
                self.ai_response_display.setPlainText(ai_response)
                self.ai_response_display.show()
        


class Step4ResultWidget(QWidget):
    """4단계: 최종 상품명 생성 결과"""
    
    # 시그널
    export_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.generated_titles = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # 헤더
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        title = QLabel("🎉 SEO 최적화 상품명 생성 완료!")
        title.setObjectName("step_title")
        header_layout.addWidget(title)
        
        subtitle = QLabel("점수가 높은 순으로 정렬된 상품명들입니다")
        subtitle.setObjectName("step_subtitle")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # 결과 영역 (임시 플레이스홀더)
        placeholder_label = QLabel("4단계 생성된 상품명 결과가 여기에 표시됩니다.")
        placeholder_label.setStyleSheet(f"""
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
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setMinimumHeight(400)
        layout.addWidget(placeholder_label)
        
        # 요약 통계
        self.summary_card = self.create_summary_card()
        layout.addWidget(self.summary_card)
        
        # 액션 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.copy_button = ModernCancelButton("📋 상품명 복사")
        self.copy_button.clicked.connect(self.copy_titles)
        button_layout.addWidget(self.copy_button)
        
        self.export_button = ModernPrimaryButton("📊 엑셀 저장")
        self.export_button.setMinimumHeight(45)
        self.export_button.setMinimumWidth(120)
        self.export_button.clicked.connect(self.export_requested.emit)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.apply_styles()
        
        
    def create_summary_card(self):
        """요약 통계 카드"""
        card = QFrame()
        card.setObjectName("summary_card")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        title = QLabel("📈 생성 결과 요약")
        title.setObjectName("summary_title")
        layout.addWidget(title)
        
        stats_layout = QHBoxLayout()
        self.total_generated_label = QLabel("생성된 상품명: 0개")
        self.avg_score_label = QLabel("평균 점수: 0점")
        self.avg_length_label = QLabel("평균 길이: 0자")
        
        for label in [self.total_generated_label, self.avg_score_label, self.avg_length_label]:
            label.setObjectName("summary_stat")
            stats_layout.addWidget(label)
            
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        card.setLayout(layout)
        return card
        
    def display_results(self, generated_titles: list):
        """생성된 상품명 결과 표시 (임시 구현)"""
        self.generated_titles = generated_titles
        # TODO: 실제 구현 필요
        
        # 요약 통계 업데이트
        self.update_summary()
        
    def update_summary(self):
        """요약 통계 업데이트"""
        if not self.generated_titles:
            return
            
        total = len(self.generated_titles)
        avg_score = sum(t.get('seo_score', 0) for t in self.generated_titles) / total
        avg_length = sum(len(t.get('title', '')) for t in self.generated_titles) / total
        
        self.total_generated_label.setText(f"생성된 상품명: {total}개")
        self.avg_score_label.setText(f"평균 점수: {avg_score:.1f}점")
        self.avg_length_label.setText(f"평균 길이: {avg_length:.1f}자")
        
    def copy_titles(self):
        """상품명들을 클립보드에 복사"""
        if not self.generated_titles:
            return
            
        titles_text = "\n".join([
            f"{i}. {title.get('title', '')}" 
            for i, title in enumerate(self.generated_titles, 1)
        ])
        
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(titles_text)
        
        # 성공 메시지 표시 (추후 구현)
        
    def apply_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLabel[objectName="step_title"] {{
                font-size: 24px;
                font-weight: 600;
                color: {ModernStyle.COLORS['success']};
                margin-bottom: 5px;
            }}
            QLabel[objectName="step_subtitle"] {{
                font-size: 16px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 20px;
            }}
            QFrame[objectName="summary_card"] {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 2px solid {ModernStyle.COLORS['success']};
                border-radius: 10px;
                margin: 15px 0;
            }}
            QLabel[objectName="summary_title"] {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
            QLabel[objectName="summary_stat"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_primary']};
                background-color: {ModernStyle.COLORS['bg_secondary']};
                padding: 8px 12px;
                border-radius: 6px;
                margin-right: 10px;
            }}
        """)