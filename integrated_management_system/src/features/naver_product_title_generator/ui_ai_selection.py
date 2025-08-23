"""
AI 분석 결과 키워드 선택 UI
체크박스 리스트 형태로 키워드 선택
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton
from .ui_steps import KeywordCard


class Step3AIKeywordSelectionWidget(QWidget):
    """3단계: AI 분석 결과 키워드 선택 위젯 (체크박스 리스트)"""
    
    keywords_selected = Signal(list)  # 선택된 키워드들
    
    def __init__(self):
        super().__init__()
        self.keyword_cards = []
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 제목과 설명
        title_label = QLabel("🤖 AI 키워드 분석 결과")
        title_label.setObjectName("step_title")
        layout.addWidget(title_label)
        
        desc_label = QLabel(
            "AI가 분석한 키워드 중 월검색량 100 이상이고 선택한 카테고리와 매칭되는 키워드들입니다.\n"
            "실제 사용하고 싶은 키워드들을 선택해주세요."
        )
        desc_label.setObjectName("step_desc")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 상단 버튼들
        button_layout = QHBoxLayout()
        
        # 전체 선택/해제 버튼
        self.select_all_button = ModernPrimaryButton("전체선택")
        self.select_all_button.clicked.connect(self.toggle_all_selection)
        button_layout.addWidget(self.select_all_button)
        
        button_layout.addStretch()
        
        # 선택 통계 라벨
        self.selection_stats_label = QLabel("0개 키워드 선택됨")
        self.selection_stats_label.setObjectName("selection_stats")
        button_layout.addWidget(self.selection_stats_label)
        
        layout.addLayout(button_layout)
        
        # 스크롤 가능한 키워드 카드 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        self.scroll_area.setObjectName("keyword_scroll_area")
        
        # 카드 컨테이너
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)  # 나머지 공간 모두 사용
        
        self.setLayout(layout)
        self.apply_styles()
        
    def load_keywords(self, keywords: list):
        """키워드 데이터 로드"""
        self.clear_cards()
        
        if not keywords:
            # 키워드가 없는 경우 메시지 표시
            no_data_label = QLabel("📭 매칭되는 키워드가 없습니다.")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setObjectName("no_data")
            self.cards_layout.addWidget(no_data_label)
            self.on_selection_changed()
            return
        
        # 키워드 카드 생성
        for keyword_data in keywords:
            card = KeywordCard(keyword_data)
            card.selection_changed.connect(self.on_selection_changed)
            self.cards_layout.addWidget(card)
            self.keyword_cards.append(card)
        
        # 스페이서 추가 (하단 여백)
        self.cards_layout.addStretch()
        
        # 초기 선택 상태 업데이트
        self.on_selection_changed()
        
    def clear_cards(self):
        """기존 카드들 제거"""
        if hasattr(self, 'keyword_cards'):
            for card in self.keyword_cards:
                card.setParent(None)
                card.deleteLater()
        self.keyword_cards = []
        
        # 레이아웃에서 모든 위젯 제거
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
                child.widget().deleteLater()
        
    def toggle_all_selection(self):
        """전체 선택/해제 토글"""
        if not hasattr(self, 'keyword_cards') or not self.keyword_cards:
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
                
            # 선택 통계 업데이트
            if total_count > 0:
                self.selection_stats_label.setText(f"{selected_count}개 키워드 선택됨 (총 {total_count}개)")
            else:
                self.selection_stats_label.setText("0개 키워드 선택됨")
        else:
            self.selection_stats_label.setText("0개 키워드 선택됨")
                
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
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QLabel[objectName="step_title"] {{
                font-size: 18px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 8px;
            }}
            QLabel[objectName="step_desc"] {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.4;
                margin-bottom: 12px;
            }}
            QLabel[objectName="selection_stats"] {{
                font-size: 13px;
                color: {ModernStyle.COLORS['text_secondary']};
                font-weight: 500;
            }}
            QLabel[objectName="no_data"] {{
                font-size: 16px;
                color: {ModernStyle.COLORS['text_tertiary']};
                padding: 60px 20px;
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 2px dashed {ModernStyle.COLORS['border']};
                border-radius: 12px;
                margin: 20px 0;
            }}
            QScrollArea[objectName="keyword_scroll_area"] {{
                background-color: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
        """)