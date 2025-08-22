"""
파워링크 광고비 분석기 결과 위젯 (우측 패널)
분석 결과 테이블, 키워드 관리, 히스토리 기능을 포함
"""
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from src.toolbox.ui_kit import ModernStyle, ModernTableWidget
from src.toolbox.ui_kit.components import ModernButton
from src.toolbox.formatters import format_int, format_float, format_price_krw
from src.desktop.common_log import log_manager
from src.foundation.logging import get_logger
from .models import KeywordAnalysisResult
from .service import powerlink_service

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
        """엑셀 내보내기 실행 (UI 로직만)"""
        try:
            # 현재 분석 결과 가져오기
            keywords_data = powerlink_service.get_all_keywords()
            
            # service에 위임 (오케스트레이션 + adapters 파일 I/O)
            success = powerlink_service.export_current_analysis_with_dialog(
                keywords_data=keywords_data,
                session_name=getattr(self, 'session_name', ''),
                parent_widget=self
            )
            
            if success:
                self.accept()  # 다이얼로그 종료
        
        except Exception as e:
            log_manager.add_log(f"PowerLink 엑셀 내보내기 UI 처리 실패: {e}", "error")
            




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
        
        # 히스토리 로드 플래그 초기화
        self.is_loaded_from_history = False
        
        self.setup_ui()
        self.setup_connections()
        
        # 초기 히스토리 로드 (UI 생성 후)
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
        
        # 이전 기록 테이블 (ModernTableWidget 사용)
        self.history_table = ModernTableWidget(
            columns=["", "세션명", "생성일시", "키워드 수"],
            has_checkboxes=True,
            has_header_checkbox=True
        )
        
        # 컬럼 너비 설정 (체크박스 컬럼 제외)
        header = self.history_table.horizontalHeader()
        # header.resizeSection(0, 50)   # 체크박스 컬럼 - ModernTableWidget에서 자동으로 80px 고정 처리
        header.resizeSection(1, 300)  # 세션명 컬럼  
        header.resizeSection(2, 150)  # 생성일시 컬럼
        header.resizeSection(3, 100)  # 키워드 수 컬럼
        header.setStretchLastSection(True)
        
        layout.addWidget(self.history_table)
        
        return tab
    
    def create_analysis_table(self) -> ModernTableWidget:
        """분석 결과 테이블 생성 (ModernTableWidget 사용)"""
        # 헤더 설정 (체크박스는 자동으로 처리됨)
        headers = [
            "", "키워드", "월검색량", "클릭수", "클릭률", 
            "1p노출위치", "1등광고비", "최소노출가격", "추천순위", "상세"
        ]
        
        table = ModernTableWidget(
            columns=headers,
            has_checkboxes=True,
            has_header_checkbox=True
        )
        
        # 헤더 설정
        header = table.horizontalHeader()
        
        # 체크박스 컬럼은 ModernTableWidget에서 자동으로 80px 고정 처리됨
        
        # 컬럼 너비 설정
        header.resizeSection(1, 180)  # 키워드
        header.resizeSection(2, 80)   # 월검색량
        header.resizeSection(3, 70)   # 클릭수
        header.resizeSection(4, 70)   # 클릭률
        header.resizeSection(5, 90)   # 1p노출위치
        header.resizeSection(6, 90)   # 1등광고비
        header.resizeSection(7, 110)  # 최소노출가격
        header.resizeSection(8, 80)   # 추천순위
        header.resizeSection(9, 100)  # 상세
        
        # ModernTableWidget에서 정렬 자동 활성화
        
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
        
        # ModernTableWidget 선택 상태 변경 시그널 연결
        self.mobile_table.selection_changed.connect(self.update_delete_button_state)
        self.pc_table.selection_changed.connect(self.update_delete_button_state)
        self.history_table.selection_changed.connect(self.update_history_button_state)
        
        # 탭 변경 시그널 연결 (이전기록 탭에서 저장 버튼 비활성화)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    
    def update_all_tables(self):
        """모든 테이블 업데이트"""
        self.update_mobile_table()
        self.update_pc_table()
        
    def update_mobile_table(self):
        """모바일 테이블 업데이트 (ModernTableWidget API 사용)"""
        mobile_sorted = powerlink_service.get_mobile_rankings()
        
        # 테이블 클리어
        self.mobile_table.clear_table()
        
        for result in mobile_sorted:
            
            # 데이터 준비
            keyword = result.keyword
            
            # 월검색량
            if result.mobile_search_volume >= 0:
                search_volume = format_int(result.mobile_search_volume)
            else:
                search_volume = "-"
            
            # 추천순위
            if result.mobile_recommendation_rank > 0:
                rank_text = f"{result.mobile_recommendation_rank}위"
            else:
                rank_text = "-"
            
            # 행 데이터 준비 (체크박스 제외)
            row_data = [
                keyword,  # 키워드
                search_volume,  # 월검색량
                format_float(result.mobile_clicks, precision=1) if result.mobile_clicks >= 0 else "-",  # 클릭수
                f"{format_float(result.mobile_ctr, precision=2)}%" if result.mobile_ctr >= 0 else "-",  # 클릭률
                f"{format_int(result.mobile_first_page_positions)}위까지" if result.mobile_first_page_positions >= 0 else "-",  # 1p노출위치
                format_price_krw(result.mobile_first_position_bid) if result.mobile_first_position_bid >= 0 else "-",  # 1등광고비
                format_price_krw(result.mobile_min_exposure_bid) if result.mobile_min_exposure_bid >= 0 else "-",  # 최소노출가격
                rank_text,  # 추천순위
                "상세"  # 상세 버튼
            ]
            
            # ModernTableWidget API 사용하여 행 추가 (반환값으로 행 번호 받기)
            row = self.mobile_table.add_row_with_data(row_data, checkable=True)
            
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
            detail_button.clicked.connect(lambda checked, k=keyword, r=result: self.show_bid_details(k, r, 'mobile'))
            self.mobile_table.setCellWidget(row, 9, detail_button)
            
    def update_pc_table(self):
        """PC 테이블 업데이트 (ModernTableWidget API 사용)"""
        pc_sorted = powerlink_service.get_pc_rankings()
        
        # 테이블 클리어
        self.pc_table.clear_table()
        
        for result in pc_sorted:
            # 데이터 준비
            keyword = result.keyword
            
            # 월검색량
            if result.pc_search_volume >= 0:
                search_volume = format_int(result.pc_search_volume)
            else:
                search_volume = "-"
            
            # 추천순위
            if result.pc_recommendation_rank > 0:
                rank_text = f"{result.pc_recommendation_rank}위"
            else:
                rank_text = "-"
            
            # 행 데이터 준비 (체크박스 제외)
            row_data = [
                keyword,  # 키워드
                search_volume,  # 월검색량
                format_float(result.pc_clicks, precision=1) if result.pc_clicks >= 0 else "-",  # 클릭수
                f"{format_float(result.pc_ctr, precision=2)}%" if result.pc_ctr >= 0 else "-",  # 클릭률
                f"{format_int(result.pc_first_page_positions)}위까지" if result.pc_first_page_positions >= 0 else "-",  # 1p노출위치
                format_price_krw(result.pc_first_position_bid) if result.pc_first_position_bid >= 0 else "-",  # 1등광고비
                format_price_krw(result.pc_min_exposure_bid) if result.pc_min_exposure_bid >= 0 else "-",  # 최소노출가격
                rank_text,  # 추천순위
                "상세"  # 상세 버튼
            ]
            
            # ModernTableWidget API 사용하여 행 추가 (반환값으로 행 번호 받기)
            row = self.pc_table.add_row_with_data(row_data, checkable=True)
            
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
            detail_button.clicked.connect(lambda checked, k=keyword, r=result: self.show_bid_details(k, r, 'pc'))
            self.pc_table.setCellWidget(row, 9, detail_button)
    
    
    def update_keyword_row_in_table(self, table: QTableWidget, keyword: str, result, device_type: str):
        """특정 키워드의 테이블 행 업데이트"""
        for row in range(table.rowCount()):
            keyword_item = table.item(row, 1)
            if keyword_item and keyword_item.text() == keyword:
                # 해당 행의 데이터 업데이트
                self.update_table_row_data(table, row, result, device_type)
                break
    
    def update_table_row_data(self, table: QTableWidget, row: int, result, device_type: str):
        """테이블의 특정 행 데이터 업데이트"""
        try:
            if device_type == 'mobile':
                # 모바일 데이터 업데이트
                table.item(row, 2).setText(format_int(result.mobile_search_volume) if result.mobile_search_volume >= 0 else "-")  # 월검색량
                table.item(row, 3).setText(format_float(result.mobile_clicks, precision=1) if result.mobile_clicks >= 0 else "-")  # 클릭수
                table.item(row, 4).setText(f"{format_float(result.mobile_ctr, precision=2)}%" if result.mobile_ctr >= 0 else "-")  # 클릭률
                table.item(row, 5).setText(f"{format_int(result.mobile_first_page_positions)}위까지" if result.mobile_first_page_positions >= 0 else "-")  # 1p노출위치
                table.item(row, 6).setText(format_price_krw(result.mobile_first_position_bid) if result.mobile_first_position_bid >= 0 else "-")  # 1등광고비
                table.item(row, 7).setText(format_price_krw(result.mobile_min_exposure_bid) if result.mobile_min_exposure_bid >= 0 else "-")  # 최소노출가격
                table.item(row, 8).setText(f"{result.mobile_recommendation_rank}위" if result.mobile_recommendation_rank > 0 else "-")  # 추천순위
            else:  # PC
                # PC 데이터 업데이트
                table.item(row, 2).setText(format_int(result.pc_search_volume) if result.pc_search_volume >= 0 else "-")  # 월검색량
                table.item(row, 3).setText(format_float(result.pc_clicks, precision=1) if result.pc_clicks >= 0 else "-")  # 클릭수
                table.item(row, 4).setText(f"{format_float(result.pc_ctr, precision=2)}%" if result.pc_ctr >= 0 else "-")  # 클릭률
                table.item(row, 5).setText(f"{format_int(result.pc_first_page_positions)}위까지" if result.pc_first_page_positions >= 0 else "-")  # 1p노출위치
                table.item(row, 6).setText(format_price_krw(result.pc_first_position_bid) if result.pc_first_position_bid >= 0 else "-")  # 1등광고비
                table.item(row, 7).setText(format_price_krw(result.pc_min_exposure_bid) if result.pc_min_exposure_bid >= 0 else "-")  # 최소노출가격
                table.item(row, 8).setText(f"{result.pc_recommendation_rank}위" if result.pc_recommendation_rank > 0 else "-")  # 추천순위
        except Exception as e:
            logger.error(f"테이블 행 {row} 업데이트 실패 ({device_type}): {e}")

    def add_keyword_to_table(self, table: ModernTableWidget, result, device_type: str, update_ui: bool = True):
        """테이블에 키워드 분석 결과 추가 (ModernTableWidget 완전 사용)"""
        try:
            # 디바이스별 데이터 준비
            if device_type == 'mobile':
                # 월검색량
                search_volume = f"{result.mobile_search_volume:,}" if hasattr(result, 'mobile_search_volume') and result.mobile_search_volume >= 0 else "-"
                
                # 클릭수
                clicks = f"{result.mobile_clicks:.1f}" if hasattr(result, 'mobile_clicks') and result.mobile_clicks is not None else "-"
                
                # 클릭률
                ctr = f"{result.mobile_ctr:.2f}%" if hasattr(result, 'mobile_ctr') and result.mobile_ctr is not None else "-"
                
                # 1p노출위치
                position = f"{result.mobile_first_page_positions}위까지" if hasattr(result, 'mobile_first_page_positions') and result.mobile_first_page_positions is not None else "-"
                
                # 1등광고비
                first_bid = f"{result.mobile_first_position_bid:,}원" if hasattr(result, 'mobile_first_position_bid') and result.mobile_first_position_bid is not None else "-"
                
                # 최소노출가격
                min_bid = f"{result.mobile_min_exposure_bid:,}원" if hasattr(result, 'mobile_min_exposure_bid') and result.mobile_min_exposure_bid is not None else "-"
                
                # 추천순위
                mobile_rank = getattr(result, 'mobile_recommendation_rank', 0) if hasattr(result, 'mobile_recommendation_rank') else 0
                rank = f"{mobile_rank}위" if mobile_rank > 0 else "-"
                
            else:  # PC
                # 월검색량
                search_volume = f"{result.pc_search_volume:,}" if hasattr(result, 'pc_search_volume') and result.pc_search_volume >= 0 else "-"
                
                # 클릭수
                clicks = f"{result.pc_clicks:.1f}" if hasattr(result, 'pc_clicks') and result.pc_clicks is not None else "-"
                
                # 클릭률
                ctr = f"{result.pc_ctr:.2f}%" if hasattr(result, 'pc_ctr') and result.pc_ctr is not None else "-"
                
                # 1p노출위치
                position = f"{result.pc_first_page_positions}위까지" if hasattr(result, 'pc_first_page_positions') and result.pc_first_page_positions is not None else "-"
                
                # 1등광고비
                first_bid = f"{result.pc_first_position_bid:,}원" if hasattr(result, 'pc_first_position_bid') and result.pc_first_position_bid is not None else "-"
                
                # 최소노출가격
                min_bid = f"{result.pc_min_exposure_bid:,}원" if hasattr(result, 'pc_min_exposure_bid') and result.pc_min_exposure_bid is not None else "-"
                
                # 추천순위
                pc_rank = getattr(result, 'pc_recommendation_rank', 0) if hasattr(result, 'pc_recommendation_rank') else 0
                rank = f"{pc_rank}위" if pc_rank > 0 else "-"
            
            # 행 데이터 준비 (체크박스 제외)
            row_data = [
                result.keyword,    # 키워드
                search_volume,     # 월검색량
                clicks,           # 클릭수
                ctr,              # 클릭률
                position,         # 1p노출위치
                first_bid,        # 1등광고비
                min_bid,          # 최소노출가격
                rank,             # 추천순위
                "상세"            # 상세 버튼
            ]
            
            # ModernTableWidget API 사용하여 행 추가 (반환값으로 행 번호 받기)
            row = table.add_row_with_data(row_data, checkable=True)
            
            # 상세 버튼 추가 (9번 컬럼)
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
            table.setCellWidget(row, 9, detail_button)
            
            # UI 업데이트 (rebuild 중에는 스킵)
            if update_ui:
                # 버튼 상태 업데이트
                self.update_delete_button_state()
                
                # 상태 표시 업데이트
                self.update_status_display()
                
        except Exception as e:
            logger.error(f"테이블 행 추가 실패: row {table.rowCount()}, device {device_type}: {e}")
            raise

    def show_bid_details(self, keyword: str, result, device_type: str):
        """입찰가 상세 정보 표시 - 개선된 다이얼로그 사용"""
        self.show_bid_details_improved(keyword, result, device_type)
    
    def update_delete_button_state(self):
        """삭제 버튼 상태 업데이트 및 헤더 체크박스 상태 업데이트"""
        # 모바일 테이블 체크 상태 확인 (ModernTableWidget API 사용)
        mobile_checked_rows = self.mobile_table.get_checked_rows()
        mobile_checked_count = len(mobile_checked_rows)
        mobile_has_checked = mobile_checked_count > 0
        
        # PC 테이블 체크 상태 확인 (ModernTableWidget API 사용)
        pc_checked_rows = self.pc_table.get_checked_rows()
        pc_checked_count = len(pc_checked_rows)
        pc_has_checked = pc_checked_count > 0
                
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
        mobile_total_rows = self.mobile_table.rowCount()
        pc_total_rows = self.pc_table.rowCount()
        has_data = mobile_total_rows > 0 or pc_total_rows > 0
        self.clear_button.setEnabled(has_data)
    
    def update_history_button_state(self):
        """히스토리 버튼 상태 업데이트 (ModernTableWidget API 사용)"""
        selected_count = self.history_table.get_selected_count()
        
        # 삭제 및 내보내기 버튼: 1개 이상 선택시 활성화
        has_selection = selected_count > 0
        self.delete_history_button.setEnabled(has_selection)
        self.export_selected_history_button.setEnabled(has_selection)
        
        # 보기 버튼: 정확히 1개만 선택시 활성화
        self.view_history_button.setEnabled(selected_count == 1)
        
        # 버튼 텍스트 업데이트
        if selected_count > 0:
            self.delete_history_button.setText(f"🗑️ 선택 삭제 ({selected_count})")
            self.export_selected_history_button.setText(f"💾 선택 저장 ({selected_count})")
        else:
            self.delete_history_button.setText("🗑️ 선택 삭제")
            self.export_selected_history_button.setText("💾 선택 저장")
        
        # 보기 버튼은 항상 기본 텍스트
        self.view_history_button.setText("👀 보기")

    def update_status_display(self):
        """상태 표시 업데이트"""
        # 키워드 개수 업데이트 로직 (필요시 구현)
        pass

    
    
    
    def refresh_history_list(self):
        """히스토리 목록 새로고침"""
        try:
            # Service를 통한 히스토리 조회 (UI → Service 위임)
            sessions = powerlink_service.get_analysis_history_sessions()
            
            if not hasattr(self, 'history_table') or self.history_table is None:
                logger.error("history_table이 초기화되지 않음")
                return
                
            # ModernTableWidget 사용: 기존 데이터 클리어
            self.history_table.clear_table()
            
            for session in sessions:
                # 생성일시 (한국시간으로 변환)
                created_at = session['created_at']
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)
                
                # UTC에서 한국시간(KST, UTC+9)으로 변환
                from datetime import timedelta
                kst_time = created_at + timedelta(hours=9)
                
                # ModernTableWidget.add_row_with_data 사용
                row_index = self.history_table.add_row_with_data([
                    session['session_name'],
                    kst_time.strftime('%Y-%m-%d %H:%M:%S'),
                    str(session['keyword_count'])
                ])
                
                # 세션 ID를 세션명 아이템에 저장
                session_name_item = self.history_table.item(row_index, 1)
                if session_name_item:
                    session_name_item.setData(Qt.UserRole, session['id'])
                
            log_manager.add_log(f"PowerLink 히스토리 새로고침: {len(sessions)}개 세션", "info")
            
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 새로고침 실패: {e}", "error")
    
    def delete_selected_history(self):
        """선택된 히스토리 삭제"""
        try:
            # 선택된 세션 ID 목록 가져오기 (ModernTableWidget API 사용)
            selected_sessions = []
            for row in self.history_table.get_checked_rows():
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
                icon="🗑️"
            )
            
            if dialog.exec() == ModernConfirmDialog.Accepted:
                # 선택된 세션들의 session_id 추출
                session_ids_to_delete = []
                
                for row, session_name in selected_sessions:
                    # 테이블에서 session_id 가져오기 (UserRole로 저장된 데이터)
                    date_item = self.history_table.item(row, 1)  # 날짜 열
                    if date_item:
                        session_id = date_item.data(Qt.UserRole)
                        if session_id:
                            session_ids_to_delete.append(session_id)
                
                # Service를 통한 세션 삭제 (UI → Service 위임)
                if session_ids_to_delete:
                    success = powerlink_service.delete_analysis_history_sessions(session_ids_to_delete)
                    if success:
                        # 히스토리 새로고침
                        self.refresh_history_list()
                else:
                    log_manager.add_log("PowerLink 히스토리 삭제 실패: session_id를 찾을 수 없음", "warning")
                
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 삭제 실패: {e}", "error")
    
    def view_selected_history(self):
        """선택된 히스토리 보기 - 모바일/PC 분석 탭에 다시 로드 (ModernTableWidget API 사용)"""
        try:
            # ModernTableWidget API를 사용하여 선택된 행 확인
            selected_rows = self.history_table.get_checked_rows()
            
            if len(selected_rows) != 1:
                from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
                if len(selected_rows) == 0:
                    ModernInfoDialog.warning(self, "선택 없음", "보려는 기록을 선택해주세요.")
                else:
                    ModernInfoDialog.warning(self, "선택 오류", "하나의 기록만 선택해주세요.")
                return
            
            # 선택된 행의 세션 데이터 가져오기
            row = selected_rows[0]
            session_name_item = self.history_table.item(row, 1)
            
            if not session_name_item:
                from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
                ModernInfoDialog.warning(self, "데이터 오류", "선택된 기록의 데이터를 찾을 수 없습니다.")
                return
            
            selected_session_id = session_name_item.data(Qt.UserRole)
            selected_session_name = session_name_item.text()
            
            if not selected_session_id:
                from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
                ModernInfoDialog.warning(self, "데이터 오류", "세션 ID를 찾을 수 없습니다.")
                return
            
            # service를 통해 히스토리 세션 데이터 로드
            loaded_keywords_data = powerlink_service.load_history_session_data(selected_session_id)
            
            if not loaded_keywords_data:
                log_manager.add_log(f"PowerLink 히스토리 로드 실패: 키워드 데이터 없음 - {selected_session_name}", "error")
                return
            
            # 기존 데이터 초기화 및 새 데이터 설정 (서비스 통해)
            self.keywords_data.clear()
            powerlink_service.clear_all_keywords()
            
            # 새 데이터 설정
            self.keywords_data = loaded_keywords_data
            powerlink_service.set_keywords_data(loaded_keywords_data)
            
            # 히스토리에서 로드된 데이터임을 표시 (중복 저장 방지)
            self.is_loaded_from_history = True
            self.loaded_session_id = selected_session_id
            
            # 테이블 갱신 (직접 호출로 확실히 업데이트)
            self.update_all_tables()
            self.update_save_button_state()
            
            # 모바일 분석 탭으로 자동 이동
            self.tab_widget.setCurrentIndex(0)  # 모바일 분석 탭
            
            # 성공 메시지 표시
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.success(
                self, 
                "기록 로드 완료", 
                f"'{selected_session_name}' 세션이 현재 분석으로 로드되었습니다.\n\n📊 {len(loaded_keywords_data)}개 키워드\n📱 모바일/PC 탭에서 확인하실 수 있습니다."
            )
            
            log_manager.add_log(f"PowerLink 히스토리 로드 완료: {selected_session_name} ({len(loaded_keywords_data)}개 키워드)", "info")
                
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 보기 실패: {e}", "error")
    
    def export_selected_history(self):
        """선택된 히스토리 엑셀 내보내기 (UI 로직만)"""
        try:
            # 선택된 세션 정보 가져오기 (ModernTableWidget API 사용)
            selected_sessions = []
            for row in self.history_table.get_checked_rows():
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
            
            # service에 위임 (오케스트레이션 + adapters 파일 I/O)
            reference_widget = getattr(self, 'export_selected_history_button', None)
            powerlink_service.export_selected_history_with_dialog(
                sessions_data=selected_sessions,
                parent_widget=self,
                reference_widget=reference_widget
            )
            
        except Exception as e:
            log_manager.add_log(f"PowerLink 히스토리 내보내기 UI 처리 실패: {e}", "error")
    
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
    
    # Legacy header checkbox methods removed - ModernTableWidget handles automatically
    
    
    
    
    
    
    
    
    def update_history_button_states(self):
        """히스토리 관련 버튼 상태 업데이트"""
        try:
            selected_count = 0
            for row in range(self.history_table.rowCount()):
                checkbox_item = self.history_table.item(row, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
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
            # self.keywords_data와 서비스 키워드 둘 다 확인
            local_count = len(self.keywords_data) if hasattr(self, 'keywords_data') else 0
            service_count = len(powerlink_service.get_all_keywords())
            has_data = max(local_count, service_count) > 0
            
            self.save_analysis_button.setEnabled(has_data)
            self.clear_button.setEnabled(has_data)
            
            # 간단한 텍스트로 고정 (카운트 제거)
            self.save_analysis_button.setText("💾 현재 분석 저장")
                
        except Exception as e:
            logger.error(f"저장 버튼 상태 업데이트 실패: {e}")
    
    def on_analysis_started(self):
        """분석 시작 시 저장 버튼 비활성화"""
        # 새로운 분석 시작 시 히스토리 플래그 초기화
        self.is_loaded_from_history = False
        if hasattr(self, 'loaded_session_id'):
            delattr(self, 'loaded_session_id')
        
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
        """현재 분석 결과 저장 - service 위임"""
        try:
            # 히스토리에서 로드된 데이터인지 확인
            if hasattr(self, 'is_loaded_from_history') and self.is_loaded_from_history:
                from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
                dialog = ModernConfirmDialog(
                    self,
                    "저장 불가",
                    "이미 저장된 히스토리 데이터입니다.\n\n새로운 분석을 실행한 후 저장해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # service를 통해 저장 처리
            success, session_id, session_name, is_duplicate = powerlink_service.save_current_analysis_to_db()
            
            if not success:
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
            
            # 키워드 개수 가져오기
            keyword_count = len(powerlink_service.get_all_keywords())
            
            # 저장 다이얼로그 표시
            save_dialog = PowerLinkSaveDialog(
                session_id=session_id,
                session_name=session_name,
                keyword_count=keyword_count,
                is_duplicate=is_duplicate,
                parent=self
            )
            save_dialog.exec()
            
            # 저장이 성공했고 중복이 아닌 경우에만 히스토리 새로고침
            if not is_duplicate:
                self.refresh_history_list()
            
        except Exception as e:
            logger.error(f"PowerLink 분석 세션 저장 실패: {e}")
            log_manager.add_log(f"PowerLink 분석 세션 저장 실패: {e}", "error")
    
    def clear_all_analysis(self):
        """전체 분석 결과 클리어"""
        try:
            # 데이터가 있는지 확인
            if not powerlink_service.get_all_keywords():
                return
            
            # 모던 확인 다이얼로그 (키워드분석기와 동일한 방식)
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            try:
                confirmed = ModernConfirmDialog.warning(
                    self, 
                    "분석 결과 삭제", 
                    f"모든 분석 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                    "삭제", 
                    "취소"
                )
            except:
                # fallback: 생성자 사용하여 ⚠️ 이모티콘 표시
                dialog = ModernConfirmDialog(
                    self,
                    "분석 결과 삭제",
                    f"모든 분석 데이터를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                    confirm_text="삭제",
                    cancel_text="취소",
                    icon="⚠️"
                )
                confirmed = dialog.exec()
            
            if confirmed:
                # 히스토리 플래그 초기화
                self.is_loaded_from_history = False
                if hasattr(self, 'loaded_session_id'):
                    delattr(self, 'loaded_session_id')
                
                # 메모리 데이터베이스 클리어 (안전한 클리어)
                keywords_before = len(powerlink_service.get_all_keywords())
                powerlink_service.clear_all_keywords()
                keywords_after = len(powerlink_service.get_all_keywords())
                logger.info(f"메모리 DB 클리어: {keywords_before}개 → {keywords_after}개")
                
                # 테이블 클리어 (ModernTableWidget API 사용)
                mobile_rows_before = self.mobile_table.rowCount()
                pc_rows_before = self.pc_table.rowCount()
                
                self.mobile_table.clear_table()
                self.pc_table.clear_table()
                
                mobile_rows_after = self.mobile_table.rowCount()
                pc_rows_after = self.pc_table.rowCount()
                logger.info(f"테이블 클리어: 모바일 {mobile_rows_before}→{mobile_rows_after}, PC {pc_rows_before}→{pc_rows_after}")
                
                # 버튼 상태 업데이트
                self.update_save_button_state()
                
                log_manager.add_log("PowerLink 분석 결과 전체 클리어", "success")
                
        except Exception as e:
            logger.error(f"전체 클리어 실패: {e}")
            log_manager.add_log(f"PowerLink 전체 클리어 실패: {e}", "error")
    
    
    
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
    
    def set_keywords_data(self, keywords_data):
        """키워드 데이터 설정 (교체 방식 - 히스토리 로드용)"""
        # 서비스를 통해 키워드 데이터 설정 (기존 데이터 교체)
        powerlink_service.set_keywords_data(keywords_data)
        
        # 테이블 새로고침
        self.refresh_tables_from_database()
        
        # 버튼 상태 업데이트
        self.update_save_button_state()
        self.update_delete_button_state()
    
    def add_keywords_data(self, keywords_data):
        """키워드 데이터 추가 (누적 방식 - 새로운 분석용)"""
        # 서비스를 통해 키워드 데이터 추가 (기존 데이터 유지)
        powerlink_service.add_keywords_data(keywords_data)
        
        # 테이블 새로고침
        self.refresh_tables_from_database()
        
        # 버튼 상태 업데이트
        self.update_save_button_state()
        self.update_delete_button_state()
    
    def refresh_tables_from_database(self):
        """데이터베이스에서 테이블 전체 새로고침 (ModernTableWidget API 사용)"""
        try:
            # 기존 테이블 데이터 클리어
            self.mobile_table.clear_table()
            self.pc_table.clear_table()
            
            # 서비스를 통해 모든 키워드 가져오기
            all_keywords = list(powerlink_service.get_all_keywords().values())
            
            # 테이블에 재추가 (update_mobile_table/update_pc_table과 동일한 방식)
            for result in all_keywords:
                # 모바일 테이블에 추가
                # 월검색량
                if result.mobile_search_volume >= 0:
                    mobile_search_volume = f"{result.mobile_search_volume:,}"
                else:
                    mobile_search_volume = "-"
                
                # 추천순위
                if result.mobile_recommendation_rank > 0:
                    mobile_rank_text = f"{result.mobile_recommendation_rank}위"
                else:
                    mobile_rank_text = "-"
                
                # 모바일 행 데이터 준비 (체크박스 제외)
                mobile_row_data = [
                    result.keyword,  # 키워드
                    mobile_search_volume,  # 월검색량
                    f"{result.mobile_clicks:.1f}" if result.mobile_clicks >= 0 else "-",  # 클릭수
                    f"{result.mobile_ctr:.2f}%" if result.mobile_ctr >= 0 else "-",  # 클릭률
                    f"{result.mobile_first_page_positions}위까지" if result.mobile_first_page_positions >= 0 else "-",  # 1p노출위치
                    f"{result.mobile_first_position_bid:,}원" if result.mobile_first_position_bid >= 0 else "-",  # 1등광고비
                    f"{result.mobile_min_exposure_bid:,}원" if result.mobile_min_exposure_bid >= 0 else "-",  # 최소노출가격
                    mobile_rank_text,  # 추천순위
                    "상세"  # 상세 버튼
                ]
                
                # ModernTableWidget API 사용하여 행 추가
                mobile_row = self.mobile_table.add_row_with_data(mobile_row_data, checkable=True)
                
                # 모바일 상세 버튼 추가
                mobile_detail_button = QPushButton("상세")
                mobile_detail_button.setStyleSheet("""
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
                mobile_detail_button.clicked.connect(lambda checked, k=result.keyword, r=result: self.show_bid_details(k, r, 'mobile'))
                self.mobile_table.setCellWidget(mobile_row, 9, mobile_detail_button)
                
                # PC 테이블에 추가
                # 월검색량
                if result.pc_search_volume >= 0:
                    pc_search_volume = f"{result.pc_search_volume:,}"
                else:
                    pc_search_volume = "-"
                
                # 추천순위
                if result.pc_recommendation_rank > 0:
                    pc_rank_text = f"{result.pc_recommendation_rank}위"
                else:
                    pc_rank_text = "-"
                
                # PC 행 데이터 준비 (체크박스 제외)
                pc_row_data = [
                    result.keyword,  # 키워드
                    pc_search_volume,  # 월검색량
                    f"{result.pc_clicks:.1f}" if result.pc_clicks >= 0 else "-",  # 클릭수
                    f"{result.pc_ctr:.2f}%" if result.pc_ctr >= 0 else "-",  # 클릭률
                    f"{result.pc_first_page_positions}위까지" if result.pc_first_page_positions >= 0 else "-",  # 1p노출위치
                    f"{result.pc_first_position_bid:,}원" if result.pc_first_position_bid >= 0 else "-",  # 1등광고비
                    f"{result.pc_min_exposure_bid:,}원" if result.pc_min_exposure_bid >= 0 else "-",  # 최소노출가격
                    pc_rank_text,  # 추천순위
                    "상세"  # 상세 버튼
                ]
                
                # ModernTableWidget API 사용하여 행 추가
                pc_row = self.pc_table.add_row_with_data(pc_row_data, checkable=True)
                
                # PC 상세 버튼 추가
                pc_detail_button = QPushButton("상세")
                pc_detail_button.setStyleSheet("""
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
                pc_detail_button.clicked.connect(lambda checked, k=result.keyword, r=result: self.show_bid_details(k, r, 'pc'))
                self.pc_table.setCellWidget(pc_row, 9, pc_detail_button)
            
            logger.info(f"테이블 새로고침 완료: {len(all_keywords)}개 키워드")
            
        except Exception as e:
            logger.error(f"테이블 새로고침 실패: {e}")
    
    def clear_all_tables(self):
        """모든 테이블 클리어 (전체 클리어 시 사용)"""
        try:
            self.mobile_table.setRowCount(0)
            self.pc_table.setRowCount(0)
            powerlink_service.clear_all_keywords()
            self.update_save_button_state()
            logger.info("모든 테이블 클리어 완룼")
        except Exception as e:
            logger.error(f"테이블 클리어 실패: {e}")
    
    
    def delete_selected_keywords(self, device_type: str):
        """선택된 키워드만 삭제 (실제 선택삭제)"""
        try:
            # 디바이스 타입에 따른 테이블 선택
            if device_type == 'mobile':
                table = self.mobile_table
            elif device_type == 'pc':
                table = self.pc_table
            else:
                # device_type이 지정되지 않은 경우 모든 테이블에서 수집
                table = None
            
            # 선택된 키워드 수집
            selected_keywords = []
            
            if table is not None:
                # 특정 테이블에서만 수집
                for row in table.get_checked_rows():
                    keyword_item = table.item(row, 1)  # 키워드는 1번 컬럼
                    if keyword_item:
                        keyword = keyword_item.text()
                        if keyword not in selected_keywords:
                            selected_keywords.append(keyword)
            else:
                # 모든 테이블에서 수집 (하위 호환성)
                for row in self.mobile_table.get_checked_rows():
                    keyword_item = self.mobile_table.item(row, 1)
                    if keyword_item:
                        keyword = keyword_item.text()
                        if keyword not in selected_keywords:
                            selected_keywords.append(keyword)
                
                for row in self.pc_table.get_checked_rows():
                    keyword_item = self.pc_table.item(row, 1)
                    if keyword_item:
                        keyword = keyword_item.text()
                        if keyword not in selected_keywords:
                            selected_keywords.append(keyword)
            
            if not selected_keywords:
                return
            
            # 선택삭제 확인 다이얼로그
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self,
                "키워드 삭제 확인",
                f"선택된 {len(selected_keywords)}개 키워드를 삭제하시겠습니까?",
                confirm_text="삭제",
                cancel_text="취소",
                icon="🗑️"
            )
            
            if dialog.exec() == ModernConfirmDialog.Accepted:
                # 서비스를 통해 선택된 키워드 삭제
                powerlink_service.remove_keywords(selected_keywords)
                
                # 테이블 전체 재구성 (남은 키워드들로)
                self.update_all_tables()
                
                # UI 상태 업데이트
                self.update_delete_button_state()
                self.update_save_button_state()
                
                # 성공 메시지
                log_manager.add_log(f"PowerLink 선택된 {len(selected_keywords)}개 키워드 삭제 완료", "success")
                
        except Exception as e:
            logger.error(f"키워드 삭제 실패: {e}")
            log_manager.add_log(f"PowerLink 키워드 삭제 실패: {e}", "error")
    
    
    def _update_rankings_in_tables(self):
        """테이블의 추천순위 컬럼만 업데이트 (전체 새로고침 없이)"""
        try:
            # 모바일 테이블 순위 업데이트
            for row in range(self.mobile_table.rowCount()):
                keyword_item = self.mobile_table.item(row, 1)  # 키워드는 1번 컬럼
                if keyword_item:
                    keyword = keyword_item.text()
                    result = powerlink_service.get_all_keywords().get(keyword)
                    if result:
                        # 추천순위 업데이트 (8번 컬럼)
                        rank_text = f"{result.mobile_recommendation_rank}위" if result.mobile_recommendation_rank > 0 else "-"
                        rank_item = self.mobile_table.item(row, 8)
                        if rank_item:
                            rank_item.setText(rank_text)
            
            # PC 테이블 순위 업데이트
            for row in range(self.pc_table.rowCount()):
                keyword_item = self.pc_table.item(row, 1)  # 키워드는 1번 컬럼
                if keyword_item:
                    keyword = keyword_item.text()
                    result = powerlink_service.get_all_keywords().get(keyword)
                    if result:
                        # 추천순위 업데이트 (8번 컬럼)
                        rank_text = f"{result.pc_recommendation_rank}위" if result.pc_recommendation_rank > 0 else "-"
                        rank_item = self.pc_table.item(row, 8)
                        if rank_item:
                            rank_item.setText(rank_text)
                            
        except Exception as e:
            logger.error(f"순위 업데이트 실패: {e}")
    
    


    def show_bid_details_improved(self, keyword: str, result, device_type: str):
        """순위별 입찰가 상세 다이얼로그 표시 (개선된 버전)"""
        try:
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
            dialog = QDialog(self)
            dialog.setWindowTitle("입찰가 상세 정보")
            dialog.setModal(True)
            dialog.resize(420, 480)
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {ModernStyle.COLORS['bg_primary']};
                }}
            """)
            
            # 메인 레이아웃
            layout = QVBoxLayout()
            layout.setSpacing(16)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 심플한 헤더
            header_layout = QVBoxLayout()
            header_layout.setSpacing(4)
            
            # 키워드 이름 (심플하게)
            keyword_label = QLabel(keyword)
            keyword_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: 600;
                    color: {ModernStyle.COLORS['text_primary']};
                    margin: 0;
                }}
            """)
            
            # 디바이스 타입 (이모지 제거)
            device_label = QLabel(f"{device_type.upper()} 순위별 입찰가")
            device_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 13px;
                    font-weight: 400;
                    color: {ModernStyle.COLORS['text_secondary']};
                    margin: 0;
                }}
            """)
            
            header_layout.addWidget(keyword_label)
            header_layout.addWidget(device_label)
            layout.addLayout(header_layout)
            
            # 테이블 생성 (심플한 스타일)
            table = QTableWidget()
            table.setRowCount(len(bid_positions))
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["순위", "입찰가"])
            
            # 미니멀한 테이블 스타일
            table.setStyleSheet(f"""
                QTableWidget {{
                    gridline-color: {ModernStyle.COLORS['border']};
                    background-color: {ModernStyle.COLORS['bg_card']};
                    selection-background-color: {ModernStyle.COLORS['primary']};
                    selection-color: white;
                    border: 1px solid {ModernStyle.COLORS['border']};
                    border-radius: 6px;
                    font-size: 14px;
                }}
                QTableWidget::item {{
                    padding: 12px 10px;
                    border-bottom: 1px solid {ModernStyle.COLORS['border']};
                    color: {ModernStyle.COLORS['text_primary']};
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
                    border-bottom: 1px solid {ModernStyle.COLORS['border']};
                    font-weight: 500;
                    font-size: 13px;
                }}
            """)
            
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setStretchLastSection(True)
            table.setAlternatingRowColors(False)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setShowGrid(False)
            
            # 컬럼 크기 설정
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Fixed)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.resizeSection(0, 80)  # 순위 컬럼 너비
            
            # 데이터 추가 (심플한 포맷)
            for row, bid_pos in enumerate(bid_positions):
                rank_item = QTableWidgetItem(f"{bid_pos.position}위")
                rank_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 0, rank_item)
                
                price_item = QTableWidgetItem(format_price_krw(bid_pos.bid_price))
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, 1, price_item)
            
            layout.addWidget(table)
            
            # 확인 버튼 (미니멀하게)
            from src.toolbox.ui_kit.components import ModernButton
            confirm_button = ModernButton("확인", "primary")
            confirm_button.clicked.connect(dialog.accept)
            confirm_button.setMinimumHeight(36)
            
            button_layout = QHBoxLayout()
            button_layout.setContentsMargins(0, 12, 0, 0)
            button_layout.addStretch()
            button_layout.addWidget(confirm_button)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            print(f"상세 다이얼로그 표시 오류: {e}")
            # 에러 다이얼로그 표시
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.error(self, "오류", f"상세 정보를 표시할 수 없습니다: {e}")
    
