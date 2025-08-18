"""
파워링크 광고비 분석기 결과 위젯 (우측 패널)
분석 결과 테이블, 키워드 관리, 히스토리 기능을 포함
"""
from typing import List, Dict, Optional
from datetime import datetime
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, 
    QCheckBox, QMessageBox, QFileDialog, QHeaderView, QDialog,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from src.toolbox.ui_kit import ModernStyle, SortableTableWidgetItem
from src.desktop.common_log import log_manager
from .control_widget import ModernButton
from src.foundation.db import get_db
from src.foundation.logging import get_logger
from .models import KeywordAnalysisResult, keyword_database

logger = get_logger("features.powerlink_analyzer.results_widget")


class PowerLinkSaveDialog(QDialog):
    """PowerLink 분석 저장 완료 다이얼로그"""
    
    def __init__(self, session_id: int, session_name: str, keyword_count: int, is_duplicate: bool = False, parent=None):
        super().__init__(parent)
        self.session_id = session_id
        self.session_name = session_name
        self.keyword_count = keyword_count
        self.is_duplicate = is_duplicate
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화 (글씨 잘림 방지 및 크기 조정)"""
        self.setWindowTitle("저장 완료")
        self.setModal(True)
        self.setFixedSize(420, 220)  # 크기 증가로 글씨 잘림 방지
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 25, 30, 25)
        
        # 체크 아이콘과 제목
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        
        # 체크 아이콘
        icon_label = QLabel("✅")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #10b981;
            }
        """)
        title_layout.addWidget(icon_label)
        
        # 제목 텍스트
        title_label = QLabel("저장 완료")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-left: 8px;
            }}
        """)
        title_layout.addWidget(title_label)
        
        layout.addLayout(title_layout)
        
        # 메인 메시지 (중복 여부에 따라 변경)
        if self.is_duplicate:
            message_text = "이미 데이터베이스에 기록이 저장되었습니다."
        else:
            message_text = "프로그램 데이터베이스에 기록이 저장되었습니다."
            
        message_label = QLabel(message_text)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_primary']};
                text-align: center;
                padding: 5px;
            }}
        """)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setWordWrap(True)  # 자동 줄바꿈
        layout.addWidget(message_label)
        
        # 안내 메시지
        guide_label = QLabel("엑셀로 내보내기도 원하시면 내보내기 버튼을\n눌러주세요.")
        guide_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {ModernStyle.COLORS['text_secondary']};
                text-align: center;
                line-height: 1.5;
                padding: 5px;
            }}
        """)
        guide_label.setAlignment(Qt.AlignCenter)
        guide_label.setWordWrap(True)  # 자동 줄바꿈
        layout.addWidget(guide_label)
        
        layout.addStretch()
        
        # 버튼들
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 엑셀 내보내기 버튼 (파란색)
        self.export_button = ModernButton("📊 엑셀 내보내기", "primary")
        self.export_button.setMinimumHeight(40)
        self.export_button.setMinimumWidth(130)
        button_layout.addWidget(self.export_button)
        
        # 완료 버튼 (회색)
        self.complete_button = ModernButton("✅ 완료", "secondary")
        self.complete_button.setMinimumHeight(40)
        self.complete_button.setMinimumWidth(130)
        button_layout.addWidget(self.complete_button)
        
        layout.addLayout(button_layout)
        
        # 시그널 연결
        self.complete_button.clicked.connect(self.accept)
        self.export_button.clicked.connect(self.export_to_excel)
        
    def export_to_excel(self):
        """엑셀 내보내기 실행"""
        try:
            # 파일 저장 다이얼로그
            from datetime import datetime
            from src.foundation.db import get_db
            
            # 파일명 생성 (세션 생성 시간 사용)
            if self.session_id and self.session_id > 0:
                # DB에서 세션 정보 가져오기
                db = get_db()
                session_info = db.get_powerlink_session_info(self.session_id)
                if session_info and 'created_at' in session_info:
                    # 세션 생성 시간 사용
                    session_time = datetime.fromisoformat(session_info['created_at'])
                    time_str = session_time.strftime('%Y%m%d_%H%M%S')
                else:
                    # 세션 정보가 없으면 현재 시간 사용
                    time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            else:
                # 중복이거나 세션 ID가 없으면 현재 시간 사용
                time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                
            # 단순한 파일명 생성
            default_filename = f"파워링크광고비분석_{time_str}.xlsx"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "엑셀 파일 저장",
                default_filename,
                "Excel files (*.xlsx)"
            )
            
            if file_path:
                # 엑셀 파일 생성
                self.create_excel_file(file_path)
                
                # 저장 완료 다이얼로그 (엑셀 내보내기 버튼 근처에 표시)
                from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
                success_dialog = ModernSaveCompletionDialog(
                    parent=self,
                    title="엑셀 내보내기 완료",
                    message="엑셀 파일이 성공적으로 저장되었습니다.",
                    file_path=file_path
                )
                
                # 엑셀 내보내기 버튼 근처에 위치 설정
                if hasattr(self, 'export_button'):
                    success_dialog.position_near_widget(self.export_button)
                    
                success_dialog.exec()
                
                self.accept()
                
        except Exception as e:
            # 오류 메시지
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            error_dialog = ModernConfirmDialog(
                self,
                "내보내기 실패",
                f"엑셀 파일 생성 중 오류가 발생했습니다.\n\n오류: {str(e)}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            error_dialog.exec()
            
    def create_excel_file(self, file_path: str):
        """엑셀 파일 생성 (excel_export 모듈 사용)"""
        from .excel_export import powerlink_excel_exporter
        
        # 현재 키워드 데이터 가져오기
        keywords_data = keyword_database.keywords
        
        # 엑셀 익스포터를 사용하여 파일 생성
        powerlink_excel_exporter.export_to_excel(
            keywords_data=keywords_data,
            file_path=file_path,
            session_name=self.session_name
        )


def safe_format_number(value, format_type="int", suffix=""):
    """안전한 숫자 포맷팅 (원본과 동일)"""
    if value is None or value == "":
        return "N/A", 0
    
    if value == "-":
        return "-", 0
        
    try:
        if format_type == "int":
            num_value = int(float(value))
            formatted = f"{num_value:,}{suffix}"
            return formatted, num_value
        elif format_type == "float1":
            num_value = float(value)
            formatted = f"{num_value:.1f}{suffix}"
            return formatted, num_value
        elif format_type == "float2":
            num_value = float(value)
            formatted = f"{num_value:.2f}{suffix}"
            return formatted, num_value
        else:
            return str(value) + suffix, float(value) if str(value).replace('.', '').isdigit() else 0
    except (ValueError, TypeError):
        return str(value) + suffix, 0





class PowerLinkResultsWidget(QWidget):
    """파워링크 분석 결과 위젯 (우측 패널)"""
    
    # 시그널 정의
    save_button_state_changed = Signal(bool)  # 저장 버튼 상태 변경
    clear_button_state_changed = Signal(bool)  # 클리어 버튼 상태 변경
    keyword_added = Signal(str)  # 키워드 추가됨
    keyword_updated = Signal(str, object)  # 키워드 데이터 업데이트됨
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keywords_data = {}  # 키워드 데이터 참조
        
        self.setup_ui()
        self.setup_connections()
        
        # 초기 히스토리 로드
        try:
            self.refresh_history_list()
        except Exception as e:
            logger.error(f"초기 히스토리 로드 실패: {e}")
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_card']};
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
                color: white;
            }}
        """)
        
        # 모바일 탭
        mobile_tab = self.create_mobile_tab()
        self.tab_widget.addTab(mobile_tab, "📱 모바일 분석")
        
        # PC 탭  
        pc_tab = self.create_pc_tab()
        self.tab_widget.addTab(pc_tab, "💻 PC 분석")
        
        # 이전 기록 탭
        history_tab = self.create_history_tab()
        self.tab_widget.addTab(history_tab, "📚 이전 기록")
        
        layout.addWidget(self.tab_widget)
        
        # 분석 관리 버튼들
        button_layout = QHBoxLayout()
        
        # 전체 클리어 버튼
        self.clear_button = ModernButton("🗑 전체 클리어", "warning")
        self.clear_button.setEnabled(False)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # 현재 분석 저장 버튼
        self.save_analysis_button = ModernButton("💾 현재 분석 저장", "success")
        self.save_analysis_button.setEnabled(False)
        button_layout.addWidget(self.save_analysis_button)
        
        layout.addLayout(button_layout)
        
    def create_mobile_tab(self) -> QWidget:
        """모바일 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # 선택 삭제 버튼
        button_layout = QHBoxLayout()
        self.mobile_delete_button = ModernButton("🗑️ 선택 삭제", "danger")
        self.mobile_delete_button.setEnabled(False)
        button_layout.addWidget(self.mobile_delete_button)
        button_layout.addStretch()
        
        # 모바일 테이블
        self.mobile_table = self.create_analysis_table()
        
        layout.addLayout(button_layout)
        layout.addWidget(self.mobile_table)
        
        return tab
        
    def create_pc_tab(self) -> QWidget:
        """PC 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # 선택 삭제 버튼
        button_layout = QHBoxLayout()
        self.pc_delete_button = ModernButton("🗑️ 선택 삭제", "danger")
        self.pc_delete_button.setEnabled(False)
        button_layout.addWidget(self.pc_delete_button)
        button_layout.addStretch()
        
        # PC 테이블
        self.pc_table = self.create_analysis_table()
        
        layout.addLayout(button_layout)
        layout.addWidget(self.pc_table)
        
        return tab
    
    def create_history_tab(self) -> QWidget:
        """이전 기록 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 상단 버튼들
        button_layout = QHBoxLayout()
        
        self.delete_history_button = ModernButton("🗑️ 선택 삭제", "danger")
        self.delete_history_button.setEnabled(False)
        self.view_history_button = ModernButton("👀 보기", "primary")
        self.view_history_button.setEnabled(False)
        self.export_selected_history_button = ModernButton("💾 선택 저장", "success")
        self.export_selected_history_button.setEnabled(False)
        
        button_layout.addWidget(self.delete_history_button)
        button_layout.addWidget(self.export_selected_history_button)
        button_layout.addStretch()
        button_layout.addWidget(self.view_history_button)
        
        layout.addLayout(button_layout)
        
        # 이전 기록 테이블
        self.history_table = QTableWidget()
        headers = ["", "세션명", "생성일시", "키워드 수"]
        self.history_table.setColumnCount(len(headers))
        self.history_table.setHorizontalHeaderLabels(headers)
        
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 13px;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                alternate-background-color: {ModernStyle.COLORS['bg_secondary']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 8px;
                border: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        
        # 행 높이 늘리기 (40px)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        
        # 컬럼 설정
        header = self.history_table.horizontalHeader()
        header.resizeSection(0, 50)   # 체크박스 컬럼
        header.resizeSection(1, 300)  # 세션명 컬럼  
        header.resizeSection(2, 150)  # 생성일시 컬럼
        header.resizeSection(3, 100)  # 키워드 수 컬럼
        header.setStretchLastSection(True)
        
        layout.addWidget(self.history_table)
        
        # 히스토리 테이블 헤더 체크박스 설정
        self.setup_history_header_checkbox()
        
        return tab
    
    def create_analysis_table(self) -> QTableWidget:
        """분석 결과 테이블 생성 (카페 추출기와 동일한 스타일 적용)"""
        table = QTableWidget()
        
        # 헤더 설정 (첫 번째 컬럼은 빈 문자열로 설정 - 체크박스용)
        headers = [
            "", "키워드", "월검색량", "클릭수", "클릭률", 
            "1p노출위치", "1등광고비", "최소노출가격", "추천순위", "상세"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # 카페 추출기와 동일한 테이블 스타일 적용
        table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                alternate-background-color: {ModernStyle.COLORS['bg_input']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 10px 8px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
                min-height: 20px;
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: none;
                border-right: 1px solid {ModernStyle.COLORS['border']};
                border-bottom: 2px solid {ModernStyle.COLORS['border']};
                padding: 8px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        
        # 테이블 설정 (카페 추출기와 동일)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 각 데이터 행의 높이를 체크박스에 맞게 적절히 조정
        table.verticalHeader().setDefaultSectionSize(40)  # 행 높이 40px
        
        # 행 헤더 숨기기 (체크박스가 있어서 불필요)
        table.verticalHeader().setVisible(False)
        
        # 헤더 설정
        header = table.horizontalHeader()
        
        # 첫 번째 컬럼의 크기를 고정하고 위젯을 배치할 공간 확보
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 80)   # 체크박스 컬럼 너비
        
        # 나머지 컬럼 크기는 Interactive로 설정
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        
        # 컬럼 너비 설정
        header.resizeSection(1, 156)  # 키워드 (120 × 1.3)
        header.resizeSection(2, 80)   # 월검색량
        header.resizeSection(3, 70)   # 클릭수
        header.resizeSection(4, 70)   # 클릭률
        header.resizeSection(5, 90)   # 1p노출위치
        header.resizeSection(6, 90)   # 1등광고비
        header.resizeSection(7, 110)  # 최소노출가격
        header.resizeSection(8, 80)   # 추천순위
        header.resizeSection(9, 60)   # 상세 (60px로 조정)
        
        # 정렬 활성화
        table.setSortingEnabled(True)
        
        return table
    
    def setup_connections(self):
        """시그널 연결"""
        # 관리 버튼
        self.clear_button.clicked.connect(self.clear_all_analysis)
        self.save_analysis_button.clicked.connect(self.save_current_analysis)
        
        # 삭제 버튼
        self.mobile_delete_button.clicked.connect(lambda: self.delete_selected_keywords('mobile'))
        self.pc_delete_button.clicked.connect(lambda: self.delete_selected_keywords('pc'))
        
        # 히스토리 버튼
        self.delete_history_button.clicked.connect(self.delete_selected_history)
        self.view_history_button.clicked.connect(self.view_selected_history)
        self.export_selected_history_button.clicked.connect(self.export_selected_history)
        
        # 헤더 체크박스 설정
        self.setup_mobile_header_checkbox()
        self.setup_pc_header_checkbox()
        
        # 탭 변경 시그널 연결 (이전기록 탭에서 저장 버튼 비활성화)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 헤더 체크박스 위치 조정을 위한 타이머 설정
        QTimer.singleShot(100, self.position_all_header_checkboxes)
    
    def set_keywords_data(self, keywords_data):
        """키워드 데이터 설정"""
        self.keywords_data = keywords_data
        self.update_all_tables()
        self.update_button_states()
    
    def update_all_tables(self):
        """모든 테이블 업데이트"""
        self.update_mobile_table()
        self.update_pc_table()
        
    def update_mobile_table(self):
        """모바일 테이블 업데이트"""
        mobile_sorted = keyword_database.calculate_mobile_rankings()
        
        self.mobile_table.setRowCount(len(mobile_sorted))
        
        for row, result in enumerate(mobile_sorted):
            # 체크박스 (원본과 동일한 빨간색 스타일)
            checkbox = QCheckBox()
            checkbox.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: white;
                    border: 2px solid {ModernStyle.COLORS['border']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {ModernStyle.COLORS['danger']};
                    border: 2px solid {ModernStyle.COLORS['danger']};
                    border-radius: 4px;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEwLjI4IDEuMjhMMy44NSA3LjcxTDEuNzIgNS41OCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
                }}
                QCheckBox::indicator:hover:unchecked {{
                    border-color: {ModernStyle.COLORS['danger']};
                }}
            """)
            checkbox.stateChanged.connect(self.update_delete_button_state)  # 시그널 연결 추가
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.mobile_table.setCellWidget(row, 0, checkbox_widget)
            
            # 키워드
            self.mobile_table.setItem(row, 1, QTableWidgetItem(result.keyword))
            
            # 월검색량 (Mobile)
            if result.mobile_search_volume >= 0:
                self.mobile_table.setItem(row, 2, SortableTableWidgetItem(
                    f"{result.mobile_search_volume:,}", result.mobile_search_volume))
            else:
                self.mobile_table.setItem(row, 2, SortableTableWidgetItem("-", 0))
            
            # 모바일 데이터
            self.mobile_table.setItem(row, 3, SortableTableWidgetItem(
                f"{result.mobile_clicks:.1f}", result.mobile_clicks))
            self.mobile_table.setItem(row, 4, SortableTableWidgetItem(
                f"{result.mobile_ctr:.2f}%", result.mobile_ctr))
            self.mobile_table.setItem(row, 5, SortableTableWidgetItem(
                f"{result.mobile_first_page_positions}위까지", result.mobile_first_page_positions))
            self.mobile_table.setItem(row, 6, SortableTableWidgetItem(
                f"{result.mobile_first_position_bid:,}원", result.mobile_first_position_bid))
            self.mobile_table.setItem(row, 7, SortableTableWidgetItem(
                f"{result.mobile_min_exposure_bid:,}원", result.mobile_min_exposure_bid))
            
            # 추천순위 ("위" 접미사 포함)
            if result.mobile_recommendation_rank > 0:
                rank_text = f"{result.mobile_recommendation_rank}위"
            else:
                rank_text = "-"
            self.mobile_table.setItem(row, 8, SortableTableWidgetItem(
                rank_text, result.mobile_recommendation_rank))
            
            # 상세 버튼 (원본과 동일한 초록색 스타일)
            detail_button = QPushButton("상세")
            detail_button.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0px;
                    font-weight: 600;
                    font-size: 13px;
                    margin: 0px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
            """)
            detail_button.clicked.connect(lambda checked, r=result: self.show_bid_details(result.keyword, r, 'mobile'))
            self.mobile_table.setCellWidget(row, 9, detail_button)
            
    def update_pc_table(self):
        """PC 테이블 업데이트"""
        pc_sorted = keyword_database.calculate_pc_rankings()
        
        self.pc_table.setRowCount(len(pc_sorted))
        
        for row, result in enumerate(pc_sorted):
            # 체크박스 (원본과 동일한 빨간색 스타일)
            checkbox = QCheckBox()
            checkbox.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox::indicator:unchecked {{
                    background-color: white;
                    border: 2px solid {ModernStyle.COLORS['border']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {ModernStyle.COLORS['danger']};
                    border: 2px solid {ModernStyle.COLORS['danger']};
                    border-radius: 4px;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEwLjI4IDEuMjhMMy44NSA3LjcxTDEuNzIgNS41OCIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
                }}
                QCheckBox::indicator:hover:unchecked {{
                    border-color: {ModernStyle.COLORS['danger']};
                }}
            """)
            checkbox.stateChanged.connect(self.update_delete_button_state)  # 시그널 연결 추가
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.pc_table.setCellWidget(row, 0, checkbox_widget)
            
            # 키워드
            self.pc_table.setItem(row, 1, QTableWidgetItem(result.keyword))
            
            # PC 월검색량
            if result.pc_search_volume >= 0:
                self.pc_table.setItem(row, 2, SortableTableWidgetItem(
                    f"{result.pc_search_volume:,}", result.pc_search_volume))
            else:
                self.pc_table.setItem(row, 2, SortableTableWidgetItem("-", 0))
            
            # PC 데이터
            self.pc_table.setItem(row, 3, SortableTableWidgetItem(
                f"{result.pc_clicks:.1f}", result.pc_clicks))
            self.pc_table.setItem(row, 4, SortableTableWidgetItem(
                f"{result.pc_ctr:.2f}%", result.pc_ctr))
            self.pc_table.setItem(row, 5, SortableTableWidgetItem(
                f"{result.pc_first_page_positions}위까지", result.pc_first_page_positions))
            self.pc_table.setItem(row, 6, SortableTableWidgetItem(
                f"{result.pc_first_position_bid:,}원", result.pc_first_position_bid))
            self.pc_table.setItem(row, 7, SortableTableWidgetItem(
                f"{result.pc_min_exposure_bid:,}원", result.pc_min_exposure_bid))
            
            # 추천순위 ("위" 접미사 포함)
            if result.pc_recommendation_rank > 0:
                rank_text = f"{result.pc_recommendation_rank}위"
            else:
                rank_text = "-"
            self.pc_table.setItem(row, 8, SortableTableWidgetItem(
                rank_text, result.pc_recommendation_rank))
            
            # 상세 버튼 (원본과 동일한 초록색 스타일)
            detail_button = QPushButton("상세")
            detail_button.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0px;
                    font-weight: 600;
                    font-size: 13px;
                    margin: 0px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
            """)
            detail_button.clicked.connect(lambda checked, r=result: self.show_bid_details(result.keyword, r, 'pc'))
            self.pc_table.setCellWidget(row, 9, detail_button)
    
    def update_keyword_data(self, keyword: str, result):
        """키워드 데이터 실시간 업데이트"""
        if keyword in self.keywords_data:
            # 기존 데이터 업데이트
            self.keywords_data[keyword] = result
            
            # 테이블에서 해당 키워드 행 찾아서 업데이트
            self.update_keyword_row_in_table(self.mobile_table, keyword, result, 'mobile')
            self.update_keyword_row_in_table(self.pc_table, keyword, result, 'pc')
            
            # 저장 버튼 상태 업데이트
            self.update_save_button_state()
    
    def update_keyword_row_in_table(self, table: QTableWidget, keyword: str, result, device_type: str):
        """특정 키워드의 테이블 행 업데이트"""
        for row in range(table.rowCount()):
            keyword_item = table.item(row, 1)
            if keyword_item and keyword_item.text() == keyword:
                # 해당 행의 데이터 업데이트
                self.update_table_row_data(table, row, result, device_type)
                break

    def add_keyword_to_table(self, table: QTableWidget, result, device_type: str, update_ui: bool = True):
        """테이블에 키워드 분석 결과 추가 (원본과 동일)"""
        row = table.rowCount()
        table.insertRow(row)
        
        # 0. 체크박스 (히스토리 테이블과 동일한 스타일)
        checkbox = QCheckBox()
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 0px;
                margin: 0px;
                padding: 0px;
                border: none;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: white;
                margin: 0px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {ModernStyle.COLORS['danger']};
                border-color: {ModernStyle.COLORS['danger']};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
            QCheckBox::indicator:hover {{
                border-color: #999999;
                background-color: #f8f9fa;
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #dc2626;
                border-color: #dc2626;
            }}
        """)
        checkbox.stateChanged.connect(lambda: self.update_delete_button_state())
        
        # 체크박스를 중앙에 배치하기 위한 컨테이너 위젯
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.addWidget(checkbox)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        
        table.setCellWidget(row, 0, checkbox_widget)
        
        # 1. 키워드
        table.setItem(row, 1, QTableWidgetItem(result.keyword))
        
        # 2. 월검색량 (Mobile)
        if hasattr(result, 'mobile_search_volume') and result.mobile_search_volume is not None and result.mobile_search_volume >= 0:
            volume_text, volume_value = safe_format_number(result.mobile_search_volume, "int")
            search_volume_item = SortableTableWidgetItem(volume_text, volume_value)
        else:
            search_volume_item = SortableTableWidgetItem("-", 0)
        table.setItem(row, 2, search_volume_item)
        
        # 디바이스별 데이터 설정
        if device_type == 'mobile':
            # 3. 클릭수
            if hasattr(result, 'mobile_clicks') and result.mobile_clicks is not None:
                clicks_text, clicks_value = safe_format_number(result.mobile_clicks, "float1")
                clicks_item = SortableTableWidgetItem(clicks_text, clicks_value)
            else:
                clicks_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 3, clicks_item)
            
            # 4. 클릭률
            if hasattr(result, 'mobile_ctr') and result.mobile_ctr is not None:
                ctr_text, ctr_value = safe_format_number(result.mobile_ctr, "float2", "%")
                ctr_item = SortableTableWidgetItem(ctr_text, ctr_value)
            else:
                ctr_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 4, ctr_item)
            
            # 5. 1p노출위치
            if hasattr(result, 'mobile_first_page_positions') and result.mobile_first_page_positions is not None:
                position_text, position_value = safe_format_number(result.mobile_first_page_positions, "int", "위까지")
                position_item = SortableTableWidgetItem(position_text, position_value)
            else:
                position_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 5, position_item)
            
            # 6. 1등광고비 (올바른 데이터 할당)
            if hasattr(result, 'mobile_first_position_bid') and result.mobile_first_position_bid is not None:
                first_bid_text, first_bid_value = safe_format_number(result.mobile_first_position_bid, "int", "원")
                first_bid_item = SortableTableWidgetItem(first_bid_text, first_bid_value)
            else:
                first_bid_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 6, first_bid_item)
            
            # 7. 최소노출가격 (올바른 데이터 할당)
            if hasattr(result, 'mobile_min_exposure_bid') and result.mobile_min_exposure_bid is not None:
                min_bid_text, min_bid_value = safe_format_number(result.mobile_min_exposure_bid, "int", "원")
                min_bid_item = SortableTableWidgetItem(min_bid_text, min_bid_value)
            else:
                min_bid_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 7, min_bid_item)
            
            # 8. 추천순위 (올바른 데이터 할당, "위" 접미사 포함)
            mobile_rank = getattr(result, 'mobile_recommendation_rank', 0) if hasattr(result, 'mobile_recommendation_rank') else 0
            if mobile_rank > 0:
                rank_item = SortableTableWidgetItem(f"{mobile_rank}위", mobile_rank)
            else:
                rank_item = SortableTableWidgetItem("-", 0)  # 초기값 "-"
            table.setItem(row, 8, rank_item)
        else:  # PC
            # 3. 클릭수
            if hasattr(result, 'pc_clicks') and result.pc_clicks is not None:
                clicks_text, clicks_value = safe_format_number(result.pc_clicks, "float1")
                clicks_item = SortableTableWidgetItem(clicks_text, clicks_value)
            else:
                clicks_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 3, clicks_item)
            
            # 4. 클릭률
            if hasattr(result, 'pc_ctr') and result.pc_ctr is not None:
                ctr_text, ctr_value = safe_format_number(result.pc_ctr, "float2", "%")
                ctr_item = SortableTableWidgetItem(ctr_text, ctr_value)
            else:
                ctr_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 4, ctr_item)
            
            # 5. 1p노출위치
            if hasattr(result, 'pc_first_page_positions') and result.pc_first_page_positions is not None:
                position_text, position_value = safe_format_number(result.pc_first_page_positions, "int", "위까지")
                position_item = SortableTableWidgetItem(position_text, position_value)
            else:
                position_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 5, position_item)
            
            # 6. 1등광고비 (올바른 데이터 할당)
            if hasattr(result, 'pc_first_position_bid') and result.pc_first_position_bid is not None:
                first_bid_text, first_bid_value = safe_format_number(result.pc_first_position_bid, "int", "원")
                first_bid_item = SortableTableWidgetItem(first_bid_text, first_bid_value)
            else:
                first_bid_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 6, first_bid_item)
            
            # 7. 최소노출가격 (올바른 데이터 할당)
            if hasattr(result, 'pc_min_exposure_bid') and result.pc_min_exposure_bid is not None:
                min_bid_text, min_bid_value = safe_format_number(result.pc_min_exposure_bid, "int", "원")
                min_bid_item = SortableTableWidgetItem(min_bid_text, min_bid_value)
            else:
                min_bid_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 7, min_bid_item)
            
            # 8. 추천순위 (올바른 데이터 할당, "위" 접미사 포함)
            pc_rank = getattr(result, 'pc_recommendation_rank', 0) if hasattr(result, 'pc_recommendation_rank') else 0
            if pc_rank > 0:
                rank_item = SortableTableWidgetItem(f"{pc_rank}위", pc_rank)
            else:
                rank_item = SortableTableWidgetItem("-", 0)  # 초기값 "-"
            table.setItem(row, 8, rank_item)
        
        # 9. 상세보기 버튼 (셀 전체를 채우는 초록색 버튼)
        detail_button = QPushButton("상세")
        detail_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 0px;
                font-weight: 600;
                font-size: 13px;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        detail_button.clicked.connect(lambda: self.show_bid_details(result.keyword, result, device_type))
        
        # 버튼을 셀 전체에 배치 (여백 제거)
        table.setCellWidget(row, 9, detail_button)
        
        # UI 업데이트 (rebuild 중에는 스킵)
        if update_ui:
            # 버튼 상태 업데이트 (새 데이터 추가되었으므로 클리어 버튼 활성화)
            self.update_delete_button_state()
            
            # 상태 표시 업데이트 (키워드 개수 증가 반영)
            self.update_status_display()

    def show_bid_details(self, keyword: str, result, device_type: str):
        """입찰가 상세 정보 표시"""
        dialog = BidDetailsDialog(keyword, result, device_type, self)
        dialog.exec()
    
    def update_delete_button_state(self):
        """삭제 버튼 상태 업데이트 및 헤더 체크박스 상태 업데이트"""
        # 모바일 테이블 체크 상태 확인
        mobile_has_checked = False
        mobile_all_checked = True
        mobile_total_rows = self.mobile_table.rowCount()
        mobile_checked_count = 0
        
        for row in range(mobile_total_rows):
            checkbox_widget = self.mobile_table.cellWidget(row, 0)
            if checkbox_widget:
                # 컨테이너 내부의 QCheckBox 찾기
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    mobile_has_checked = True
                    mobile_checked_count += 1
                else:
                    mobile_all_checked = False
            else:
                mobile_all_checked = False
                
        # PC 테이블 체크 상태 확인  
        pc_has_checked = False
        pc_all_checked = True
        pc_total_rows = self.pc_table.rowCount()
        pc_checked_count = 0
        
        for row in range(pc_total_rows):
            checkbox_widget = self.pc_table.cellWidget(row, 0)
            if checkbox_widget:
                # 컨테이너 내부의 QCheckBox 찾기
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    pc_has_checked = True
                    pc_checked_count += 1
                else:
                    pc_all_checked = False
            else:
                pc_all_checked = False
                
        # 버튼 상태 업데이트 (체크된 개수 표시)
        if mobile_has_checked:
            self.mobile_delete_button.setText(f"🗑️ 선택 삭제({mobile_checked_count})")
            self.mobile_delete_button.setEnabled(True)
        else:
            self.mobile_delete_button.setText("🗑️ 선택 삭제")
            self.mobile_delete_button.setEnabled(False)
            
        if pc_has_checked:
            self.pc_delete_button.setText(f"🗑️ 선택 삭제({pc_checked_count})")
            self.pc_delete_button.setEnabled(True)
        else:
            self.pc_delete_button.setText("🗑️ 선택 삭제")
            self.pc_delete_button.setEnabled(False)
        
        # 클리어 버튼 상태 업데이트 (테이블에 데이터가 있으면 활성화)
        has_data = mobile_total_rows > 0 or pc_total_rows > 0
        self.clear_button.setEnabled(has_data)
        
        # 헤더 체크박스 상태 업데이트 (시그널 차단으로 무한 루프 방지)
        if hasattr(self, 'mobile_header_checkbox') and self.mobile_header_checkbox:
            self.mobile_header_checkbox.blockSignals(True)
            if mobile_total_rows == 0:
                self.mobile_header_checkbox.setCheckState(Qt.Unchecked)
            elif mobile_checked_count == mobile_total_rows:
                self.mobile_header_checkbox.setCheckState(Qt.Checked)
            elif mobile_checked_count > 0:
                self.mobile_header_checkbox.setCheckState(Qt.PartiallyChecked)
            else:
                self.mobile_header_checkbox.setCheckState(Qt.Unchecked)
            self.mobile_header_checkbox.blockSignals(False)
        
        if hasattr(self, 'pc_header_checkbox') and self.pc_header_checkbox:
            self.pc_header_checkbox.blockSignals(True)
            if pc_total_rows == 0:
                self.pc_header_checkbox.setCheckState(Qt.Unchecked)
            elif pc_checked_count == pc_total_rows:
                self.pc_header_checkbox.setCheckState(Qt.Checked)
            elif pc_checked_count > 0:
                self.pc_header_checkbox.setCheckState(Qt.PartiallyChecked)
            else:
                self.pc_header_checkbox.setCheckState(Qt.Unchecked)
            self.pc_header_checkbox.blockSignals(False)

    def update_status_display(self):
        """상태 표시 업데이트"""
        # 키워드 개수 업데이트 로직 (필요시 구현)
        pass

    def delete_selected_keywords(self, table_type):
        """선택된 키워드 삭제"""
        table = self.mobile_table if table_type == 'mobile' else self.pc_table
        
        # 선택된 행 찾기
        selected_keywords = []
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    keyword_item = table.item(row, 1)
                    if keyword_item:
                        selected_keywords.append(keyword_item.text())
        
        if not selected_keywords:
            QMessageBox.information(self, "알림", "삭제할 키워드를 선택해주세요.")
            return
        
        reply = QMessageBox.question(
            self, "확인", 
            f"{len(selected_keywords)}개 키워드를 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 키워드 삭제
            for keyword in selected_keywords:
                if keyword in self.keywords_data:
                    del self.keywords_data[keyword]
                keyword_database.remove_keyword(keyword)
            
            # 순위 재계산
            keyword_database.recalculate_all_rankings()
            
            # 테이블 업데이트
            self.update_all_tables()
            self.update_button_states()
            
            log_manager.add_log(f"{len(selected_keywords)}개 키워드 삭제 완료", "success")
    
    def clear_all_data(self):
        """모든 데이터 지우기"""
        if not self.keywords_data:
            return
            
        # 모던 다이얼로그로 확인 (클리어 버튼 근처에 표시)
        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
        dialog = ModernConfirmDialog(
            self, 
            "전체 삭제 확인", 
            "모든 분석 데이터를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.", 
            confirm_text="삭제", 
            cancel_text="취소", 
            icon="🗑️",
            position_near_widget=self.clear_button
        )
        
        if dialog.exec() == ModernConfirmDialog.Accepted:
            self.keywords_data.clear()
            keyword_database.clear()
            self.mobile_table.setRowCount(0)
            self.pc_table.setRowCount(0)
            self.update_button_states()
            log_manager.add_log("PowerLink 분석 결과 전체 삭제", "success")
    
    
    def refresh_history_list(self):
        """히스토리 목록 새로고침"""
        try:
            db = get_db()
            sessions = db.list_powerlink_sessions()
            
            self.history_table.setRowCount(len(sessions))
            
            for row, session in enumerate(sessions):
                # 체크박스 (원본과 동일한 빨간색 스타일)
                checkbox = QCheckBox()
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        spacing: 0px;
                        margin: 0px;
                        padding: 0px;
                        border: none;
                        background-color: transparent;
                    }}
                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                        border: 2px solid #ccc;
                        border-radius: 3px;
                        background-color: white;
                        margin: 0px;
                    }}
                    QCheckBox::indicator:checked {{
                        background-color: {ModernStyle.COLORS['danger']};
                        border-color: {ModernStyle.COLORS['danger']};
                        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                    }}
                    QCheckBox::indicator:hover {{
                        border-color: #999999;
                        background-color: #f8f9fa;
                    }}
                    QCheckBox::indicator:checked:hover {{
                        background-color: #dc2626;
                        border-color: #dc2626;
                    }}
                """)
                checkbox.stateChanged.connect(self.update_history_button_states)
                
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.history_table.setCellWidget(row, 0, checkbox_widget)
                
                # 세션명 (세션 ID도 함께 저장)
                session_name_item = QTableWidgetItem(session['session_name'])
                session_name_item.setData(Qt.UserRole, session['id'])
                self.history_table.setItem(row, 1, session_name_item)
                
                # 생성일시 (한국시간으로 변환)
                created_at = session['created_at']
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                # UTC에서 한국시간(KST, UTC+9)으로 변환
                from datetime import timedelta
                kst_time = created_at + timedelta(hours=9)
                
                self.history_table.setItem(row, 2, QTableWidgetItem(
                    kst_time.strftime('%Y-%m-%d %H:%M:%S')))
                
                # 키워드 수
                self.history_table.setItem(row, 3, QTableWidgetItem(str(session['keyword_count'])))
                
            log_manager.add_log(f"PowerLink 히스토리 새로고침: {len(sessions)}개 세션", "info")
            
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 새로고침 실패: {e}", "error")
    
    def delete_selected_history(self):
        """선택된 히스토리 삭제"""
        try:
            # 선택된 세션 ID 목록 가져오기
            selected_sessions = []
            for row in range(self.history_table.rowCount()):
                container_widget = self.history_table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        session_name = self.history_table.item(row, 1).text()
                        selected_sessions.append((row, session_name))
            
            if not selected_sessions:
                return
            
            # 모던 다이얼로그로 확인 (선택삭제 버튼 근처에 표시)
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self, 
                "히스토리 삭제 확인", 
                f"선택된 {len(selected_sessions)}개의 분석 기록을 삭제하시겠습니까?\n\n"
                f"이 작업은 되돌릴 수 없습니다.", 
                confirm_text="삭제", 
                cancel_text="취소", 
                icon="🗑️",
                position_near_widget=self.delete_history_button
            )
            
            if dialog.exec() == ModernConfirmDialog.Accepted:
                # DB에서 삭제 (구현 필요시)
                # db = get_db()
                # for _, session_name in selected_sessions:
                #     db.delete_powerlink_session(session_name)
                
                # 히스토리 새로고침
                self.refresh_history_list()
                log_manager.add_log(f"PowerLink 히스토리 {len(selected_sessions)}개 삭제", "success")
                
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 삭제 실패: {e}", "error")
    
    def view_selected_history(self):
        """선택된 히스토리 보기 - 모바일/PC 분석 탭에 다시 로드 (다이얼로그 제거)"""
        try:
            # 선택된 하나의 세션 찾기
            selected_session_id = None
            selected_session_name = None
            for row in range(self.history_table.rowCount()):
                container_widget = self.history_table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        # 세션 ID 가져오기 (세션명 아이템에서)
                        session_name_item = self.history_table.item(row, 1)
                        selected_session_id = session_name_item.data(Qt.UserRole)
                        selected_session_name = session_name_item.text()
                        break
            
            if not selected_session_id:
                return
            
            # DB에서 세션 키워드 데이터 로드
            db = get_db()
            session_keywords_data = db.get_powerlink_session_keywords(selected_session_id)
            if not session_keywords_data:
                log_manager.add_log(f"PowerLink 히스토리 로드 실패: 키워드 데이터 없음 - {selected_session_name}", "error")
                return
            
            # 키워드 데이터를 KeywordAnalysisResult 객체로 변환
            from .models import KeywordAnalysisResult, BidPosition
            loaded_keywords_data = {}
            
            for keyword, data in session_keywords_data.items():
                try:
                    # BidPosition 객체들 복원
                    pc_bid_positions = []
                    if data.get('pc_bid_positions'):
                        for bid_data in data['pc_bid_positions']:
                            pc_bid_positions.append(BidPosition(
                                position=bid_data['position'],
                                bid_price=bid_data['bid_price']
                            ))
                    
                    mobile_bid_positions = []
                    if data.get('mobile_bid_positions'):
                        for bid_data in data['mobile_bid_positions']:
                            mobile_bid_positions.append(BidPosition(
                                position=bid_data['position'],
                                bid_price=bid_data['bid_price']
                            ))
                    
                    # KeywordAnalysisResult 객체 복원
                    result = KeywordAnalysisResult(
                        keyword=keyword,
                        pc_search_volume=data.get('pc_search_volume', 0),
                        mobile_search_volume=data.get('mobile_search_volume', 0),
                        pc_clicks=data.get('pc_clicks', 0),
                        pc_ctr=data.get('pc_ctr', 0),
                        pc_first_page_positions=data.get('pc_first_page_positions', 0),
                        pc_first_position_bid=data.get('pc_first_position_bid', 0),
                        pc_min_exposure_bid=data.get('pc_min_exposure_bid', 0),
                        pc_bid_positions=pc_bid_positions,
                        mobile_clicks=data.get('mobile_clicks', 0),
                        mobile_ctr=data.get('mobile_ctr', 0),
                        mobile_first_page_positions=data.get('mobile_first_page_positions', 0),
                        mobile_first_position_bid=data.get('mobile_first_position_bid', 0),
                        mobile_min_exposure_bid=data.get('mobile_min_exposure_bid', 0),
                        mobile_bid_positions=mobile_bid_positions,
                        analyzed_at=datetime.fromisoformat(data.get('analyzed_at', datetime.now().isoformat()))
                    )
                    
                    loaded_keywords_data[keyword] = result
                    keyword_database.add_keyword(result)
                    
                except Exception as e:
                    log_manager.add_log(f"PowerLink 키워드 복원 실패: {keyword}: {e}", "error")
                    continue
            
            if loaded_keywords_data:
                # 기존 데이터 초기화
                self.keywords_data.clear()
                keyword_database.clear()
                
                # 새 데이터 설정
                self.keywords_data = loaded_keywords_data
                
                # keyword_database에도 데이터 추가
                for keyword, result in loaded_keywords_data.items():
                    keyword_database.add_keyword(result)
                
                # 순위 재계산
                keyword_database.recalculate_all_rankings()
                
                # 테이블 갱신 (직접 호출로 확실히 업데이트)
                self.update_all_tables()
                self.update_save_button_state()
                
                # 모바일 분석 탭으로 자동 이동
                self.tab_widget.setCurrentIndex(0)  # 모바일 분석 탭
                
                log_manager.add_log(f"PowerLink 히스토리 로드 완료: {selected_session_name} ({len(loaded_keywords_data)}개 키워드)", "info")
            else:
                log_manager.add_log(f"PowerLink 히스토리 로드 실패: 유효한 키워드 없음 - {selected_session_name}", "error")
                
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 보기 실패: {e}", "error")
    
    def export_selected_history(self):
        """선택된 히스토리 엑셀 내보내기"""
        try:
            # 선택된 세션 정보 가져오기
            selected_sessions = []
            for row in range(self.history_table.rowCount()):
                container_widget = self.history_table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        # 세션 ID 가져오기 (세션명 아이템에서)
                        session_name_item = self.history_table.item(row, 1)
                        session_id = session_name_item.data(Qt.UserRole)
                        session_name = session_name_item.text()
                        created_at = self.history_table.item(row, 2).text()
                        selected_sessions.append({
                            'id': session_id,
                            'name': session_name,
                            'created_at': created_at
                        })
            
            if not selected_sessions:
                return
            
            from src.foundation.db import get_db
            from datetime import datetime
            import os
            
            db = get_db()
            
            # 선택된 세션이 1개인 경우: 일반 엑셀내보내기처럼 파일 다이얼로그
            if len(selected_sessions) == 1:
                session = selected_sessions[0]
                
                # 세션 키워드 데이터 가져오기
                keywords_data = db.get_powerlink_session_keywords(session['id'])
                
                if not keywords_data:
                    from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                    dialog = ModernConfirmDialog(
                        self,
                        "데이터 없음",
                        "선택된 기록에 키워드 데이터가 없습니다.",
                        confirm_text="확인",
                        cancel_text=None,
                        icon="⚠️"
                    )
                    dialog.exec()
                    return
                
                # 파일 저장 다이얼로그 (원본 세션 시간으로 기본 파일명 설정)
                session_time = datetime.fromisoformat(session['created_at'])
                time_str = session_time.strftime('%Y%m%d_%H%M%S')
                default_filename = f"파워링크광고비분석_{time_str}.xlsx"
                
                from PySide6.QtWidgets import QFileDialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "엑셀 파일 저장",
                    default_filename,
                    "Excel files (*.xlsx);;All files (*.*)"
                )
                
                if file_path:
                    try:
                        # 엑셀 파일 생성
                        from .excel_export import powerlink_excel_exporter
                        powerlink_excel_exporter.export_to_excel(
                            keywords_data=keywords_data,
                            file_path=file_path,
                            session_name=session['name']
                        )
                        
                        # 저장 완료 다이얼로그
                        from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
                        success_dialog = ModernSaveCompletionDialog(
                            parent=self,
                            title="저장 완료",
                            message="엑셀 파일이 성공적으로 저장되었습니다.",
                            file_path=file_path
                        )
                        
                        # 선택저장 버튼 근처에 위치 설정
                        if hasattr(self, 'export_selected_history_button'):
                            success_dialog.position_near_widget(self.export_selected_history_button)
                            
                        success_dialog.exec()
                        
                        log_manager.add_log(f"PowerLink 히스토리 단일 파일 저장 완료: {session['name']}", "success")
                        
                    except Exception as e:
                        log_manager.add_log(f"엑셀 파일 저장 실패: {e}", "error")
                        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                        dialog = ModernConfirmDialog(
                            self,
                            "저장 실패",
                            f"엑셀 파일 저장 중 오류가 발생했습니다.\n\n{str(e)}",
                            confirm_text="확인",
                            cancel_text=None,
                            icon="❌"
                        )
                        dialog.exec()
            
            # 선택된 세션이 다중인 경우: 폴더 선택 + 자동 파일명 생성
            else:
                # 폴더 선택 다이얼로그
                from PySide6.QtWidgets import QFileDialog
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "엑셀 파일 저장 폴더 선택",
                    ""
                )
                
                if not folder_path:
                    return
                
                # 각 세션별로 엑셀 파일 생성
                saved_files = []
                
                for session in selected_sessions:
                    try:
                        # 세션 키워드 데이터 가져오기
                        keywords_data = db.get_powerlink_session_keywords(session['id'])
                        
                        if keywords_data:
                            # 파일명 생성 (세션 생성 시간 사용)
                            session_time = datetime.fromisoformat(session['created_at'])
                            time_str = session_time.strftime('%Y%m%d_%H%M%S')
                            filename = f"파워링크광고비분석_{time_str}.xlsx"
                            file_path = os.path.join(folder_path, filename)
                            
                            # 엑셀 파일 생성
                            from .excel_export import powerlink_excel_exporter
                            powerlink_excel_exporter.export_to_excel(
                                keywords_data=keywords_data,
                                file_path=file_path,
                                session_name=session['name']
                            )
                            
                            saved_files.append(file_path)
                            
                    except Exception as e:
                        log_manager.add_log(f"세션 {session['name']} 내보내기 실패: {e}", "error")
                        continue
                
                if saved_files:
                    # 저장 완료 다이얼로그 (폴더 열기 옵션 포함)
                    from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
                    success_dialog = ModernSaveCompletionDialog(
                        parent=self,
                        title="선택저장 완료",
                        message=f"{len(saved_files)}개의 엑셀 파일이 성공적으로 저장되었습니다.",
                        file_path=saved_files[0]  # 첫 번째 파일 경로로 폴더 열기
                    )
                    
                    # 선택저장 버튼 근처에 위치 설정
                    if hasattr(self, 'export_selected_history_button'):
                        success_dialog.position_near_widget(self.export_selected_history_button)
                        
                    success_dialog.exec()
                    
                    log_manager.add_log(f"PowerLink 히스토리 {len(saved_files)}개 파일 저장 완료", "success")
                else:
                    # 실패 메시지
                    from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                    dialog = ModernConfirmDialog(
                        self,
                        "저장 실패",
                        "선택된 기록을 저장하는 중 오류가 발생했습니다.",
                        confirm_text="확인",
                        cancel_text=None,
                        icon="❌"
                    )
                    dialog.exec()
            
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 내보내기 실패: {e}", "error")
    
    def update_button_states(self):
        """버튼 상태 업데이트"""
        has_data = bool(self.keywords_data)
        
        # 테이블에도 데이터가 있는지 확인
        if not has_data:
            if (hasattr(self, 'pc_table') and self.pc_table.rowCount() > 0) or \
               (hasattr(self, 'mobile_table') and self.mobile_table.rowCount() > 0):
                has_data = True
                
        self.save_analysis_button.setEnabled(has_data)
        self.clear_button.setEnabled(has_data)
        
        # 시그널 발생
        self.save_button_state_changed.emit(has_data)
        self.clear_button_state_changed.emit(has_data)
    
    def setup_mobile_header_checkbox(self):
        """모바일 테이블 헤더에 체크박스 추가 (원본과 동일)"""
        try:
            # 헤더용 체크박스 생성
            self.mobile_header_checkbox = QCheckBox()
            self.mobile_header_checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                    margin: 0px;
                    padding: 0px;
                    border: none;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                    margin: 1px;
                }
                QCheckBox::indicator:checked {
                    background-color: #dc3545;
                    border-color: #dc3545;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }
                QCheckBox::indicator:hover {
                    border-color: #999999;
                    background-color: #f8f9fa;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #c82333;
                    border-color: #c82333;
                }
            """)
            self.mobile_header_checkbox.stateChanged.connect(lambda state: self.on_header_checkbox_changed(self.mobile_table, self.mobile_header_checkbox))
            
            # 첫 번째 컬럼 헤더를 빈 문자열로 설정
            header_item = self.mobile_table.horizontalHeaderItem(0)
            if header_item:
                header_item.setText("")
            
            # 실제 위젯을 헤더에 직접 배치 (Qt의 제약으로 직접적인 위젯 설정은 어려움)
            # 대신 헤더 위치에 overlay 방식으로 체크박스 배치
            self.position_mobile_header_checkbox()
            
        except Exception as e:
            print(f"모바일 헤더 체크박스 설정 실패: {e}")
    
    def setup_pc_header_checkbox(self):
        """PC 테이블 헤더에 체크박스 추가 (원본과 동일)"""
        try:
            # 헤더용 체크박스 생성
            self.pc_header_checkbox = QCheckBox()
            self.pc_header_checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                    margin: 0px;
                    padding: 0px;
                    border: none;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                    margin: 1px;
                }
                QCheckBox::indicator:checked {
                    background-color: #dc3545;
                    border-color: #dc3545;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }
                QCheckBox::indicator:hover {
                    border-color: #999999;
                    background-color: #f8f9fa;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #c82333;
                    border-color: #c82333;
                }
            """)
            self.pc_header_checkbox.stateChanged.connect(lambda state: self.on_header_checkbox_changed(self.pc_table, self.pc_header_checkbox))
            
            # 첫 번째 컬럼 헤더를 빈 문자열로 설정
            header_item = self.pc_table.horizontalHeaderItem(0)
            if header_item:
                header_item.setText("")
            
            # 실제 위젯을 헤더에 직접 배치 (Qt의 제약으로 직접적인 위젯 설정은 어려움)
            # 대신 헤더 위치에 overlay 방식으로 체크박스 배치
            self.position_pc_header_checkbox()
            
        except Exception as e:
            print(f"PC 헤더 체크박스 설정 실패: {e}")
    
    def position_mobile_header_checkbox(self):
        """모바일 테이블 헤더 위치에 체크박스 오버레이"""
        try:
            if not hasattr(self, 'mobile_header_checkbox') or not self.mobile_header_checkbox:
                return
                
            # QTableWidget의 헤더 영역 위치 계산
            header = self.mobile_table.horizontalHeader()
            
            # 안전한 위치 계산
            if header.sectionSize(0) <= 0:
                return
                
            header_rect = header.sectionViewportPosition(0), 0, header.sectionSize(0), header.height()
            
            # 체크박스를 헤더 위에 오버레이로 배치 (부모는 한번만 설정)
            if self.mobile_header_checkbox.parent() != self.mobile_table:
                self.mobile_header_checkbox.setParent(self.mobile_table)
            
            # 체크박스 위치 계산 및 설정 (센터 정렬, 18px 크기)
            checkbox_x = header_rect[0] + (header_rect[2] - 22) // 2
            checkbox_y = (header_rect[3] - 22) // 2
            
            self.mobile_header_checkbox.setGeometry(checkbox_x, checkbox_y, 22, 22)
            self.mobile_header_checkbox.show()
            self.mobile_header_checkbox.raise_()  # 최상위로 올리기
            
        except Exception as e:
            print(f"모바일 헤더 체크박스 위치 설정 실패: {e}")
    
    def position_pc_header_checkbox(self):
        """PC 테이블 헤더 위치에 체크박스 오버레이"""
        try:
            if not hasattr(self, 'pc_header_checkbox') or not self.pc_header_checkbox:
                return
                
            # QTableWidget의 헤더 영역 위치 계산
            header = self.pc_table.horizontalHeader()
            
            # 안전한 위치 계산
            if header.sectionSize(0) <= 0:
                return
                
            header_rect = header.sectionViewportPosition(0), 0, header.sectionSize(0), header.height()
            
            # 체크박스를 헤더 위에 오버레이로 배치 (부모는 한번만 설정)
            if self.pc_header_checkbox.parent() != self.pc_table:
                self.pc_header_checkbox.setParent(self.pc_table)
            
            # 체크박스 위치 계산 및 설정 (센터 정렬, 18px 크기)
            checkbox_x = header_rect[0] + (header_rect[2] - 22) // 2
            checkbox_y = (header_rect[3] - 22) // 2
            
            self.pc_header_checkbox.setGeometry(checkbox_x, checkbox_y, 22, 22)
            self.pc_header_checkbox.show()
            self.pc_header_checkbox.raise_()  # 최상위로 올리기
            
        except Exception as e:
            print(f"PC 헤더 체크박스 위치 설정 실패: {e}")
    
    def on_header_checkbox_changed(self, table: QTableWidget, header_checkbox: QCheckBox):
        """헤더 체크박스 상태 변경 시 모든 행 체크박스 상태 변경"""
        try:
            is_checked = header_checkbox.isChecked()
            
            # 모든 행의 체크박스 상태를 헤더 체크박스와 동일하게 설정
            for row in range(table.rowCount()):
                # 컨테이너 위젯 내의 체크박스 찾기
                container_widget = table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.blockSignals(True)  # 시그널 차단으로 무한 루프 방지
                        checkbox.setChecked(is_checked)
                        checkbox.blockSignals(False)  # 시그널 재활성화
            
            # 삭제 버튼 상태 업데이트
            self.update_delete_button_state()
            
        except Exception as e:
            print(f"헤더 체크박스 변경 처리 실패: {e}")
    
    def position_all_header_checkboxes(self):
        """모든 헤더 체크박스 위치 조정"""
        self.position_mobile_header_checkbox()
        self.position_pc_header_checkbox()
        self.position_history_header_checkbox()
    
    def setup_history_header_checkbox(self):
        """히스토리 테이블 헤더에 체크박스 추가 (원본과 동일)"""
        try:
            # 헤더용 체크박스 생성
            self.history_header_checkbox = QCheckBox()
            self.history_header_checkbox.setStyleSheet(f"""
                QCheckBox {{
                    spacing: 0px;
                    margin: 0px;
                    padding: 0px;
                    border: none;
                    background-color: transparent;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                    margin: 1px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {ModernStyle.COLORS['danger']};
                    border-color: {ModernStyle.COLORS['danger']};
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }}
                QCheckBox::indicator:hover {{
                    border-color: #999999;
                    background-color: #f8f9fa;
                }}
                QCheckBox::indicator:checked:hover {{
                    background-color: #c82333;
                    border-color: #c82333;
                }}
            """)
            self.history_header_checkbox.stateChanged.connect(lambda state: self.on_history_header_checkbox_changed(state))
            
            # 첫 번째 컬럼 헤더를 빈 문자열로 설정
            header_item = self.history_table.horizontalHeaderItem(0)
            if header_item:
                header_item.setText("")
            
            # 헤더 위치에 오버레이로 체크박스 배치
            self.position_history_header_checkbox()
            
        except Exception as e:
            print(f"히스토리 헤더 체크박스 설정 실패: {e}")
    
    def position_history_header_checkbox(self):
        """히스토리 테이블 헤더 위치에 체크박스 오버레이"""
        try:
            if not hasattr(self, 'history_header_checkbox') or not self.history_header_checkbox:
                return
                
            # QTableWidget의 헤더 영역 위치 계산
            header = self.history_table.horizontalHeader()
            
            # 안전한 위치 계산
            if header.sectionSize(0) <= 0:
                return
                
            header_rect = header.sectionViewportPosition(0), 0, header.sectionSize(0), header.height()
            
            # 체크박스를 헤더 위에 오버레이로 배치 (부모는 한번만 설정)
            if self.history_header_checkbox.parent() != self.history_table:
                self.history_header_checkbox.setParent(self.history_table)
            
            # 체크박스 위치 조정 (중앙 정렬)
            x = header_rect[0] + (header_rect[2] - self.history_header_checkbox.width()) // 2
            y = header_rect[1] + (header_rect[3] - self.history_header_checkbox.height()) // 2
            
            self.history_header_checkbox.move(x, y)
            self.history_header_checkbox.show()
            self.history_header_checkbox.raise_()  # 다른 위젯 위로 올리기
            
        except Exception as e:
            print(f"히스토리 헤더 체크박스 위치 조정 실패: {e}")
    
    def on_history_header_checkbox_changed(self, state):
        """히스토리 헤더 체크박스 상태 변경 처리"""
        try:
            is_checked = (state == 2)  # Qt.Checked
            
            # 모든 행의 체크박스 상태 변경
            for row in range(self.history_table.rowCount()):
                container_widget = self.history_table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.blockSignals(True)  # 시그널 차단으로 무한 루프 방지
                        checkbox.setChecked(is_checked)
                        checkbox.blockSignals(False)  # 시그널 재활성화
            
            # 히스토리 버튼 상태 업데이트
            self.update_history_button_states()
            
        except Exception as e:
            print(f"히스토리 헤더 체크박스 변경 처리 실패: {e}")
    
    def update_history_button_states(self):
        """히스토리 관련 버튼 상태 업데이트"""
        try:
            selected_count = 0
            for row in range(self.history_table.rowCount()):
                container_widget = self.history_table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        selected_count += 1
            
            # 버튼 활성화 상태 및 텍스트 업데이트
            has_selection = selected_count > 0
            
            # 선택삭제 버튼에 개수 표시
            if has_selection:
                self.delete_history_button.setText(f"🗑️ 선택삭제({selected_count})")
                self.export_selected_history_button.setText(f"💾 선택저장({selected_count})")
            else:
                self.delete_history_button.setText("🗑️ 선택삭제")
                self.export_selected_history_button.setText("💾 선택저장")
            
            self.delete_history_button.setEnabled(has_selection)
            self.export_selected_history_button.setEnabled(has_selection)
            self.view_history_button.setEnabled(selected_count == 1)  # 보기는 1개만 선택시
            
        except Exception as e:
            print(f"히스토리 버튼 상태 업데이트 실패: {e}")
    
    def on_tab_changed(self, index):
        """탭 변경 시 처리"""
        # 이전기록 탭(index 2)에서 저장 버튼 비활성화
        if index == 2:  # 이전기록 탭
            self.save_analysis_button.setEnabled(False)
        else:  # 모바일 분석(0) 또는 PC 분석(1) 탭
            self.update_save_button_state()
    
    def update_save_button_state(self):
        """저장 버튼 상태 업데이트"""
        try:
            # self.keywords_data와 keyword_database.keywords 둘 다 확인
            local_count = len(self.keywords_data) if hasattr(self, 'keywords_data') else 0
            db_count = len(keyword_database.keywords)
            has_data = max(local_count, db_count) > 0
            
            self.save_analysis_button.setEnabled(has_data)
            self.clear_button.setEnabled(has_data)
            
            # 간단한 텍스트로 고정 (카운트 제거)
            self.save_analysis_button.setText("💾 현재 분석 저장")
                
        except Exception as e:
            logger.error(f"저장 버튼 상태 업데이트 실패: {e}")
    
    def on_analysis_started(self):
        """분석 시작 시 저장 버튼 비활성화"""
        self.save_analysis_button.setEnabled(False)
        self.save_analysis_button.setText("💾 분석 중...")
        log_manager.add_log("PowerLink 분석 시작 - 저장 버튼 비활성화", "info")
    
    def on_analysis_finished(self):
        """분석 완료 시 저장 버튼 활성화"""
        self.save_analysis_button.setText("💾 현재 분석 저장")
        # 저장 가능한 데이터가 있으면 버튼 활성화
        self.update_save_button_state()
        log_manager.add_log("PowerLink 분석 완료 - 저장 버튼 상태 업데이트", "info")
    
    def save_current_analysis(self):
        """현재 분석 결과 저장"""
        try:
            # 현재 키워드 데이터 가져오기
            keywords_data = keyword_database.keywords
            
            if not keywords_data:
                from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                dialog = ModernConfirmDialog(
                    self,
                    "저장 실패",
                    "저장할 분석 결과가 없습니다.\n\n키워드 분석을 먼저 실행해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # 중복 확인
            db = get_db()
            is_duplicate = db.check_powerlink_session_duplicate_24h(keywords_data)
            
            from datetime import datetime
            session_name = f"PowerLink분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if is_duplicate:
                # 중복이면 저장하지 않고 다이얼로그만 표시
                save_dialog = PowerLinkSaveDialog(
                    session_id=0,  # 더미값
                    session_name=session_name,
                    keyword_count=len(keywords_data),
                    is_duplicate=True,
                    parent=self
                )
                save_dialog.exec()
            else:
                # 중복이 아니면 DB에 저장하고 다이얼로그 표시
                session_id = db.save_powerlink_analysis_session(keywords_data)
                
                # 히스토리 새로고침
                self.refresh_history_list()
                
                save_dialog = PowerLinkSaveDialog(
                    session_id=session_id,
                    session_name=session_name,
                    keyword_count=len(keywords_data),
                    is_duplicate=False,
                    parent=self
                )
                save_dialog.exec()
                
                log_manager.add_log(f"PowerLink 분석 세션 저장 완료: {session_name} ({len(keywords_data)}개 키워드)", "success")
            
        except Exception as e:
            logger.error(f"PowerLink 분석 세션 저장 실패: {e}")
            log_manager.add_log(f"PowerLink 분석 세션 저장 실패: {e}", "error")
    
    def clear_all_analysis(self):
        """전체 분석 결과 클리어"""
        try:
            # 데이터가 있는지 확인
            if not keyword_database.keywords:
                return
            
            # 모던 확인 다이얼로그 (클리어 버튼 근처에 표시)
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self,
                "전체 클리어 확인",
                f"모든 분석 결과를 삭제하시겠습니까?\\n\\n현재 키워드: {len(keyword_database.keywords)}개\\n\\n이 작업은 되돌릴 수 없습니다.",
                confirm_text="삭제",
                cancel_text="취소",
                icon="🗑",
                position_near_widget=self.clear_button
            )
            
            if dialog.exec() == ModernConfirmDialog.Accepted:
                # 메모리 데이터베이스 클리어
                keyword_database.clear()
                
                # 테이블 클리어
                self.mobile_table.setRowCount(0)
                self.pc_table.setRowCount(0)
                
                # 버튼 상태 업데이트
                self.update_save_button_state()
                
                log_manager.add_log("PowerLink 분석 결과 전체 클리어", "success")
                
        except Exception as e:
            logger.error(f"전체 클리어 실패: {e}")
            log_manager.add_log(f"PowerLink 전체 클리어 실패: {e}", "error")
    
    def add_keyword_immediately(self, keyword: str):
        """키워드를 즉시 테이블에 추가 (데이터 로딩 전 상태로)"""
        try:
            # 중복 체크 - 이미 테이블에 있는지 확인
            mobile_existing = self.find_keyword_row_in_table(self.mobile_table, keyword)
            pc_existing = self.find_keyword_row_in_table(self.pc_table, keyword)
            
            if mobile_existing >= 0 or pc_existing >= 0:
                logger.debug(f"키워드 '{keyword}' 이미 테이블에 존재함 (모바일: {mobile_existing}, PC: {pc_existing})")
                return
            
            # 빈 결과 객체 생성 (모든 값을 "-"로 초기화)
            empty_result = KeywordAnalysisResult(
                keyword=keyword,
                pc_search_volume=-1,  # -1은 아직 분석되지 않음을 의미
                mobile_search_volume=-1,  # -1은 아직 분석되지 않음을 의미
                pc_clicks=-1,  # -1은 아직 분석되지 않음을 의미 (0과 구분)
                pc_ctr=-1,  # -1은 아직 분석되지 않음을 의미 (0과 구분)
                pc_first_page_positions=0,
                pc_first_position_bid=0,
                pc_min_exposure_bid=0,
                pc_bid_positions=[],
                mobile_clicks=-1,  # -1은 아직 분석되지 않음을 의미 (0과 구분)
                mobile_ctr=-1,  # -1은 아직 분석되지 않음을 의미 (0과 구분)
                mobile_first_page_positions=0,
                mobile_first_position_bid=0,
                mobile_min_exposure_bid=0,
                mobile_bid_positions=[],
                pc_recommendation_rank=0,
                mobile_recommendation_rank=0,
                analyzed_at=datetime.now()
            )
            
            # 모바일과 PC 테이블에 모두 추가 (데이터는 "-"로 표시)
            mobile_row = self.mobile_table.rowCount()
            self.mobile_table.insertRow(mobile_row)
            self.add_keyword_to_table_row(self.mobile_table, mobile_row, empty_result, 'mobile')
            
            pc_row = self.pc_table.rowCount()
            self.pc_table.insertRow(pc_row)
            self.add_keyword_to_table_row(self.pc_table, pc_row, empty_result, 'pc')
            
            logger.debug(f"키워드 '{keyword}' 즉시 추가 완료 (모바일: {mobile_row}, PC: {pc_row})")
            
        except Exception as e:
            logger.error(f"키워드 즉시 추가 실패: {keyword}: {e}")
    
    def update_keyword_data(self, keyword: str, result: KeywordAnalysisResult):
        """실시간으로 키워드 데이터 업데이트"""
        try:
            # 모바일 테이블에서 키워드 행 찾기
            mobile_row = self.find_keyword_row_in_table(self.mobile_table, keyword)
            if mobile_row >= 0:
                self.update_table_row_data(self.mobile_table, mobile_row, result, 'mobile')
                logger.debug(f"모바일 테이블 행 {mobile_row} 업데이트: {keyword}")
            
            # PC 테이블에서 키워드 행 찾기
            pc_row = self.find_keyword_row_in_table(self.pc_table, keyword)
            if pc_row >= 0:
                self.update_table_row_data(self.pc_table, pc_row, result, 'pc')
                logger.debug(f"PC 테이블 행 {pc_row} 업데이트: {keyword}")
            
            if mobile_row < 0 and pc_row < 0:
                logger.warning(f"키워드 '{keyword}' 테이블에서 찾을 수 없음")
                
            # 저장 버튼 상태 업데이트
            self.update_save_button_state()
                
        except Exception as e:
            logger.error(f"키워드 데이터 업데이트 실패: {keyword}: {e}")
    
    def find_keyword_row_in_table(self, table: QTableWidget, keyword: str) -> int:
        """테이블에서 특정 키워드의 행 번호 찾기"""
        for row in range(table.rowCount()):
            item = table.item(row, 1)  # 키워드는 1번 컬럼
            if item and item.text() == keyword:
                return row
        return -1
    
    def update_table_row_data(self, table: QTableWidget, row: int, result: KeywordAnalysisResult, device_type: str):
        """테이블 특정 행의 데이터를 실시간으로 업데이트"""
        try:
            # 2. 월검색량 (device specific)
            if device_type == 'mobile':
                if hasattr(result, 'mobile_search_volume') and result.mobile_search_volume is not None and result.mobile_search_volume >= 0:
                    volume_text, volume_value = safe_format_number(result.mobile_search_volume, "int")
                    search_volume_item = SortableTableWidgetItem(volume_text, volume_value)
                else:
                    search_volume_item = SortableTableWidgetItem("-", 0)
            else:  # PC
                if hasattr(result, 'pc_search_volume') and result.pc_search_volume is not None and result.pc_search_volume >= 0:
                    volume_text, volume_value = safe_format_number(result.pc_search_volume, "int")
                    search_volume_item = SortableTableWidgetItem(volume_text, volume_value)
                else:
                    search_volume_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 2, search_volume_item)
            
            # 디바이스별 데이터 업데이트
            if device_type == 'mobile':
                # 3. 클릭수
                if hasattr(result, 'mobile_clicks') and result.mobile_clicks is not None and result.mobile_clicks >= 0:
                    clicks_text, clicks_value = safe_format_number(result.mobile_clicks, "float1")
                    clicks_item = SortableTableWidgetItem(clicks_text, clicks_value)
                else:
                    clicks_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 3, clicks_item)
                
                # 4. 클릭률
                if hasattr(result, 'mobile_ctr') and result.mobile_ctr is not None and result.mobile_ctr >= 0:
                    ctr_text, ctr_value = safe_format_number(result.mobile_ctr, "float2", "%")
                    ctr_item = SortableTableWidgetItem(ctr_text, ctr_value)
                else:
                    ctr_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 4, ctr_item)
                
                # 5. 1p노출위치
                if hasattr(result, 'mobile_first_page_positions') and result.mobile_first_page_positions is not None:
                    position_text, position_value = safe_format_number(result.mobile_first_page_positions, "int", "위까지")
                    position_item = SortableTableWidgetItem(position_text, position_value)
                else:
                    position_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 5, position_item)
                
                # 6. 1등광고비
                if hasattr(result, 'mobile_first_position_bid') and result.mobile_first_position_bid is not None:
                    first_bid_text, first_bid_value = safe_format_number(result.mobile_first_position_bid, "int", "원")
                    first_bid_item = SortableTableWidgetItem(first_bid_text, first_bid_value)
                else:
                    first_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 6, first_bid_item)
                
                # 7. 최소노출가격
                if hasattr(result, 'mobile_min_exposure_bid') and result.mobile_min_exposure_bid is not None:
                    min_bid_text, min_bid_value = safe_format_number(result.mobile_min_exposure_bid, "int", "원")
                    min_bid_item = SortableTableWidgetItem(min_bid_text, min_bid_value)
                else:
                    min_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 7, min_bid_item)
                
                # 8. 추천순위
                mobile_rank = getattr(result, 'mobile_recommendation_rank', 0) if hasattr(result, 'mobile_recommendation_rank') else 0
                if mobile_rank > 0:
                    rank_item = SortableTableWidgetItem(str(mobile_rank), mobile_rank)
                else:
                    rank_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 8, rank_item)
                
            else:  # PC
                # 3. 클릭수
                if hasattr(result, 'pc_clicks') and result.pc_clicks is not None and result.pc_clicks >= 0:
                    clicks_text, clicks_value = safe_format_number(result.pc_clicks, "float1")
                    clicks_item = SortableTableWidgetItem(clicks_text, clicks_value)
                else:
                    clicks_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 3, clicks_item)
                
                # 4. 클릭률
                if hasattr(result, 'pc_ctr') and result.pc_ctr is not None and result.pc_ctr >= 0:
                    ctr_text, ctr_value = safe_format_number(result.pc_ctr, "float2", "%")
                    ctr_item = SortableTableWidgetItem(ctr_text, ctr_value)
                else:
                    ctr_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 4, ctr_item)
                
                # 5. 1p노출위치
                if hasattr(result, 'pc_first_page_positions') and result.pc_first_page_positions is not None:
                    position_text, position_value = safe_format_number(result.pc_first_page_positions, "int", "위까지")
                    position_item = SortableTableWidgetItem(position_text, position_value)
                else:
                    position_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 5, position_item)
                
                # 6. 1등광고비
                if hasattr(result, 'pc_first_position_bid') and result.pc_first_position_bid is not None:
                    first_bid_text, first_bid_value = safe_format_number(result.pc_first_position_bid, "int", "원")
                    first_bid_item = SortableTableWidgetItem(first_bid_text, first_bid_value)
                else:
                    first_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 6, first_bid_item)
                
                # 7. 최소노출가격
                if hasattr(result, 'pc_min_exposure_bid') and result.pc_min_exposure_bid is not None:
                    min_bid_text, min_bid_value = safe_format_number(result.pc_min_exposure_bid, "int", "원")
                    min_bid_item = SortableTableWidgetItem(min_bid_text, min_bid_value)
                else:
                    min_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 7, min_bid_item)
                
                # 8. 추천순위
                pc_rank = getattr(result, 'pc_recommendation_rank', 0) if hasattr(result, 'pc_recommendation_rank') else 0
                if pc_rank > 0:
                    rank_item = SortableTableWidgetItem(str(pc_rank), pc_rank)
                else:
                    rank_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 8, rank_item)
            
            # 상세 버튼은 이미 설정되어 있으므로 건드리지 않음
            
        except Exception as e:
            logger.error(f"테이블 행 데이터 업데이트 실패: row {row}, device {device_type}: {e}")
    
    def set_keywords_data(self, keywords_data):
        """키워드 데이터 설정"""
        # 새로운 키워드 데이터를 기존 데이터에 추가/업데이트
        for keyword, result in keywords_data.items():
            keyword_database.add_keyword(result)
        
        # 순위 재계산
        keyword_database.recalculate_all_rankings()
        
        # 테이블 새로고침
        self.refresh_tables_from_database()
        
        # 버튼 상태 업데이트
        self.update_save_button_state()
    
    def refresh_tables_from_database(self):
        """데이터베이스에서 테이블 전체 새로고침"""
        try:
            # 기존 테이블 데이터 클리어
            self.mobile_table.setRowCount(0)
            self.pc_table.setRowCount(0)
            
            # 데이터베이스에서 모든 키워드 가져오기
            all_keywords = keyword_database.get_all_keywords()
            
            # 테이블에 재추가
            for result in all_keywords:
                # 모바일 테이블
                mobile_row = self.mobile_table.rowCount()
                self.mobile_table.insertRow(mobile_row)
                self.add_keyword_to_table_row(self.mobile_table, mobile_row, result, 'mobile')
                
                # PC 테이블
                pc_row = self.pc_table.rowCount()
                self.pc_table.insertRow(pc_row)
                self.add_keyword_to_table_row(self.pc_table, pc_row, result, 'pc')
            
            logger.info(f"테이블 새로고침 완료: {len(all_keywords)}개 키워드")
            
        except Exception as e:
            logger.error(f"테이블 새로고침 실패: {e}")
    
    def clear_all_tables(self):
        """모든 테이블 클리어 (전체 클리어 시 사용)"""
        try:
            self.mobile_table.setRowCount(0)
            self.pc_table.setRowCount(0)
            keyword_database.clear()
            self.update_save_button_state()
            logger.info("모든 테이블 클리어 완료")
        except Exception as e:
            logger.error(f"테이블 클리어 실패: {e}")
    
    def add_keyword_to_table_row(self, table: QTableWidget, row: int, result: KeywordAnalysisResult, device_type: str):
        """테이블 특정 행에 키워드 데이터 추가"""
        try:
            # 0. 체크박스 (히스토리 테이블과 동일한 스타일)
            checkbox = QCheckBox()
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    spacing: 0px;
                    margin: 0px;
                    padding: 0px;
                    border: none;
                    background-color: transparent;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                    margin: 0px;
                }}
                QCheckBox::indicator:checked {{
                    background-color: {ModernStyle.COLORS['danger']};
                    border-color: {ModernStyle.COLORS['danger']};
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }}
                QCheckBox::indicator:hover {{
                    border-color: #999999;
                    background-color: #f8f9fa;
                }}
                QCheckBox::indicator:checked:hover {{
                    background-color: #dc2626;
                    border-color: #dc2626;
                }}
            """)
            checkbox.stateChanged.connect(lambda: self.update_delete_button_state())
            
            # 체크박스를 중앙에 배치하기 위한 컨테이너 위젯
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            
            table.setCellWidget(row, 0, checkbox_widget)
            
            # 1. 키워드
            table.setItem(row, 1, QTableWidgetItem(result.keyword))
            
            # 2. 월검색량 (device specific)
            if device_type == 'mobile':
                if hasattr(result, 'mobile_search_volume') and result.mobile_search_volume is not None and result.mobile_search_volume >= 0:
                    volume_text, volume_value = safe_format_number(result.mobile_search_volume, "int")
                    search_volume_item = SortableTableWidgetItem(volume_text, volume_value)
                else:
                    search_volume_item = SortableTableWidgetItem("-", 0)
            else:  # PC
                if hasattr(result, 'pc_search_volume') and result.pc_search_volume is not None and result.pc_search_volume >= 0:
                    volume_text, volume_value = safe_format_number(result.pc_search_volume, "int")
                    search_volume_item = SortableTableWidgetItem(volume_text, volume_value)
                else:
                    search_volume_item = SortableTableWidgetItem("-", 0)
            table.setItem(row, 2, search_volume_item)
            
            # 디바이스별 데이터 설정
            if device_type == 'mobile':
                # 3. 클릭수
                if hasattr(result, 'mobile_clicks') and result.mobile_clicks is not None and result.mobile_clicks >= 0:
                    clicks_text, clicks_value = safe_format_number(result.mobile_clicks, "float1")
                    clicks_item = SortableTableWidgetItem(clicks_text, clicks_value)
                else:
                    clicks_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 3, clicks_item)
                
                # 4. 클릭률
                if hasattr(result, 'mobile_ctr') and result.mobile_ctr is not None and result.mobile_ctr >= 0:
                    ctr_text, ctr_value = safe_format_number(result.mobile_ctr, "float2", "%")
                    ctr_item = SortableTableWidgetItem(ctr_text, ctr_value)
                else:
                    ctr_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 4, ctr_item)
                
                # 5. 1p노출위치
                if hasattr(result, 'mobile_first_page_positions') and result.mobile_first_page_positions is not None and result.mobile_first_page_positions > 0:
                    position_text, position_value = safe_format_number(result.mobile_first_page_positions, "int", "위까지")
                    position_item = SortableTableWidgetItem(position_text, position_value)
                else:
                    position_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 5, position_item)
                
                # 6. 1등광고비
                if hasattr(result, 'mobile_first_position_bid') and result.mobile_first_position_bid is not None and result.mobile_first_position_bid > 0:
                    first_bid_text, first_bid_value = safe_format_number(result.mobile_first_position_bid, "int", "원")
                    first_bid_item = SortableTableWidgetItem(first_bid_text, first_bid_value)
                else:
                    first_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 6, first_bid_item)
                
                # 7. 최소노출가격
                if hasattr(result, 'mobile_min_exposure_bid') and result.mobile_min_exposure_bid is not None and result.mobile_min_exposure_bid > 0:
                    min_bid_text, min_bid_value = safe_format_number(result.mobile_min_exposure_bid, "int", "원")
                    min_bid_item = SortableTableWidgetItem(min_bid_text, min_bid_value)
                else:
                    min_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 7, min_bid_item)
                
                # 8. 추천순위
                mobile_rank = getattr(result, 'mobile_recommendation_rank', 0) if hasattr(result, 'mobile_recommendation_rank') else 0
                if mobile_rank > 0:
                    rank_item = SortableTableWidgetItem(str(mobile_rank), mobile_rank)
                else:
                    rank_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 8, rank_item)
                
            else:  # PC
                # 3. 클릭수
                if hasattr(result, 'pc_clicks') and result.pc_clicks is not None and result.pc_clicks >= 0:
                    clicks_text, clicks_value = safe_format_number(result.pc_clicks, "float1")
                    clicks_item = SortableTableWidgetItem(clicks_text, clicks_value)
                else:
                    clicks_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 3, clicks_item)
                
                # 4. 클릭률
                if hasattr(result, 'pc_ctr') and result.pc_ctr is not None and result.pc_ctr >= 0:
                    ctr_text, ctr_value = safe_format_number(result.pc_ctr, "float2", "%")
                    ctr_item = SortableTableWidgetItem(ctr_text, ctr_value)
                else:
                    ctr_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 4, ctr_item)
                
                # 5. 1p노출위치
                if hasattr(result, 'pc_first_page_positions') and result.pc_first_page_positions is not None and result.pc_first_page_positions > 0:
                    position_text, position_value = safe_format_number(result.pc_first_page_positions, "int", "위까지")
                    position_item = SortableTableWidgetItem(position_text, position_value)
                else:
                    position_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 5, position_item)
                
                # 6. 1등광고비
                if hasattr(result, 'pc_first_position_bid') and result.pc_first_position_bid is not None and result.pc_first_position_bid > 0:
                    first_bid_text, first_bid_value = safe_format_number(result.pc_first_position_bid, "int", "원")
                    first_bid_item = SortableTableWidgetItem(first_bid_text, first_bid_value)
                else:
                    first_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 6, first_bid_item)
                
                # 7. 최소노출가격
                if hasattr(result, 'pc_min_exposure_bid') and result.pc_min_exposure_bid is not None and result.pc_min_exposure_bid > 0:
                    min_bid_text, min_bid_value = safe_format_number(result.pc_min_exposure_bid, "int", "원")
                    min_bid_item = SortableTableWidgetItem(min_bid_text, min_bid_value)
                else:
                    min_bid_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 7, min_bid_item)
                
                # 8. 추천순위
                pc_rank = getattr(result, 'pc_recommendation_rank', 0) if hasattr(result, 'pc_recommendation_rank') else 0
                if pc_rank > 0:
                    rank_item = SortableTableWidgetItem(str(pc_rank), pc_rank)
                else:
                    rank_item = SortableTableWidgetItem("-", 0)
                table.setItem(row, 8, rank_item)
            
            # 9. 상세보기 버튼 (셀 전체를 채우는 초록색 버튼)
            detail_button = QPushButton("상세")
            detail_button.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0px;
                    font-weight: 600;
                    font-size: 13px;
                    margin: 0px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
            """)
            detail_button.clicked.connect(lambda: self.show_bid_details_dialog(result, device_type))
            table.setCellWidget(row, 9, detail_button)
            
        except Exception as e:
            logger.error(f"테이블 행 추가 실패: row {row}, device {device_type}: {e}")
    
    def update_delete_button_state(self):
        """선택삭제 버튼 상태 업데이트"""
        try:
            # 모바일 테이블 체크 여부 확인
            mobile_checked = False
            if hasattr(self, 'mobile_table'):
                for row in range(self.mobile_table.rowCount()):
                    container_widget = self.mobile_table.cellWidget(row, 0)
                    if container_widget:
                        checkbox = container_widget.findChild(QCheckBox)
                        if checkbox and checkbox.isChecked():
                            mobile_checked = True
                            break
            
            # PC 테이블 체크 여부 확인
            pc_checked = False
            if hasattr(self, 'pc_table'):
                for row in range(self.pc_table.rowCount()):
                    container_widget = self.pc_table.cellWidget(row, 0)
                    if container_widget:
                        checkbox = container_widget.findChild(QCheckBox)
                        if checkbox and checkbox.isChecked():
                            pc_checked = True
                            break
            
            # 버튼 상태 업데이트
            if hasattr(self, 'mobile_delete_button'):
                self.mobile_delete_button.setEnabled(mobile_checked)
                # 선택된 개수 표시
                if mobile_checked:
                    count = sum(1 for row in range(self.mobile_table.rowCount()) 
                              if self.mobile_table.cellWidget(row, 0) and 
                              self.mobile_table.cellWidget(row, 0).findChild(QCheckBox) and
                              self.mobile_table.cellWidget(row, 0).findChild(QCheckBox).isChecked())
                    self.mobile_delete_button.setText(f"🗑️ 선택 삭제 ({count})")
                else:
                    self.mobile_delete_button.setText("🗑️ 선택 삭제")
            
            if hasattr(self, 'pc_delete_button'):
                self.pc_delete_button.setEnabled(pc_checked)
                # 선택된 개수 표시
                if pc_checked:
                    count = sum(1 for row in range(self.pc_table.rowCount()) 
                              if self.pc_table.cellWidget(row, 0) and 
                              self.pc_table.cellWidget(row, 0).findChild(QCheckBox) and
                              self.pc_table.cellWidget(row, 0).findChild(QCheckBox).isChecked())
                    self.pc_delete_button.setText(f"🗑️ 선택 삭제 ({count})")
                else:
                    self.pc_delete_button.setText("🗑️ 선택 삭제")
                    
        except Exception as e:
            logger.error(f"삭제 버튼 상태 업데이트 실패: {e}")
    
    def delete_selected_mobile_keywords(self):
        """모바일 선택된 키워드 삭제"""
        self.delete_selected_keywords_from_table(self.mobile_table, "모바일")
    
    def delete_selected_pc_keywords(self):
        """PC 선택된 키워드 삭제"""
        self.delete_selected_keywords_from_table(self.pc_table, "PC")
    
    def delete_selected_keywords_from_table(self, table: QTableWidget, device_name: str):
        """선택된 키워드를 테이블에서 삭제"""
        try:
            # 선택된 키워드들 찾기
            selected_keywords = []
            selected_rows = []
            
            for row in range(table.rowCount()):
                container_widget = table.cellWidget(row, 0)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        keyword_item = table.item(row, 1)
                        if keyword_item:
                            selected_keywords.append(keyword_item.text())
                            selected_rows.append(row)
            
            if not selected_keywords:
                return
            
            # 모던 확인 다이얼로그
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self,
                f"{device_name} 키워드 삭제 확인",
                f"선택된 {len(selected_keywords)}개의 키워드를 삭제하시겠습니까?\\n\\n"
                f"삭제할 키워드: {', '.join(selected_keywords[:3])}{'...' if len(selected_keywords) > 3 else ''}\\n\\n"
                f"이 작업은 되돌릴 수 없습니다.",
                confirm_text="삭제",
                cancel_text="취소",
                icon="🗑️"
            )
            
            if dialog.exec() == ModernConfirmDialog.Accepted:
                # 메모리 데이터베이스에서 제거
                for keyword in selected_keywords:
                    keyword_database.remove_keyword(keyword)
                
                # 테이블에서 제거 (역순으로 제거해야 인덱스 꼬임 방지)
                for row in sorted(selected_rows, reverse=True):
                    table.removeRow(row)
                
                # 순위 재계산
                keyword_database.recalculate_all_rankings()
                
                # 저장 버튼 상태 업데이트
                self.update_save_button_state()
                
                log_manager.add_log(f"PowerLink {device_name} 키워드 {len(selected_keywords)}개 삭제", "success")
                
        except Exception as e:
            logger.error(f"{device_name} 키워드 삭제 실패: {e}")
            log_manager.add_log(f"PowerLink {device_name} 키워드 삭제 실패: {e}", "error")
    
    def show_bid_details_dialog(self, result, device_type: str):
        """입찰가 상세 다이얼로그 표시"""
        try:
            dialog = BidDetailsDialog(result.keyword, result, device_type, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"입찰가 상세 다이얼로그 표시 실패: {e}")
            # 기본 메시지박스로 대체
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "오류", f"상세 정보를 표시할 수 없습니다: {e}")


class BidDetailsDialog(QDialog):
    """입찰가 상세 정보 다이얼로그"""
    
    def __init__(self, keyword: str, result, device_type: str, parent=None):
        super().__init__(parent)
        self.keyword = keyword
        self.result = result
        self.device_type = device_type
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle(f"{self.keyword} - {self.device_type.upper()} 순위별 입찰가")
        self.setModal(True)
        self.setFixedSize(400, 600)
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 제목
        title_label = QLabel(f"🎯 {self.keyword}")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {ModernStyle.COLORS['text_primary']};
                padding: 10px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-radius: 8px;
                text-align: center;
            }}
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 디바이스 타입 라벨
        device_label = QLabel(f"{self.device_type.upper()} 순위별 입찰가")
        device_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 600;
                color: {ModernStyle.COLORS['primary']};
                text-align: center;
                margin: 5px 0px;
            }}
        """)
        device_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_label)
        
        # 입찰가 테이블 (모바일 1~5위, PC 1~10위)
        if self.device_type.lower() == 'mobile':
            bid_positions = getattr(self.result, 'mobile_bid_positions', [])
            if bid_positions:
                bid_positions = bid_positions[:5]  # 모바일 1~5등
        else:
            bid_positions = getattr(self.result, 'pc_bid_positions', [])
            if bid_positions:
                bid_positions = bid_positions[:10]  # PC 1~10등
            
        if bid_positions:
            table = self.create_simple_bid_table(bid_positions)
            layout.addWidget(table)
        else:
            # 데이터가 없을 때 메시지 표시
            no_data_label = QLabel("하과 데이터가 없습니다.")
            no_data_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    color: {ModernStyle.COLORS['text_secondary']};
                    text-align: center;
                    padding: 20px;
                    background-color: {ModernStyle.COLORS['bg_card']};
                    border: 1px solid {ModernStyle.COLORS['border']};
                    border-radius: 8px;
                }}
            """)
            no_data_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_data_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = ModernButton("닫기", "primary")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # 다이얼로그 스타일
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)
    
    def create_simple_bid_table(self, bid_positions) -> QTableWidget:
        """간단한 입찰가 테이블 생성"""
        table = QTableWidget()
        table.setRowCount(len(bid_positions))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["순위", "입찰가"])
        
        # 테이블 스타일
        table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 14px;
            }}
            QTableWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 10px;
                border: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
                font-size: 13px;
            }}
        """)
        
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 컬럼 크기 설정
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.resizeSection(0, 80)  # 순위 컬럼 너비
        
        # 데이터 추가
        for row, bid_pos in enumerate(bid_positions):
            rank_item = QTableWidgetItem(f"{bid_pos.position}위")
            rank_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, rank_item)
            
            price_item = QTableWidgetItem(f"{bid_pos.bid_price:,}원")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 1, price_item)
        
        return table
        
    def show_bid_details(self, keyword: str, result, device_type: str):
        """순위별 입찰가 상세 다이얼로그 표시"""
        try:
            from src.toolbox.ui_kit.modern_dialog import ModernDialog
            
            # 디바이스별 입찰가 데이터 가져오기
            if device_type == 'mobile':
                bid_positions = result.mobile_bid_positions
                title = f"{keyword} - 모바일 순위별 입찰가"
            else:
                bid_positions = result.pc_bid_positions
                title = f"{keyword} - PC 순위별 입찰가"
            
            if not bid_positions:
                # 모던 다이얼로그로 에러 표시
                from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                error_dialog = ModernConfirmDialog(
                    self,
                    "정보 없음",
                    f"{device_type.upper()} 순위별 입찰가 정보가 없습니다.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="ℹ️"
                )
                error_dialog.exec()
                return
            
            # 상세 다이얼로그 생성
            dialog = ModernDialog(self)
            dialog.setWindowTitle(title)
            dialog.resize(400, 500)
            
            # 테이블 생성 (선택 시 텍스트가 잘 보이도록 스타일 개선)
            table = QTableWidget()
            table.setRowCount(len(bid_positions))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["순위", "입찰가"])
            
            # 테이블 스타일 (선택된 행의 텍스트 색상 개선)
            table.setStyleSheet(f"""
                QTableWidget {{
                    gridline-color: {ModernStyle.COLORS['border']};
                    background-color: {ModernStyle.COLORS['bg_card']};
                    selection-background-color: {ModernStyle.COLORS['primary']};
                    selection-color: white;
                    border: 1px solid {ModernStyle.COLORS['border']};
                    border-radius: 8px;
                    font-size: 14px;
                }}
                QTableWidget::item {{
                    padding: 12px;
                    border-bottom: 1px solid {ModernStyle.COLORS['border']};
                    color: {ModernStyle.COLORS['text_primary']};
                }}
                QTableWidget::item:selected {{
                    background-color: {ModernStyle.COLORS['primary']};
                    color: white;
                    border: none;
                }}
                QTableWidget::item:focus {{
                    background-color: {ModernStyle.COLORS['primary']};
                    color: white;
                    outline: none;
                    border: none;
                }}
                QHeaderView::section {{
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                    color: {ModernStyle.COLORS['text_primary']};
                    padding: 10px;
                    border: 1px solid {ModernStyle.COLORS['border']};
                    font-weight: 600;
                    font-size: 13px;
                }}
            """)
            
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setStretchLastSection(True)
            table.setAlternatingRowColors(False)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            
            # 컬럼 크기 설정
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Fixed)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.resizeSection(0, 80)  # 순위 컬럼 너비
            
            # 데이터 추가
            for row, bid_pos in enumerate(bid_positions):
                rank_item = QTableWidgetItem(f"{bid_pos.position}위")
                rank_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 0, rank_item)
                
                price_item = QTableWidgetItem(f"{bid_pos.bid_price:,}원")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 1, price_item)
            
            # 다이얼로그에 테이블 추가
            layout = QVBoxLayout()
            layout.addWidget(table)
            
            # 확인 버튼
            from src.toolbox.ui_kit.components import ModernButton
            confirm_button = ModernButton("확인", "primary")
            confirm_button.clicked.connect(dialog.accept)
            
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            button_layout.addWidget(confirm_button)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            print(f"상세 다이얼로그 표시 오류: {e}")
            # 기본 메시지박스로 대체
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "오류", f"상세 정보를 표시할 수 없습니다: {e}")
    
