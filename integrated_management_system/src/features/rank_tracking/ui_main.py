"""
순위 추적 UI 컴포넌트 모음
메인 위젯, 프로젝트 리스트, 순위 테이블, 다이얼로그들을 모두 포함
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QDialog, QFrame, QTabWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLineEdit, QApplication, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QBrush, QColor, QFont

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.modern_dialog import ModernHelpDialog, ModernInfoDialog
from src.toolbox.ui_kit.sortable_items import SortableTableWidgetItem
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernHelpButton, ModernCancelButton
from src.toolbox.ui_kit import tokens
from src.toolbox.formatters import format_price_krw, format_datetime, format_datetime_full, format_datetime_short
from src.foundation.logging import get_logger
from src.desktop.common_log import log_manager

# 분리된 위젯들 임포트
from .ui_list import ProjectListWidget
from .ui_table import RankingTableWidget
from .service import rank_tracking_service

logger = get_logger("features.rank_tracking.ui")


# === 다이얼로그 클래스들 ===

class NewProjectDialog(QDialog):
    """새 프로젝트 생성 다이얼로그 - 기존 ModernProjectUrlDialog와 동일"""
    
    def __init__(self, parent=None, button_pos=None):
        super().__init__(parent)
        self.result_url = ""
        self.result_product_name = ""
        self.result_ok = False
        self.button_pos = button_pos  # 버튼 위치 (QPoint)
        
        self.setup_ui()
        self.position_dialog()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle("새 프로젝트 생성")
        
        # 메인 레이아웃 - 토큰 기반
        main_layout = QVBoxLayout()
        margin = tokens.GAP_16
        spacing = tokens.GAP_10
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 헤더
        header_label = QLabel("🚀 새 프로젝트 생성")
        font_size = tokens.get_font_size('title')
        margin_bottom = tokens.GAP_6
        header_label.setStyleSheet(f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: {margin_bottom}px;
            }}
        """)
        main_layout.addWidget(header_label)
        
        # 설명
        desc_label = QLabel("네이버 쇼핑 상품 URL을 입력하여 새 프로젝트를 생성하세요.")
        desc_font_size = tokens.get_font_size('header')
        desc_margin = tokens.GAP_4)
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: {desc_font_size}pt;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: {desc_margin}px;
            }}
        """)
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # URL 입력 라벨
        url_label = QLabel("상품 URL:")
        label_font_size = tokens.get_font_size('normal')
        label_margin = tokens.GAP_4)
        url_label.setStyleSheet(f"""
            QLabel {{
                font-size: {label_font_size}pt;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: {label_margin}px;
            }}
        """)
        main_layout.addWidget(url_label)
        
        # URL 입력 필드
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://shopping.naver.com/catalog/...")
        self.url_input.textChanged.connect(self._clear_validation_error)  # 입력시 오류 메시지 제거
        padding_v = tokens.GAP_6)
        padding_h = tokens.GAP_10)
        border_radius = tokens.GAP_6)
        input_font_size = tokens.get_font_size('normal')
        min_height = tokens.GAP_35)
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                padding: {padding_v}px {padding_h}px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {border_radius}px;
                font-size: {input_font_size}pt;
                background-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                min-height: {min_height}px;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {ModernStyle.COLORS['primary']}88;
            }}
        """)
        main_layout.addWidget(self.url_input)
        
        # 상품명 입력 라벨
        product_name_label = QLabel("상품명:")
        label_font_size = tokens.get_font_size('normal')
        label_margin_v = tokens.GAP_4)
        label_margin_top = tokens.GAP_10)
        product_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: {label_font_size}pt;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: {label_margin_v}px;
                margin-top: {label_margin_top}px;
            }}
        """)
        main_layout.addWidget(product_name_label)
        
        # 상품명 입력 필드
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("검색될 수 있는 키워드 또는 상품명을 입력해주세요")
        self.product_name_input.textChanged.connect(self._clear_validation_error)  # 입력시 오류 메시지 제거
        self.product_name_input.setStyleSheet(f"""
            QLineEdit {{
                padding: {padding_v}px {padding_h}px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {border_radius}px;
                font-size: {input_font_size}pt;
                background-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                min-height: {min_height}px;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {ModernStyle.COLORS['primary']}88;
            }}
        """)
        main_layout.addWidget(self.product_name_input)
        
        # 도움말
        help_label = QLabel("💡 팁: 네이버 쇼핑에서 상품 페이지 URL을 복사해서 붙여넣으세요.\n상품명은 키워드 생성을 위해 사용됩니다.")
        help_font_size = tokens.get_font_size('normal')
        help_padding = tokens.GAP_6)
        help_border_radius = tokens.GAP_4)
        help_margin = tokens.GAP_6)
        help_label.setStyleSheet(f"""
            QLabel {{
                font-size: {help_font_size}pt;
                color: {ModernStyle.COLORS['text_muted']};
                padding: {help_padding}px {help_padding + 3}px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-radius: {help_border_radius}px;
                margin: {help_margin}px 0px {help_margin + 7}px 0px;
            }}
        """)
        help_label.setWordWrap(True)
        main_layout.addWidget(help_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 취소 버튼 - 공용 버튼 사용
        self.cancel_button = ModernCancelButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 생성 버튼
        self.create_button = ModernPrimaryButton("프로젝트 생성")
        self.create_button.clicked.connect(self.accept)
        self.create_button.setDefault(True)
        button_layout.addWidget(self.create_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 반응형 크기 설정
        dialog_width = tokens.GAP_500)
        dialog_height = tokens.GAP_480)
        self.adjustSize()
        self.setMinimumWidth(dialog_width)
        self.setMaximumWidth(int(dialog_width * 1.2))
        self.setMinimumHeight(dialog_height)
        
        # 실제 필요한 높이 계산하여 설정
        required_height = main_layout.sizeHint().height() + tokens.GAP_16) * 5
        if required_height > dialog_height:
            self.resize(dialog_width, required_height)
        else:
            self.resize(dialog_width, dialog_height)
    
    def position_dialog(self):
        """버튼 위치 근처에 다이얼로그 표시"""
        if self.button_pos:
            # self.button_pos는 이미 글로벌 좌표
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # 다이얼로그 반응형 크기
            dialog_width = max(self.width(), tokens.GAP_300))
            dialog_height = max(self.height(), tokens.GAP_200))
            
            # 버튼 위쪽에 다이얼로그 배치 - 반응형 간격
            gap = tokens.GAP_16) * 8
            x = self.button_pos.x() - dialog_width // 2
            y = self.button_pos.y() - dialog_height - gap
            
            # 화면 경계 체크 및 조정
            x = max(screen_rect.left() + 10, min(x, screen_rect.right() - dialog_width - 10))
            y = max(screen_rect.top() + 10, y)
            
            self.move(x, y)
        else:
            # 기본 중앙 정렬
            self.center_on_parent()
    
    def center_on_parent(self):
        """부모 윈도우 중앙에 위치"""
        if self.parent():
            parent_geo = self.parent().geometry()
            parent_pos = self.parent().mapToGlobal(parent_geo.topLeft())
            
            center_x = parent_pos.x() + parent_geo.width() // 2 - self.width() // 2
            center_y = parent_pos.y() + parent_geo.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
            center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
    
    def accept(self):
        """생성 버튼 클릭"""
        url = self.url_input.text().strip()
        product_name = self.product_name_input.text().strip()
        
        # URL 비어있음 검사
        if not url:
            self._show_validation_error("URL을 입력해주세요.")
            return
        
        # 상품명 비어있음 검사
        if not product_name:
            self._show_validation_error("상품명을 입력해주세요.")
            return
        
        # URL 형식 검사
        if not self._validate_url_format(url):
            self._show_validation_error("올바른 네이버 쇼핑 URL을 입력해주세요.\n예: https://shopping.naver.com/catalog/...")
            return
        
        self.result_url = url
        self.result_product_name = product_name
        self.result_ok = True
        super().accept()
    
    def _validate_url_format(self, url: str) -> bool:
        """네이버 쇼핑 URL 형식 검증"""
        import re
        
        # 네이버 쇼핑 URL 패턴들
        patterns = [
            r'https?://shopping\.naver\.com/catalog/\d+',  # catalog 패턴
            r'https?://smartstore\.naver\.com/[^/]+/products/\d+',  # 스마트스토어 패턴
            r'https?://brand\.naver\.com/[^/]+/products/\d+',  # 브랜드스토어 패턴
        ]
        
        for pattern in patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def _show_validation_error(self, message: str):
        """검증 오류 메시지 표시"""
        # 기존 오류 메시지가 있으면 제거
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
        
        # 오류 라벨 생성
        self.error_label = QLabel(message)
        error_font_size = tokens.get_font_size('normal')
        error_padding_v = tokens.GAP_6)
        error_padding_h = tokens.GAP_10)
        error_border_radius = tokens.GAP_6)
        error_margin = tokens.GAP_4)
        self.error_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['danger']};
                font-size: {error_font_size}pt;
                padding: {error_padding_v}px {error_padding_h}px;
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: {error_border_radius}px;
                margin: {error_margin}px 0px;
            }}
        """)
        self.error_label.setWordWrap(True)
        
        # URL 입력 필드 아래에 삽입
        layout = self.layout()
        url_input_index = -1
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget == self.url_input:
                url_input_index = i
                break
        
        if url_input_index >= 0:
            layout.insertWidget(url_input_index + 1, self.error_label)
    
    def _clear_validation_error(self):
        """검증 오류 메시지 제거"""
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
    
    def reject(self):
        """취소 버튼 클릭"""
        self.result_url = ""
        self.result_product_name = ""
        self.result_ok = False
        super().reject()
    
    @classmethod
    def getProjectData(cls, parent, button_widget=None):
        """프로젝트 데이터 입력 다이얼로그 표시"""
        button_pos = None
        if button_widget:
            # 버튼의 글로벌 중앙 위치 계산 (이미 글로벌 좌표로 변환)
            button_pos = button_widget.mapToGlobal(button_widget.rect().center())
        
        dialog = cls(parent, button_pos)
        dialog.exec()
        return dialog.result_url, dialog.result_product_name, dialog.result_ok



