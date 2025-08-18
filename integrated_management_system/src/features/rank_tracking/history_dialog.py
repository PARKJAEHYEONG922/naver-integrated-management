"""
프로젝트 변경사항 이력 다이얼로그
기존 통합관리프로그램과 동일한 3개 탭 구조
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QBrush, QColor

from src.toolbox.ui_kit import ModernStyle, SortableTableWidgetItem
from src.desktop.common_log import log_manager
from src.foundation.logging import get_logger
from .service import rank_tracking_service

logger = get_logger("features.rank_tracking.history_dialog")




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
        header_label.setFont(QFont("맑은 고딕", 16, QFont.Bold))
        header_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_primary']}; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
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
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['secondary']};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['secondary']};
                opacity: 0.8;
            }}
        """)
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
        
        self.basic_info_table.setColumnWidth(0, 150)  # 변경 일시
        self.basic_info_table.setColumnWidth(1, 100)  # 변경 필드
        
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
        left_title.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        left_title.setStyleSheet(f"""
            color: {ModernStyle.COLORS['text_primary']};
            padding: 5px;
            background-color: {ModernStyle.COLORS['bg_card']};
            border-radius: 4px;
        """)
        left_layout.addWidget(left_title)
        
        # 통계 레이블
        self.keyword_stats_label = QLabel("총 0건의 키워드이력 (추가 0건, 삭제 0건)")
        self.keyword_stats_label.setFont(QFont("맑은 고딕", 10))
        self.keyword_stats_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']}; padding: 2px;")
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
        
        self.keyword_history_table.setColumnWidth(0, 100)  # 날짜
        self.keyword_history_table.setColumnWidth(1, 200)  # 키워드 (더 넓게)
        self.keyword_history_table.setColumnWidth(2, 60)   # 작업
        
        left_layout.addWidget(self.keyword_history_table)
        left_widget.setLayout(left_layout)
        
        # === 오른쪽 영역: 현재 관리 키워드 ===
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(8)
        
        # 오른쪽 제목
        right_title = QLabel("🔍 현재 관리 키워드")
        right_title.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        right_title.setStyleSheet(f"""
            color: {ModernStyle.COLORS['text_primary']};
            padding: 5px;
            background-color: {ModernStyle.COLORS['bg_card']};
            border-radius: 4px;
        """)
        right_layout.addWidget(right_title)
        
        # 키워드 개수 레이블
        self.current_keywords_count_label = QLabel("총 0개의 키워드 관리 중")
        self.current_keywords_count_label.setFont(QFont("맑은 고딕", 10))
        self.current_keywords_count_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']}; padding: 2px;")
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
        
        self.current_keywords_table.setColumnWidth(0, 100)  # 날짜
        self.current_keywords_table.setColumnWidth(1, 150)  # 키워드 (더 넓게)
        self.current_keywords_table.setColumnWidth(2, 150)  # 카테고리 (줄임: 200 → 150)
        self.current_keywords_table.setColumnWidth(3, 80)   # 월검색량
        
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
        title_label.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_primary']}; padding: 5px;")
        title_layout.addWidget(title_label)
        
        # 마지막 순위확인 정보 (프로젝트에서 가져오기)
        self.last_rank_check_label = QLabel("(최신 확인: 2025-08-15 22:17)")
        self.last_rank_check_label.setFont(QFont("맑은 고딕", 10))
        self.last_rank_check_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']}; padding: 5px;")
        title_layout.addWidget(self.last_rank_check_label)
        
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
                border-radius: 8px;
                gridline-color: {ModernStyle.COLORS['border']};
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 8px;
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
                padding: 10px;
                border: none;
                font-weight: 600;
                font-size: 12px;
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
        self.ranking_history_table.setColumnWidth(3, 100)  # 현재 순위 (두 줄 표시용으로 넓게)
        self.ranking_history_table.setColumnWidth(4, 100)  # 이전 순위 (두 줄 표시용으로 넓게)
        self.ranking_history_table.setColumnWidth(5, 120)  # 순위변동 (80 × 1.5 = 120)
        
        main_layout.addWidget(self.ranking_history_table)
        main_widget.setLayout(main_layout)
        
        self.tab_widget.addTab(main_widget, "📈 순위 이력")
    
    def setup_table_style(self, table: QTableWidget):
        """테이블 스타일 설정"""
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        
        # 가로 스크롤 활성화 (키워드/카테고리 길이 문제 해결)
        table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        table.setWordWrap(False)  # 줄바꿈 비활성화로 스크롤 유도
        
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                gridline-color: {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']}30;
            }}
            QTableWidget::item:alternate {{
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 10px;
                border: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
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
            history_data = rank_tracking_service.get_basic_info_change_history(self.project_id)
            
            if not history_data:
                self.show_no_data_message(self.basic_info_table, "기본정보 변경 이력이 없습니다.")
                return
            
            self.basic_info_table.setRowCount(len(history_data))
            
            for row, record in enumerate(history_data):
                # 변경 일시 (기존 통합관리프로그램과 동일한 포맷)
                change_time = self.format_datetime_full(record.get('change_time'))
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
            history_data = rank_tracking_service.get_keyword_management_history(self.project_id)
            
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
                    action_time = self.format_datetime(record.get('action_time'))
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
            current_keywords = rank_tracking_service.get_project_keywords(self.project_id)
            
            # 프로젝트 정보 조회 (카테고리 비교용)
            project_info = rank_tracking_service.get_project_by_id(self.project_id)
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
                    # 색상 준비
                    success_brush = QBrush(QColor(ModernStyle.COLORS['success']))
                    danger_brush = QBrush(QColor(ModernStyle.COLORS['danger']))
                    
                    # 날짜 (키워드 추가된 날짜) - 기본 색상
                    created_at = self.format_datetime(keyword_obj.created_at) if keyword_obj.created_at else "-"
                    date_item = QTableWidgetItem(created_at)
                    self.current_keywords_table.setItem(row, 0, date_item)
                    
                    # 키워드 - 기본 색상
                    keyword_item = QTableWidgetItem(keyword_obj.keyword)
                    self.current_keywords_table.setItem(row, 1, keyword_item)
                    
                    # 카테고리 (마지막 부분만) - 일치 여부에 따라 색상 결정
                    category = keyword_obj.category or ""
                    if category and ">" in category:
                        # "쇼핑/검색 > 반려동물 > 강아지 간식 > 개껌" → "개껌"
                        last_category = category.split(">")[-1].strip()
                        display_category = last_category
                    else:
                        display_category = category or "-"
                    
                    category_item = QTableWidgetItem(display_category)
                    
                    # 카테고리 색상 적용 (메인 UI와 동일한 방식)
                    if project_category_base and category and category != '-':
                        # 키워드 카테고리에서 괄호 앞 부분만 추출
                        keyword_category_base = category.split('(')[0].strip()
                        
                        if project_category_base == keyword_category_base:
                            # 일치하면 초록색 글자
                            category_item.setForeground(QBrush(QColor('#059669')))  # 초록색
                        else:
                            # 불일치하면 빨간색 글자
                            category_item.setForeground(QBrush(QColor('#DC2626')))  # 빨간색
                    
                    self.current_keywords_table.setItem(row, 2, category_item)
                    
                    # 월검색량 (0인 경우도 0으로 표시) - 기본 색상
                    monthly_volume = keyword_obj.monthly_volume or 0
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
            current_keywords = rank_tracking_service.get_project_keywords(self.project_id)
            
            if not current_keywords:
                self.show_no_data_message(self.ranking_history_table, "등록된 키워드가 없습니다.")
                return
            
            # 프로젝트 정보 조회 (마지막 순위확인 시간과 카테고리 비교용)
            project_info = rank_tracking_service.get_project_by_id(self.project_id)
            project_category_base = ""
            last_check_time = None
            
            if project_info:
                if hasattr(project_info, 'category') and project_info.category:
                    # 프로젝트 카테고리에서 마지막 부분 추출 (메인 UI와 동일한 방식)
                    project_category_base = project_info.category.split('>')[-1].strip() if '>' in project_info.category else project_info.category.strip()
                
                # 마지막 순위확인 시간 - 메인 UI에서 전달받은 시간 사용
                logger.info(f"전달받은 현재 시간: {self.current_time}")
                if self.current_time:
                    # 시간 포맷 그대로 사용 (이미 "MM/DD\nHH:MM" 형태)
                    formatted_time = self.current_time.replace('\n', ' ')
                    self.last_rank_check_label.setText(f"(최신 확인: {formatted_time})")
                    logger.info(f"마지막 확인 시간 표시됨: {formatted_time}")
                else:
                    self.last_rank_check_label.setText("(순위 확인 기록 없음)")
                    logger.warning("마지막 확인 시간이 None이어서 기록 없음으로 표시")
            
            # 각 키워드별로 순위 변동 데이터 계산
            ranking_changes = []
            current_time_for_header = None
            previous_time_for_header = None
            
            for keyword_obj in current_keywords:
                keyword = keyword_obj.keyword
                
                # 키워드의 모든 순위 기록을 시간순으로 가져오기
                keyword_rankings = rank_tracking_service.get_keyword_ranking_history(self.project_id, keyword)
                
                if not keyword_rankings:
                    continue
                
                # 현재 순위 (가장 최근 기록) - 숫자만 표시
                current_rank = keyword_rankings[0].get('rank', 999)
                current_rank_display = f"{current_rank}" if current_rank <= 200 else "200+"
                current_rank_time = keyword_rankings[0].get('created_at', '')
                
                # 헤더용 시간 정보 (첫 번째 키워드에서만 설정) - 메인 테이블 시간 우선 사용
                if current_time_for_header is None:
                    if self.current_time:
                        current_time_for_header = self.current_time.replace('\n', ' ')
                    elif current_rank_time:
                        current_time_for_header = self.format_datetime_short(current_rank_time)
                
                # 이전 순위 (두 번째로 최근 기록) - 숫자만 표시
                previous_rank = None
                previous_rank_display = "-"
                change_display = "-"
                
                if len(keyword_rankings) >= 2:
                    previous_rank = keyword_rankings[1].get('rank', 999)
                    previous_rank_display = f"{previous_rank}" if previous_rank <= 200 else "200+"
                    previous_rank_time = keyword_rankings[1].get('created_at', '')
                    
                    # 헤더용 시간 정보 (첫 번째 키워드에서만 설정) - 메인 테이블 시간 우선 사용
                    if previous_time_for_header is None:
                        if self.previous_time:
                            previous_time_for_header = self.previous_time.replace('\n', ' ')
                        elif previous_rank_time:
                            previous_time_for_header = self.format_datetime_short(previous_rank_time)
                else:
                    # 이전 순위가 없는 경우
                    if previous_time_for_header is None:
                        previous_time_for_header = ""
                    
                
                # 순위 변동 계산
                if previous_rank is None:
                    # 이전순위가 없는 경우 (첫 번째 순위 확인)
                    change_display = "-"
                elif current_rank > 200 and previous_rank > 200:
                    change_display = "-"
                elif current_rank > 200:
                    change_display = "↓ 200위밖"
                elif previous_rank > 200:
                    change_display = f"↑ {200 - current_rank + 1}위 상승"
                else:
                    rank_diff = previous_rank - current_rank
                    if rank_diff > 0:
                        change_display = f"↑ {rank_diff}위 상승"
                    elif rank_diff < 0:
                        change_display = f"↓ {abs(rank_diff)}위 하락"
                    else:
                        change_display = "-"
                
                ranking_changes.append({
                    'keyword': keyword,
                    'category': getattr(keyword_obj, 'category', '') or '-',
                    'monthly_volume': getattr(keyword_obj, 'monthly_volume', -1),
                    'current_rank': current_rank,
                    'current_rank_display': current_rank_display,  # 숫자만 표시
                    'previous_rank_display': previous_rank_display,  # 숫자만 표시
                    'change_display': change_display,
                    'project_category_base': project_category_base
                })
            
            # 테이블 헤더에 시간 정보 추가 - 실제 데이터에서 시간 가져오기
            if current_time_for_header:
                current_header = f"현재 순위\n({current_time_for_header})"
            else:
                current_header = "현재 순위"
            
            if previous_time_for_header:
                previous_header = f"이전 순위\n({previous_time_for_header})"
            else:
                previous_header = "이전 순위"
            
            # 헤더 설정
            self.ranking_history_table.setHorizontalHeaderItem(3, QTableWidgetItem(current_header))
            self.ranking_history_table.setHorizontalHeaderItem(4, QTableWidgetItem(previous_header))
            
            if not ranking_changes:
                # 데이터가 없어도 기본 헤더는 설정
                self.ranking_history_table.setHorizontalHeaderItem(3, QTableWidgetItem("현재 순위"))
                self.ranking_history_table.setHorizontalHeaderItem(4, QTableWidgetItem("이전 순위"))
                self.show_no_data_message(self.ranking_history_table, "순위 확인 이력이 없습니다.")
                return
            
            # 테이블에 데이터 표시
            self.ranking_history_table.setRowCount(len(ranking_changes))
            
            for row, data in enumerate(ranking_changes):
                # 키워드
                keyword_item = QTableWidgetItem(data['keyword'])
                self.ranking_history_table.setItem(row, 0, keyword_item)
                
                # 카테고리 (색상 적용)
                category = data['category']
                category_display = category.split('>')[-1].strip() if '>' in category else category
                category_item = QTableWidgetItem(category_display)
                
                # 카테고리 색상 적용 (키워드 관리 탭과 동일)
                if data['project_category_base'] and category != '-':
                    keyword_category_base = category.split('(')[0].strip()
                    if data['project_category_base'] == keyword_category_base:
                        # 일치하면 초록색 글자
                        category_item.setForeground(QBrush(QColor('#059669')))
                    else:
                        # 불일치하면 빨간색 글자
                        category_item.setForeground(QBrush(QColor('#DC2626')))
                
                self.ranking_history_table.setItem(row, 1, category_item)
                
                # 월검색량
                monthly_volume = data['monthly_volume']
                if monthly_volume == -1:
                    volume_display = "-"
                elif monthly_volume == 0:
                    volume_display = "0"
                else:
                    volume_display = f"{monthly_volume:,}"
                
                volume_item = SortableTableWidgetItem(volume_display, monthly_volume if monthly_volume >= 0 else -1)
                self.ranking_history_table.setItem(row, 2, volume_item)
                
                # 현재 순위 - 숫자만 표시
                current_rank_item = SortableTableWidgetItem(data['current_rank_display'], data['current_rank'])
                # 순위에 따른 색상 적용
                if data['current_rank'] <= 10:
                    current_rank_item.setForeground(QBrush(QColor('#059669')))  # 초록색 (10위 이내)
                elif data['current_rank'] <= 50:
                    current_rank_item.setForeground(QBrush(QColor('#D97706')))  # 주황색 (50위 이내)
                elif data['current_rank'] <= 200:
                    current_rank_item.setForeground(QBrush(QColor('#DC2626')))  # 빨간색 (200위 이내)
                else:
                    current_rank_item.setForeground(QBrush(QColor('#6B7280')))  # 회색 (200위 밖)
                
                self.ranking_history_table.setItem(row, 3, current_rank_item)
                
                # 이전 순위 - 숫자만 표시, 정렬용 데이터도 설정
                previous_rank_item = SortableTableWidgetItem(data['previous_rank_display'], previous_rank)
                self.ranking_history_table.setItem(row, 4, previous_rank_item)
                
                # 순위변동
                change_item = QTableWidgetItem(data['change_display'])
                if "상승" in data['change_display']:
                    change_item.setForeground(QBrush(QColor('#059669')))  # 초록색 (상승)
                elif "하락" in data['change_display']:
                    change_item.setForeground(QBrush(QColor('#DC2626')))  # 빨간색 (하락)
                    
                self.ranking_history_table.setItem(row, 5, change_item)
            
            # 행 높이 조정 - 적당한 높이로 설정
            for row in range(len(ranking_changes)):
                self.ranking_history_table.setRowHeight(row, 35)  # 50px에서 35px로 줄임
            
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
    
    def format_datetime(self, dt) -> str:
        """날짜시간 포맷팅 (간단 버전)"""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        
        if isinstance(dt, datetime):
            return dt.strftime("%m/%d %H:%M")
        
        return str(dt) if dt else "-"
    
    def format_field_value(self, field_name: str, value: str) -> str:
        """필드값 포맷팅 (기존 통합관리프로그램과 동일)"""
        if not value or value == '':
            return '-'
        
        # 가격 필드인 경우 천 단위 콤마와 "원" 추가
        if field_name == 'price':
            try:
                price_value = int(float(value))
                return f"{price_value:,}원"
            except (ValueError, TypeError):
                return str(value)
        
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
    
    def format_datetime_full(self, datetime_str: str) -> str:
        """날짜시간을 전체 포맷으로 변환 (YYYY-MM-DD HH:MM:SS)"""
        if not datetime_str:
            return ""
        
        try:
            # 문자열을 datetime 객체로 변환
            if isinstance(datetime_str, str):
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            else:
                dt = datetime_str
                
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(datetime_str)
    
    def format_datetime_short(self, datetime_str: str) -> str:
        """날짜시간을 단축 포맷으로 변환 (MM/DD HH:MM)"""
        if not datetime_str:
            return ""
        
        try:
            # 문자열을 datetime 객체로 변환
            if isinstance(datetime_str, str):
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            else:
                dt = datetime_str
                
            return dt.strftime("%m/%d %H:%M")
        except Exception:
            return ""