class ProjectHistoryDialog(QDialog):
    """프로젝트 변경사항 이력 다이얼로그"""
    
    def __init__(self, project_id: int, project_name: str, parent=None, current_time: str = None, previous_time: str = None):
        super().__init__(parent)
        self.project_id = project_id
        self.project_name = project_name
        self.current_time = current_time
        self.previous_time = previous_time
        self.setup_ui()
        self.load_all_history()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle(f"📊 {self.project_name} - 변경 이력")
        self.setFixedSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header_label = QLabel(f"📊 {self.project_name} - 변경 이력")
        header_font = QFont("맑은 고딕")
        header_font.setPointSize(tokens.get_font_size('title'))
        header_font.setWeight(QFont.Bold)
        header_label.setFont(header_font)
        header_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_primary']}; margin-bottom: {tokens.GAP_10)}px;")
        layout.addWidget(header_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.GAP_6)}px;
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: {tokens.GAP_10)}px {tokens.GAP_20)}px;
                margin-right: {tokens.GAP_2)}px;
                border-top-left-radius: {tokens.GAP_8)}px;
                border-top-right-radius: {tokens.GAP_8)}px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {ModernStyle.COLORS['primary']}30;
            }}
        """)
        
        # 3개 탭 생성
        self.create_basic_info_tab()
        self.create_keyword_management_tab()
        self.create_ranking_history_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 닫기 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = ModernPrimaryButton("닫기")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_basic_info_tab(self):
        """기본정보 변경 탭 생성"""
        self.basic_info_table = QTableWidget()
        self.basic_info_table.setColumnCount(4)
        self.basic_info_table.setHorizontalHeaderLabels([
            "변경 일시", "변경 필드", "변경 전", "변경 후"
        ])
        self.setup_table_style(self.basic_info_table)
        
        # 열 너비 설정
        header = self.basic_info_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 변경 일시
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # 변경 필드
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 변경 전
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 변경 후
        
        self.basic_info_table.setColumnWidth(0, tokens.GAP_150))  # 변경 일시
        self.basic_info_table.setColumnWidth(1, tokens.GAP_100))  # 변경 필드
        
        self.tab_widget.addTab(self.basic_info_table, "📝 기본정보 변경")
    
    def create_keyword_management_tab(self):
        """키워드 관리 탭 생성 (2개 영역으로 분할)"""
        from PySide6.QtWidgets import QSplitter
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 좌우 분할 스플리터
        splitter = QSplitter(Qt.Horizontal)
        
        # === 왼쪽 영역: 키워드 관리 이력 ===
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(8)
        
        # 왼쪽 제목
        left_title = QLabel("📋 키워드 관리 이력")
        title_font_size = tokens.get_font_size('large')
        title_padding = tokens.GAP_5)
        title_border_radius = tokens.GAP_4)
        left_title.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}pt;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                padding: {title_padding}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: {title_border_radius}px;
            }}
        """)
        left_layout.addWidget(left_title)
        
        # 통계 레이블
        self.keyword_stats_label = QLabel("총 0건의 키워드이력 (추가 0건, 삭제 0건)")
        stats_font_size = tokens.get_font_size('normal')
        stats_padding = tokens.GAP_2)
        self.keyword_stats_label.setStyleSheet(f"""
            QLabel {{
                font-size: {stats_font_size}pt;
                color: {ModernStyle.COLORS['text_secondary']};
                padding: {stats_padding}px;
            }}
        """)
        left_layout.addWidget(self.keyword_stats_label)
        
        # 키워드 관리 이력 테이블
        self.keyword_history_table = QTableWidget()
        self.keyword_history_table.setColumnCount(3)
        self.keyword_history_table.setHorizontalHeaderLabels([
            "날짜", "키워드", "작업"
        ])
        self.setup_table_style(self.keyword_history_table)
        
        # 왼쪽 테이블 열 너비 설정
        left_header = self.keyword_history_table.horizontalHeader()
        left_header.setSectionResizeMode(0, QHeaderView.Fixed)
        left_header.setSectionResizeMode(1, QHeaderView.Interactive)  # 가로 스크롤 가능하게 변경
        left_header.setSectionResizeMode(2, QHeaderView.Fixed)
        
        self.keyword_history_table.setColumnWidth(0, tokens.GAP_80))  # 날짜
        self.keyword_history_table.setColumnWidth(1, tokens.GAP_120))  # 키워드
        self.keyword_history_table.setColumnWidth(2, tokens.GAP_60))   # 작업
        
        left_layout.addWidget(self.keyword_history_table)
        left_widget.setLayout(left_layout)
        
        # === 오른쪽 영역: 현재 관리 키워드 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(8)
        
        # 오른쪽 제목
        right_title = QLabel("🔍 현재 관리 키워드")
        right_title_font_size = tokens.get_font_size('large')
        right_title_padding = tokens.GAP_5)
        right_title_border_radius = tokens.GAP_4)
        right_title.setStyleSheet(f"""
            QLabel {{
                font-size: {right_title_font_size}pt;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                padding: {right_title_padding}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: {right_title_border_radius}px;
            }}
        """)
        right_layout.addWidget(right_title)
        
        # 키워드 개수 레이블
        self.current_keywords_count_label = QLabel("총 0개의 키워드 관리 중")
        count_font_size = tokens.get_font_size('normal')
        count_padding = tokens.GAP_2)
        self.current_keywords_count_label.setStyleSheet(f"""
            QLabel {{
                font-size: {count_font_size}pt;
                color: {ModernStyle.COLORS['text_secondary']};
                padding: {count_padding}px;
            }}
        """)
        right_layout.addWidget(self.current_keywords_count_label)
        
        # 현재 키워드 테이블
        self.current_keywords_table = QTableWidget()
        self.current_keywords_table.setColumnCount(4)
        self.current_keywords_table.setHorizontalHeaderLabels([
            "날짜", "키워드", "카테고리", "월검색량"
        ])
        self.setup_table_style(self.current_keywords_table)
        
        # 오른쪽 테이블 열 너비 설정
        right_header = self.current_keywords_table.horizontalHeader()
        right_header.setSectionResizeMode(0, QHeaderView.Fixed)
        right_header.setSectionResizeMode(1, QHeaderView.Interactive)  # 키워드 열 가로 스크롤 가능
        right_header.setSectionResizeMode(2, QHeaderView.Interactive)  # 카테고리 열 가로 스크롤 가능
        right_header.setSectionResizeMode(3, QHeaderView.Fixed)
        
        self.current_keywords_table.setColumnWidth(0, tokens.GAP_80))  # 날짜
        self.current_keywords_table.setColumnWidth(1, tokens.GAP_150))  # 키워드 (더 넓게)
        self.current_keywords_table.setColumnWidth(2, tokens.GAP_150))  # 카테고리 (줄임: 200 → 150)
        self.current_keywords_table.setColumnWidth(3, tokens.GAP_80))   # 월검색량
        
        right_layout.addWidget(self.current_keywords_table)
        right_widget.setLayout(right_layout)
        
        # 스플리터에 위젯 추가
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])  # 1:1 비율
        
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        
        self.tab_widget.addTab(main_widget, "🏷️ 키워드 관리")
    
    def create_ranking_history_tab(self):
        """순위 이력 탭 생성 - 스크린샷 참고한 디자인"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 제목과 마지막 순위확인 정보
        title_layout = QHBoxLayout()
        
        title_label = QLabel("📈 순위 변동 현황")
        title_font_size = tokens.get_font_size('large')
        title_padding = tokens.GAP_5)
        title_border_radius = tokens.GAP_4)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}pt;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
                padding: {title_padding}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: {title_border_radius}px;
            }}
        """)
        title_layout.addWidget(title_label)
        
        
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # 순위 이력 테이블
        self.ranking_history_table = QTableWidget()
        self.ranking_history_table.setColumnCount(6)
        self.ranking_history_table.setHorizontalHeaderLabels([
            "키워드", "카테고리", "월검색량", "현재 순위", "이전 순위", "순위변동"
        ])
        
        # 테이블 스타일 설정
        self.ranking_history_table.setAlternatingRowColors(True)
        self.ranking_history_table.setWordWrap(True)  # 줄바꿈 활성화
        self.ranking_history_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.ranking_history_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.ranking_history_table.verticalHeader().setVisible(False)
        # 정렬은 데이터 로드 후에 활성화
        self.ranking_history_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.GAP_6)}px;
                gridline-color: {ModernStyle.COLORS['border']};
                font-size: {tokens.get_font_size('normal')}pt;
            }}
            QTableWidget::item {{
                padding: {tokens.GAP_6)}px;
                border: none;
                text-align: center;
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: {tokens.GAP_10)}px;
                border: none;
                border-right: 1px solid {ModernStyle.COLORS['border']};
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
                font-size: {tokens.get_font_size('normal')}pt;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
        """)
        
        # 열 너비 설정 - 스크린샷 참고
        header = self.ranking_history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # 키워드 - 가로 스크롤 가능
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # 카테고리 - 가로 스크롤 가능
        header.setSectionResizeMode(2, QHeaderView.Fixed)        # 월검색량
        header.setSectionResizeMode(3, QHeaderView.Fixed)        # 현재 순위
        header.setSectionResizeMode(4, QHeaderView.Fixed)        # 이전 순위
        header.setSectionResizeMode(5, QHeaderView.Fixed)        # 순위변동
        
        self.ranking_history_table.setColumnWidth(0, 144)  # 키워드 (120 × 1.2 = 144)
        self.ranking_history_table.setColumnWidth(1, 190)  # 카테고리 (10 줄임: 200 → 190)
        self.ranking_history_table.setColumnWidth(2, 96)   # 월검색량 (80 × 1.2 = 96)
        self.ranking_history_table.setColumnWidth(3, 110)  # 현재 순위 (두 줄 표시용으로 넓게)
        self.ranking_history_table.setColumnWidth(4, 110)  # 이전 순위 (두 줄 표시용으로 넓게)
        self.ranking_history_table.setColumnWidth(5, 100)  # 순위변동
        
        main_layout.addWidget(self.ranking_history_table)
        main_widget.setLayout(main_layout)
        
        self.tab_widget.addTab(main_widget, "📈 순위 이력")
    
    def setup_table_style(self, table: QTableWidget):
        """테이블 공통 스타일 설정"""
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        
        # 헤더 스타일
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(tokens.GAP_150))
        
        # 테이블 스타일
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.GAP_6)}px;
                gridline-color: {ModernStyle.COLORS['border']};
                selection-background-color: {ModernStyle.COLORS['primary']}20;
            }}
            QTableWidget::item {{
                padding: {tokens.GAP_8)}px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']}20;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_card']};
                padding: {tokens.GAP_10)}px;
                border: none;
                border-right: 1px solid {ModernStyle.COLORS['border']};
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
        """)
    
    def load_all_history(self):
        """모든 이력 데이터 로드"""
        try:
            log_manager.add_log(f"📊 {self.project_name} 변경 이력 로드 시작", "info")
            
            # 각 탭별로 데이터 로드
            self.load_basic_info_history()
            self.load_keyword_management_history()
            self.load_ranking_history()
            
            log_manager.add_log("✅ 변경 이력 로드 완료", "success")
            
        except Exception as e:
            log_manager.add_log(f"❌ 변경 이력 로드 실패: {e}", "error")
            logger.error(f"Failed to load project history: {e}")
    
    def load_basic_info_history(self):
        """기본정보 변경 이력 로드"""
        try:
            # 실제 서비스에서 데이터를 가져오려고 시도
            try:
                history_data = rank_tracking_service.get_basic_info_change_history(self.project_id)
            except:
                history_data = []
            
            if not history_data:
                self.show_no_data_message(self.basic_info_table, "기본정보 변경 이력이 없습니다.")
                return
            
            self.basic_info_table.setRowCount(len(history_data))
            
            for row, record in enumerate(history_data):
                # 변경 일시 (기존 통합관리프로그램과 동일한 포맷)
                change_time = format_datetime_full(record.get('change_time'))
                self.basic_info_table.setItem(row, 0, QTableWidgetItem(change_time))
                
                # 변경 필드
                field_name = self.get_field_display_name(record.get('field_name', ''))
                self.basic_info_table.setItem(row, 1, QTableWidgetItem(field_name))
                
                # 변경 전 값 (가격 포맷팅 적용)
                old_value = self.format_field_value(record.get('field_name', ''), record.get('old_value', ''))
                self.basic_info_table.setItem(row, 2, QTableWidgetItem(old_value))
                
                # 변경 후 값 (가격 포맷팅 적용)
                new_value = self.format_field_value(record.get('field_name', ''), record.get('new_value', ''))
                self.basic_info_table.setItem(row, 3, QTableWidgetItem(new_value))
            
        except Exception as e:
            logger.error(f"Failed to load basic info history: {e}")
            self.show_no_data_message(self.basic_info_table, f"기본정보 이력 로드 실패: {e}")
    
    def load_keyword_management_history(self):
        """키워드 관리 이력 로드 (좌우 분할 방식)"""
        try:
            # 1. 키워드 관리 이력 로드 (왼쪽)
            try:
                history_data = rank_tracking_service.get_keyword_management_history(self.project_id)
            except:
                history_data = []
            
            if not history_data:
                self.keyword_history_table.setRowCount(0)
                self.keyword_stats_label.setText("총 0건의 키워드이력 (추가 0건, 삭제 0건)")
            else:
                # 통계 계산
                add_count = len([h for h in history_data if h.get('action') == 'add'])
                delete_count = len([h for h in history_data if h.get('action') == 'delete'])
                total_count = len(history_data)
                
                self.keyword_stats_label.setText(f"총 {total_count}건의 키워드이력 (추가 {add_count}건, 삭제 {delete_count}건)")
                
                # 이력 테이블 데이터 설정
                self.keyword_history_table.setRowCount(len(history_data))
                
                for row, record in enumerate(history_data):
                    # 날짜 (MM-DD HH:MM 형태)
                    action_time = format_datetime_short(record.get('action_time'))
                    self.keyword_history_table.setItem(row, 0, QTableWidgetItem(action_time))
                    
                    # 키워드
                    keyword = record.get('keyword', '')
                    self.keyword_history_table.setItem(row, 1, QTableWidgetItem(keyword))
                    
                    # 작업 (추가/삭제)
                    action = self.get_action_display_name(record.get('action', ''))
                    action_item = QTableWidgetItem(action)
                    # 추가는 초록색, 삭제는 빨간색으로 표시
                    if record.get('action') == 'add':
                        success_brush = QBrush(QColor(ModernStyle.COLORS['success']))
                        action_item.setForeground(success_brush)
                    elif record.get('action') == 'delete':
                        danger_brush = QBrush(QColor(ModernStyle.COLORS['danger']))
                        action_item.setForeground(danger_brush)
                    
                    self.keyword_history_table.setItem(row, 2, action_item)
            
            # 2. 현재 관리 키워드 로드 (오른쪽)
            try:
                current_keywords = rank_tracking_service.get_project_keywords(self.project_id)
            except:
                current_keywords = []
            
            # 프로젝트 정보 조회 (카테고리 비교용)
            try:
                project_info = rank_tracking_service.get_project_by_id(self.project_id)
            except:
                project_info = None
                
            project_category_base = ""
            
            if project_info and hasattr(project_info, 'category') and project_info.category:
                # 프로젝트 카테고리에서 마지막 부분 추출 (메인 UI와 동일한 방식)
                project_category_base = project_info.category.split('>')[-1].strip() if '>' in project_info.category else project_info.category.strip()
            
            if not current_keywords:
                self.current_keywords_table.setRowCount(0)
                self.current_keywords_count_label.setText("총 0개의 키워드 관리 중")
            else:
                self.current_keywords_count_label.setText(f"총 {len(current_keywords)}개의 키워드 관리 중")
                self.current_keywords_table.setRowCount(len(current_keywords))
                
                for row, keyword_obj in enumerate(current_keywords):
                    # 날짜 (키워드 추가된 날짜) - 기본 색상
                    created_at = format_datetime_short(keyword_obj.created_at) if hasattr(keyword_obj, 'created_at') and keyword_obj.created_at else "-"
                    date_item = QTableWidgetItem(created_at)
                    self.current_keywords_table.setItem(row, 0, date_item)
                    
                    # 키워드 - 기본 색상
                    keyword_item = QTableWidgetItem(keyword_obj.keyword)
                    self.current_keywords_table.setItem(row, 1, keyword_item)
                    
                    # 카테고리 (마지막 부분만 표시)
                    category = getattr(keyword_obj, 'category', '') or ""
                    if category and ">" in category:
                        # "쇼핑/검색 > 반려동물 > 강아지 간식 > 개껌" → "개껌"
                        last_category = category.split(">")[-1].strip()
                        display_category = last_category
                    else:
                        display_category = category or "-"
                    
                    category_item = QTableWidgetItem(display_category)
                    
                    # 카테고리 색상 적용 (현재 방식: 전체 경로 비교)
                    if project_info and hasattr(project_info, 'category') and project_info.category and category and category != '-':
                        # 프로젝트 카테고리와 키워드 카테고리 전체 경로 비교
                        # 괄호 앞 부분만 비교 (예: "쇼핑/검색 > 반려동물 > 강아지 간식 > 개껌(95%)" → "쇼핑/검색 > 반려동물 > 강아지 간식 > 개껌")
                        project_category_clean = project_info.category.split('(')[0].strip()
                        keyword_category_clean = category.split('(')[0].strip()
                        
                        if project_category_clean == keyword_category_clean:
                            # 일치하면 초록색 글자
                            category_item.setForeground(QBrush(QColor('#059669')))  # 초록색
                        else:
                            # 불일치하면 빨간색 글자
                            category_item.setForeground(QBrush(QColor('#DC2626')))  # 빨간색
                    
                    self.current_keywords_table.setItem(row, 2, category_item)
                    
                    # 월검색량 (0인 경우도 0으로 표시) - 기본 색상
                    monthly_volume = getattr(keyword_obj, 'monthly_volume', 0) or 0
                    volume_display = f"{monthly_volume:,}"
                    volume_item = QTableWidgetItem(volume_display)
                    self.current_keywords_table.setItem(row, 3, volume_item)
            
        except Exception as e:
            logger.error(f"Failed to load keyword management data: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.keyword_history_table.setRowCount(0)
            self.current_keywords_table.setRowCount(0)
            self.keyword_stats_label.setText("키워드 이력 로드 실패")
            self.current_keywords_count_label.setText("현재 키워드 로드 실패")
    
    def load_ranking_history(self):
        """순위 이력 로드 - 현재 등록된 키워드들의 순위 변동 현황"""
        try:
            # 현재 등록된 키워드들 가져오기
            try:
                current_keywords = rank_tracking_service.get_project_keywords(self.project_id)
            except:
                current_keywords = []
            
            if not current_keywords:
                self.show_no_data_message(self.ranking_history_table, "등록된 키워드가 없습니다.")
                return
            
            # 프로젝트의 순위 데이터 가져오기
            try:
                ranking_overview = rank_tracking_service.get_ranking_overview(self.project_id)
                all_dates = ranking_overview.get('dates', [])
                keywords_data = ranking_overview.get('keywords', {})
            except:
                all_dates = []
                keywords_data = {}
            
            # 헤더 레이블 업데이트 (날짜 시간 포함)
            headers = ["키워드", "카테고리", "월검색량"]
            
            # 현재 순위 헤더
            if all_dates and len(all_dates) > 0:
                latest_date = all_dates[0]
                date_display = format_datetime_short(latest_date).replace("-", "/")  # MM-DD → MM/DD
                headers.append(f"현재 순위\n({date_display})")
            else:
                headers.append("현재 순위")
            
            # 이전 순위 헤더
            if all_dates and len(all_dates) > 1:
                previous_date = all_dates[1]
                date_display = format_datetime_short(previous_date).replace("-", "/")  # MM-DD → MM/DD
                headers.append(f"이전 순위\n({date_display})")
            else:
                headers.append("이전 순위")
            
            headers.append("순위변동")
            
            # 헤더 설정
            self.ranking_history_table.setHorizontalHeaderLabels(headers)
            
            # 헤더 높이 조정 (2줄 표시를 위해)
            header = self.ranking_history_table.horizontalHeader()
            header.setDefaultSectionSize(100)
            header.setMinimumHeight(50)  # 2줄 표시를 위한 높이
            
            # 각 키워드별로 순위 데이터 표시
            self.ranking_history_table.setRowCount(len(current_keywords))
            
            for row, keyword_obj in enumerate(current_keywords):
                # 키워드
                keyword_item = QTableWidgetItem(keyword_obj.keyword)
                self.ranking_history_table.setItem(row, 0, keyword_item)
                
                # 카테고리
                category = getattr(keyword_obj, 'category', '') or '-'
                category_display = category.split('>')[-1].strip() if '>' in category else category
                category_item = QTableWidgetItem(category_display)
                
                # 카테고리 색상 적용 (현재 방식: 전체 경로 비교)
                try:
                    project_info = rank_tracking_service.get_project_by_id(self.project_id)
                    if project_info and hasattr(project_info, 'category') and project_info.category and category and category != '-':
                        # 프로젝트 카테고리와 키워드 카테고리 전체 경로 비교
                        project_category_clean = project_info.category.split('(')[0].strip()
                        keyword_category_clean = category.split('(')[0].strip()
                        
                        if project_category_clean == keyword_category_clean:
                            # 일치하면 초록색 글자
                            category_item.setForeground(QBrush(QColor('#059669')))  # 초록색
                        else:
                            # 불일치하면 빨간색 글자
                            category_item.setForeground(QBrush(QColor('#DC2626')))  # 빨간색
                except:
                    pass  # 색상 적용 실패 시 기본 색상 유지
                
                self.ranking_history_table.setItem(row, 1, category_item)
                
                # 월검색량
                monthly_volume = getattr(keyword_obj, 'monthly_volume', 0) or 0
                volume_display = f"{monthly_volume:,}" if monthly_volume > 0 else "0"
                volume_item = SortableTableWidgetItem(volume_display, monthly_volume)
                self.ranking_history_table.setItem(row, 2, volume_item)
                
                # 순위 데이터 가져오기
                keyword_ranking_data = keywords_data.get(keyword_obj.keyword, {})
                current_rank = None
                previous_rank = None
                
                # 가장 최근 2개의 순위 데이터 찾기
                if all_dates and len(all_dates) > 0:
                    # 최신 날짜 (현재 순위)
                    latest_date = all_dates[0]
                    current_rank = keyword_ranking_data.get(latest_date)
                    
                    # 이전 날짜 (이전 순위)
                    if len(all_dates) > 1:
                        previous_date = all_dates[1]
                        previous_rank = keyword_ranking_data.get(previous_date)
                
                # 현재 순위
                if current_rank and isinstance(current_rank, int) and current_rank > 0:
                    if current_rank > 200 or current_rank == 999:
                        current_rank_display = "200위+"
                        current_rank_item = SortableTableWidgetItem(current_rank_display, 999)
                    else:
                        current_rank_display = f"{current_rank}위"
                        current_rank_item = SortableTableWidgetItem(current_rank_display, current_rank)
                else:
                    current_rank_item = SortableTableWidgetItem("-", 9999)  # 정렬용으로 더 큰 값 사용
                self.ranking_history_table.setItem(row, 3, current_rank_item)
                
                # 이전 순위
                if previous_rank and isinstance(previous_rank, int) and previous_rank > 0:
                    if previous_rank > 200 or previous_rank == 999:
                        previous_rank_display = "200위+"
                        previous_rank_item = SortableTableWidgetItem(previous_rank_display, 999)
                    else:
                        previous_rank_display = f"{previous_rank}위"
                        previous_rank_item = SortableTableWidgetItem(previous_rank_display, previous_rank)
                else:
                    previous_rank_item = SortableTableWidgetItem("-", 9999)  # 정렬용으로 더 큰 값 사용
                self.ranking_history_table.setItem(row, 4, previous_rank_item)
                
                # 순위변동
                change_item = QTableWidgetItem("-")
                if current_rank and previous_rank and isinstance(current_rank, int) and isinstance(previous_rank, int) and current_rank > 0 and previous_rank > 0:
                    rank_change = previous_rank - current_rank  # 이전 순위 - 현재 순위
                    
                    if rank_change > 0:
                        # 순위 상승 (초록색)
                        change_display = f"▲ {rank_change}"
                        change_item = QTableWidgetItem(change_display)
                        change_item.setForeground(QBrush(QColor(ModernStyle.COLORS['success'])))  # 초록색
                    elif rank_change < 0:
                        # 순위 하락 (빨간색)
                        change_display = f"▼ {abs(rank_change)}"
                        change_item = QTableWidgetItem(change_display)
                        change_item.setForeground(QBrush(QColor(ModernStyle.COLORS['danger'])))  # 빨간색
                    else:
                        # 순위 변동 없음
                        change_item = QTableWidgetItem("━")
                        change_item.setForeground(QBrush(QColor(ModernStyle.COLORS['text_secondary'])))
                
                self.ranking_history_table.setItem(row, 5, change_item)
            
            # 모든 데이터 추가 후 정렬 활성화
            self.ranking_history_table.setSortingEnabled(True)
            
        except Exception as e:
            logger.error(f"Failed to load ranking history: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.show_no_data_message(self.ranking_history_table, f"순위 이력 로드 실패: {e}")
    
    def show_no_data_message(self, table: QTableWidget, message: str):
        """데이터가 없을 때 메시지 표시"""
        table.setRowCount(0)  # 행을 0개로 설정하여 빈 테이블로 만듦
        
        # 헤더는 그대로 유지 (숨기지 않음)
        table.horizontalHeader().setVisible(True)
        table.verticalHeader().setVisible(False)
        
        # 빈 테이블 상태에서는 기본 스타일만 유지
        self.setup_table_style(table)
    
    
    def format_field_value(self, field_name: str, value: str) -> str:
        """필드값 포맷팅 (기존 통합관리프로그램과 동일)"""
        if not value or value == '':
            return '-'
        
        # 가격 필드인 경우 format_price_krw 사용
        if field_name == 'price':
            try:
                price_value = int(float(value))
                return format_price_krw(price_value)
            except (ValueError, TypeError):
                return format_price_krw(None)
        
        return str(value)
    
    def get_field_display_name(self, field_name: str) -> str:
        """필드명을 표시용으로 변환"""
        field_map = {
            'current_name': '상품명',
            'price': '가격',
            'store_name': '스토어명',
            'category': '카테고리',
            'image_url': '이미지URL'
        }
        return field_map.get(field_name, field_name)
    
    def get_action_display_name(self, action: str) -> str:
        """액션을 표시용으로 변환"""
        action_map = {
            'add': '추가',
            'delete': '삭제',
            'update': '수정'
        }
        return action_map.get(action, action)
    


# === 메인 위젯 ===

class RankTrackingWidget(QWidget):
    """순위 추적 메인 위젯 - 3-panel 레이아웃"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정 - 반응형"""
        main_layout = QVBoxLayout()
        margin = tokens.GAP_16)
        spacing = tokens.GAP_10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 헤더 (제목 + 사용법 툴팁)
        self.setup_header(main_layout)
        
        # 메인 콘텐츠 영역 - 3-panel 레이아웃 - 반응형
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(spacing)
        
        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Horizontal)
        
        # 좌측: 프로젝트 목록 - 반응형 너비
        sidebar_width = tokens.GAP_220)
        self.project_list = ProjectListWidget()
        self.project_list.setMinimumWidth(sidebar_width)
        self.project_list.setMaximumWidth(int(sidebar_width * 1.3))
        self.project_list.project_selected.connect(self.on_project_selected)
        self.project_list.project_deleted.connect(self.on_project_deleted)
        self.project_list.projects_selection_changed.connect(self.on_projects_selection_changed)
        splitter.addWidget(self.project_list)
        
        # 우측: 수직 레이아웃 (기본정보 + 키워드 테이블) - 반응형
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_margin = tokens.GAP_6)
        right_spacing = tokens.GAP_10)
        right_layout.setContentsMargins(right_margin, right_margin, right_margin, right_margin)
        right_layout.setSpacing(right_spacing)
        
        # 기본정보 영역 (위쪽)
        self.product_info_widget = self.create_product_info_widget()
        right_layout.addWidget(self.product_info_widget)
        
        # 키워드 테이블 영역 (아래쪽)
        self.ranking_table = RankingTableWidget()
        # 신호 연결: 프로젝트 정보 업데이트 시 목록 새로고침
        self.ranking_table.project_updated.connect(self.project_list.load_projects)
        # 신호 연결: 마지막 확인 시간 업데이트
        self.ranking_table.last_check_time_changed.connect(
            lambda s: self.last_check_label.setText(f"마지막 확인: {s or '-'}")
        )
        right_layout.addWidget(self.ranking_table)
        
        # 기본정보와 테이블의 비율 설정 (1:4)
        right_layout.setStretchFactor(self.product_info_widget, 1)
        right_layout.setStretchFactor(self.ranking_table, 4)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # 스플리터 비율 설정
        splitter.setStretchFactor(0, 0)  # 좌측 고정
        splitter.setStretchFactor(1, 1)  # 우측 확장
        
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
    
    def setup_header(self, layout):
        """헤더 섹션"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("📈 상품 순위추적")
        title_font_size = tokens.get_font_size('title')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}pt;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 다이얼로그 버튼 - 공용 사용법 버튼 사용
        self.help_button = ModernHelpButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()  # 오른쪽 여백
        
        layout.addLayout(header_layout)
    
    def create_product_info_widget(self):
        """기본정보 위젯 생성 - 원본과 동일한 레이아웃"""
        widget = QFrame()
        frame_padding = tokens.GAP_10)
        frame_border_radius = tokens.GAP_6)
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: #F8F9FA;
                border-radius: {frame_border_radius}px;
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: {frame_padding}px;
            }}
        """)
        
        layout = QGridLayout()
        grid_spacing = tokens.GAP_6)
        grid_v_spacing = tokens.GAP_6)
        layout.setSpacing(grid_spacing)
        layout.setVerticalSpacing(grid_v_spacing)
        
        # 헤더 스타일 설정 - 반응형
        header_padding = tokens.GAP_2)
        value_padding_v = tokens.GAP_4)
        value_padding_h = tokens.GAP_8)
        value_border_radius = tokens.GAP_4)
        
        header_style = f"""
            QLabel {{
                color: #495057;
                font-weight: 600;
                padding: {header_padding}px 0px;
                border: none;
            }}
        """
        
        value_style = f"""
            QLabel {{ 
                padding: {value_padding_v}px {value_padding_h}px; 
                border: 1px solid transparent;
                border-radius: {value_border_radius}px;
                background-color: #FFFFFF;
                color: #212529;
            }} 
            QLabel:hover {{ 
                border: 1px solid #DEE2E6; 
                background-color: #F8F9FA;
            }}
        """
        
        # Row 0: 상품ID (새로고침 버튼 포함) - 반응형
        product_id_header = QLabel("상품ID")
        header_font_size = tokens.get_font_size('normal')
        product_id_header.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                color: #495057;
                font-weight: 600;
                padding: {header_padding}px 0px;
                border: none;
            }}
        """)
        layout.addWidget(product_id_header, 0, 0)
        
        # 상품ID 행에 수평 레이아웃 생성 (ID + 새로고침 버튼)
        product_id_layout = QHBoxLayout()
        
        self.product_id_label = QLabel("-")
        self.product_id_label.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                padding: {value_padding_v}px {value_padding_h}px; 
                border: 1px solid transparent;
                border-radius: {value_border_radius}px;
                background-color: #FFFFFF;
                color: #212529;
            }} 
            QLabel:hover {{ 
                border: 1px solid #DEE2E6; 
                background-color: #F8F9FA;
            }}
        """)
        product_id_layout.addWidget(self.product_id_label)
        
        # 새로고침 버튼 (반응형)
        btn_size = tokens.GAP_20)
        self.refresh_product_button = QPushButton("⟲")
        self.refresh_product_button.setToolTip("상품 정보 새로고침")
        self.refresh_product_button.setFixedSize(btn_size + 2, btn_size + 2)
        border_radius = tokens.GAP_4)
        btn_font_size = tokens.get_font_size('normal')
        self.refresh_product_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #F3F4F6;
                color: #6B7280;
                border: 1px solid #D1D5DB;
                border-radius: {border_radius}px;
                font-size: {btn_font_size}pt;
                font-weight: 500;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #E5E7EB;
                color: #374151;
                border-color: #9CA3AF;
            }}
            QPushButton:pressed {{
                background-color: #D1D5DB;
                color: #111827;
                border-color: #6B7280;
            }}
            QPushButton:disabled {{
                background-color: #F9FAFB;
                color: #D1D5DB;
                border-color: #F3F4F6;
            }}
        """)
        self.refresh_product_button.clicked.connect(self.refresh_product_info)
        product_id_layout.addWidget(self.refresh_product_button)
        product_id_layout.addStretch()  # 오른쪽 여백
        
        # 레이아웃을 위젯으로 만들어서 그리드에 추가
        product_id_widget = QWidget()
        product_id_widget.setLayout(product_id_layout)
        layout.addWidget(product_id_widget, 0, 1)
        
        # Row 1: 상품명 - 반응형
        product_name_header = QLabel("상품명")
        product_name_header.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                color: #495057;
                font-weight: 600;
                padding: {header_padding}px 0px;
                border: none;
            }}
        """)
        layout.addWidget(product_name_header, 1, 0)
        
        # 상품명 행에 수평 레이아웃 생성 (상품명 + 변경사항 버튼)
        product_name_layout = QHBoxLayout()
        
        self.product_name_label = QLabel("-")
        self.product_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                padding: {value_padding_v}px {value_padding_h}px; 
                border: 1px solid transparent;
                border-radius: {value_border_radius}px;
                background-color: #FFFFFF;
                color: #212529;
            }} 
            QLabel:hover {{ 
                border: 1px solid #DEE2E6; 
                background-color: #F8F9FA;
            }}
        """)
        product_name_layout.addWidget(self.product_name_label)
        
        # 변경사항 버튼 - 반응형
        self.changes_button = QPushButton("📝")
        self.changes_button.setToolTip("프로젝트 변경사항 보기")
        self.changes_button.setFixedSize(btn_size + 2, btn_size + 2)
        self.changes_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #F3F4F6;
                color: #6B7280;
                border: 1px solid #D1D5DB;
                border-radius: {border_radius}px;
                font-size: {btn_font_size}pt;
                font-weight: 500;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #E5E7EB;
                color: #374151;
                border-color: #9CA3AF;
            }}
            QPushButton:pressed {{
                background-color: #D1D5DB;
                color: #111827;
                border-color: #6B7280;
            }}
            QPushButton:disabled {{
                background-color: #F9FAFB;
                color: #D1D5DB;
                border-color: #F3F4F6;
            }}
        """)
        self.changes_button.clicked.connect(self.show_project_changes)
        product_name_layout.addWidget(self.changes_button)
        product_name_layout.addStretch()  # 오른쪽 여백
        
        # 레이아웃을 위젯으로 만들어서 그리드에 추가
        product_name_widget = QWidget()
        product_name_widget.setLayout(product_name_layout)
        layout.addWidget(product_name_widget, 1, 1)
        
        # Row 2: 스토어명 - 반응형
        store_name_header = QLabel("스토어명")
        store_name_header.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                color: #495057;
                font-weight: 600;
                padding: {header_padding}px 0px;
                border: none;
            }}
        """)
        layout.addWidget(store_name_header, 2, 0)
        
        self.store_name_label = QLabel("-")
        self.store_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                padding: {value_padding_v}px {value_padding_h}px; 
                border: 1px solid transparent;
                border-radius: {value_border_radius}px;
                background-color: #FFFFFF;
                color: #212529;
            }} 
            QLabel:hover {{ 
                border: 1px solid #DEE2E6; 
                background-color: #F8F9FA;
            }}
        """)
        layout.addWidget(self.store_name_label, 2, 1)
        
        # Row 3: 가격 - 반응형
        price_header = QLabel("가격")
        price_header.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                color: #495057;
                font-weight: 600;
                padding: {header_padding}px 0px;
                border: none;
            }}
        """)
        layout.addWidget(price_header, 3, 0)
        
        self.price_label = QLabel("-")
        self.price_label.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                padding: {value_padding_v}px {value_padding_h}px; 
                border: 1px solid transparent;
                border-radius: {value_border_radius}px;
                background-color: #FFFFFF;
                color: #212529;
            }} 
            QLabel:hover {{ 
                border: 1px solid #DEE2E6; 
                background-color: #F8F9FA;
            }}
        """)
        layout.addWidget(self.price_label, 3, 1)
        
        # Row 4: 카테고리 - 반응형
        category_header = QLabel("카테고리")
        category_header.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                color: #495057;
                font-weight: 600;
                padding: {header_padding}px 0px;
                border: none;
            }}
        """)
        layout.addWidget(category_header, 4, 0)
        
        self.category_label = QLabel("-")
        self.category_label.setStyleSheet(f"""
            QLabel {{
                font-size: {header_font_size}pt;
                padding: {value_padding_v}px {value_padding_h}px; 
                border: 1px solid transparent;
                border-radius: {value_border_radius}px;
                background-color: #FFFFFF;
                color: #212529;
            }} 
            QLabel:hover {{ 
                border: 1px solid #DEE2E6; 
                background-color: #F8F9FA;
            }}
        """)
        layout.addWidget(self.category_label, 4, 1)
        
        # 컬럼 너비 설정 (헤더는 고정폭, 값은 유동적)
        layout.setColumnStretch(0, 0)  # 헤더 컬럼은 고정
        layout.setColumnStretch(1, 1)  # 값 컬럼은 늘어남
        
        # 마지막 확인 시간 (카드 외부에 별도 표시) - 반응형
        self.last_check_label = QLabel("마지막 확인: -")
        last_check_font_size = tokens.get_font_size('normal')
        margin_top = tokens.GAP_6)
        self.last_check_label.setStyleSheet(f"""
            QLabel {{
                font-size: {last_check_font_size}pt;
                color: #495057;
                margin-top: {margin_top}px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.last_check_label, 5, 0, 1, 2)  # Row 5로 이동 - 두 컬럼에 걸쳐서 표시
        
        widget.setLayout(layout)
        return widget
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = """
📝 순위추적 모듈 사용법 (3단계):

1️⃣ 프로젝트 생성하기
• '➕ 새 프로젝트' 버튼 클릭
• 프로젝트명 입력 후 네이버 쇼핑 상품 URL 붙여넣기
• 상품 정보(제목, 카테고리)가 자동 추출됩니다

2️⃣ 키워드 관리하기  
• 프로젝트 선택 후 '🔤 키워드 추가' 클릭
• 순위를 추적할 키워드 입력 (개별 또는 줄바꿈으로 다중 입력)
• 월 검색량과 카테고리가 자동 조회됩니다

3️⃣ 순위 추적하기
• '🔍 순위 확인' 클릭하여 현재 네이버 쇼핑 순위 조회
• 1-10위: 녹색, 11-50위: 노란색, 51위 이하: 회색 표시
• 🔍 '순위 이력' 클릭으로 시간별 순위 변동 확인

💡 통합관리프로그램 고급 기능:
• Foundation DB 기반 영구 데이터 저장 및 관리
• 다중 프로젝트 📤 엑셀 내보내기로 전체 데이터 저장
• 네이버 개발자 API + 검색광고 API 이중 연동 시스템
• 실시간 월검색량 및 카테고리 자동 조회 및 업데이트
• 적응형 API 딜레이 및 병렬 처리로 빠른 순위 확인
• 키워드 더블클릭으로 삭제 가능
• 프로젝트별 순위 이력 추적 및 차트 표시
• SQLite 기반 순위 기록 영구 저장
• 애플리케이션 재시작 후에도 모든 프로젝트 및 이력 유지
        """
        
        ModernHelpDialog.show_help(
            parent=self,
            title="📈 상품 순위추적 사용법",
            message=help_text.strip(),
            button_widget=self.help_button
        )
    
    def on_project_selected(self, project_id):
        """프로젝트 선택 처리"""
        try:
            project = rank_tracking_service.get_project_by_id(project_id)
            if project:
                # 기본정보 업데이트
                self.update_product_info(project)
                # 테이블 업데이트
                self.ranking_table.set_project(project)
        except Exception as e:
            logger.error(f"프로젝트 선택 오류: {e}")
    
    def on_projects_selection_changed(self, selected_projects):
        """다중 프로젝트 선택 변경 처리"""
        try:
            # ranking_table에 선택된 프로젝트들 전달
            self.ranking_table.set_selected_projects(selected_projects)
        except Exception as e:
            logger.error(f"다중 프로젝트 선택 처리 오류: {e}")
    
    def on_project_deleted(self, project_id: int):
        """프로젝트 삭제 처리"""
        self.project_list.load_projects()
        self.ranking_table.clear_project()
        # 기본정보도 초기화
        self.update_product_info(None)
    
    def update_product_info(self, project):
        """기본정보 업데이트"""
        # 현재 프로젝트 저장
        self.current_project = project
        
        if not project:
            self.product_id_label.setText("-")
            self.product_name_label.setText("-")
            self.store_name_label.setText("-")
            self.price_label.setText("-")
            self.category_label.setText("-")
            self.last_check_label.setText("마지막 확인: -")
            return
        
        self.product_id_label.setText(str(project.product_id) if project.product_id else "-")
        self.product_name_label.setText(project.current_name if project.current_name else "-")
        self.store_name_label.setText(project.store_name if hasattr(project, 'store_name') and project.store_name else "-")
        
        # 가격 포맷팅 (toolbox.formatters 사용)
        if hasattr(project, 'price') and project.price:
            self.price_label.setText(format_price_krw(project.price))
        else:
            self.price_label.setText("-")
        
        self.category_label.setText(project.category if hasattr(project, 'category') and project.category else "-")
        
        # 프로젝트 ID 저장 (마지막 확인 시간은 시그널을 통해 업데이트됨)
        self.current_project_id = project.id
    
    def refresh_product_info(self):
        """상품 정보 새로고침 - 프로젝트 정보 + 키워드 월검색량/카테고리 업데이트"""
        if not hasattr(self, 'current_project') or not self.current_project:
            log_manager.add_log("⚠️ 새로고침할 프로젝트가 선택되지 않았습니다.", "warning")
            return
        
        # 버튼 비활성화 (새로고침 중)
        self.refresh_product_button.setEnabled(False)
        self.refresh_product_button.setText("⏳")
        
        try:
            # Service를 통한 새로고침 처리
            result = rank_tracking_service.refresh_project_info(self.current_project.id)
            
            if result['success']:
                # 프로젝트 정보 업데이트
                updated_project = rank_tracking_service.get_project_by_id(self.current_project.id)
                if updated_project:
                    self.update_product_info(updated_project)
                
                # 키워드 월검색량 및 카테고리 새로고침 (백그라운드 업데이트)
                keywords = rank_tracking_service.get_project_keywords(self.current_project.id)
                if keywords:
                    keyword_names = [kw.keyword for kw in keywords]
                    log_manager.add_log(f"🔍 {len(keyword_names)}개 키워드의 월검색량/카테고리 업데이트를 시작합니다.", "info")
                    
                    # 키워드 정보 백그라운드 업데이트 시작
                    rank_tracking_service.start_background_keyword_info_update(self.current_project.id, keyword_names, updated_project)
                else:
                    log_manager.add_log("📝 새로고침할 키워드가 없습니다.", "info")
                
                log_manager.add_log(result['message'], "success")
            else:
                log_manager.add_log(result['message'], "error")
                
        except Exception as e:
            logger.error(f"상품 정보 새로고침 실패: {e}")
            log_manager.add_log(f"❌ 상품 정보 새로고침 중 오류가 발생했습니다: {str(e)}", "error")
        
        finally:
            # 버튼 복원
            self.refresh_product_button.setEnabled(True)
            self.refresh_product_button.setText("⟲")
    
    def show_project_changes(self):
        """프로젝트 변경사항 다이얼로그 표시"""
        if not hasattr(self, 'current_project') or not self.current_project:
            ModernInfoDialog.info(self, "알림", "프로젝트를 먼저 선택해주세요.")
            return
            
        # 변경사항 다이얼로그 표시
        dialog = ProjectHistoryDialog(
            project_id=self.current_project.id, 
            project_name=self.current_project.current_name,
            parent=self
        )
        dialog.exec()
    
