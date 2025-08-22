"""
순위 테이블 위젯 - 키워드 순위 관리 및 표시
기존 UI와 완전 동일한 스타일 및 기능
"""
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QApplication, QTableWidgetItem, QCheckBox, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.modern_table import ModernTableWidget
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernDangerButton, ModernSuccessButton, ModernCancelButton
from src.desktop.common_log import log_manager
from src.toolbox.ui_kit import ModernTextInputDialog
from src.foundation.logging import get_logger

from .worker import RankingCheckWorker, ranking_worker_manager, keyword_info_worker_manager
from .adapters import format_date, format_date_with_time, format_rank_display, get_rank_color, format_monthly_volume, get_category_match_color
from .service import rank_tracking_service
# view_model은 service로 통합됨

logger = get_logger("features.rank_tracking.ranking_table_widget")


class AddKeywordsDialog(QDialog):
    """키워드 추가 다이얼로그 (원본과 완전 동일)"""
    
    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("키워드 추가")
        self.setModal(True)
        self.setMinimumSize(560, 520)
        self.resize(560, 520)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 25, 30, 30)
        main_layout.setSpacing(20)
        
        # 헤더
        header_label = QLabel("📝 키워드 추가")
        header_label.setStyleSheet("""
            QLabel {
                color: #2563eb;
                font-size: 20px;
                font-weight: bold;
                padding: 0 0 5px 0;
                margin: 0;
            }
        """)
        main_layout.addWidget(header_label)
        
        # 설명
        self.description_label = QLabel("추적할 키워드를 입력하세요")
        self.description_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 14px;
                margin: 0 0 10px 0;
            }
        """)
        main_layout.addWidget(self.description_label)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                color: #e2e8f0;
                background-color: #e2e8f0;
                border: none;
                height: 1px;
            }
        """)
        main_layout.addWidget(separator)
        
        # 입력 라벨
        input_label = QLabel("키워드 목록")
        input_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 13px;
                font-weight: 600;
                margin: 5px 0;
            }
        """)
        main_layout.addWidget(input_label)
        
        # 키워드 입력 필드
        self.keywords_input = QTextEdit()
        self.keywords_input.setPlaceholderText("예:\n강아지 사료\n고양이 간식\n반려동물 장난감\n\n또는 쉼표로 구분: 강아지 사료, 고양이 간식, 반려동물 장난감")
        self.keywords_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                background-color: #ffffff;
                color: #1e293b;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #2563eb;
                outline: none;
            }
        """)
        self.keywords_input.setMinimumHeight(160)
        self.keywords_input.setMaximumHeight(160)
        main_layout.addWidget(self.keywords_input)
        
        # 안내 텍스트
        help_label = QLabel("ℹ️ 각 줄에 하나씩 입력하거나 쉼표(,)로 구분해서 입력하세요")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                line-height: 1.4;
                padding: 8px 12px;
                background-color: #f1f5f9;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
                margin: 5px 0 10px 0;
            }
        """)
        main_layout.addWidget(help_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("추가")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 포커스 설정
        self.keywords_input.setFocus()
    
    def get_keywords(self):
        """입력된 키워드들을 파싱해서 리스트로 반환"""
        text = self.keywords_input.toPlainText().strip()
        if not text:
            return []
        
        keywords = []
        
        # 쉼표로 구분된 경우와 줄 바꿈으로 구분된 경우 모두 처리
        if ',' in text:
            # 쉼표로 구분된 경우
            for keyword in text.split(','):
                keyword = keyword.strip()
                if keyword:
                    keywords.append(keyword)
        else:
            # 줄 바꿈으로 구분된 경우
            for line in text.split('\n'):
                keyword = line.strip()
                if keyword:
                    keywords.append(keyword)
        
        # 중복 제거하면서 순서 유지 + 영어 대문자 변환
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            # 영어는 대문자로 변환, 한글은 그대로 유지
            processed_keyword = ""
            for char in keyword:
                if char.isalpha() and char.isascii():  # 영문자만 대문자 변환
                    processed_keyword += char.upper()
                else:
                    processed_keyword += char
            
            normalized = processed_keyword.upper().replace(' ', '')
            if normalized not in seen:
                seen.add(normalized)
                unique_keywords.append(processed_keyword)  # 처리된 키워드 저장
        
        return unique_keywords


class RankingTableWidget(QWidget):
    """순위 테이블 위젯 - 기존과 완전 동일"""
    
    project_updated = Signal()  # 프로젝트 업데이트 시그널
    
    def __init__(self):
        super().__init__()
        self.current_project_id = None
        self.current_project = None
        self.selected_projects = []  # 다중 선택된 프로젝트들
        self.setup_ui()
        
        # 워커 매니저 시그널 연결
        ranking_worker_manager.progress_updated.connect(self.on_progress_updated)
        ranking_worker_manager.keyword_rank_updated.connect(self.on_keyword_rank_updated)
        ranking_worker_manager.ranking_finished.connect(self.on_ranking_finished)
        
        # 키워드 정보 워커 매니저 시그널 연결
        keyword_info_worker_manager.progress_updated.connect(self.on_keyword_info_progress_updated)
        keyword_info_worker_manager.category_updated.connect(self.on_keyword_category_updated)
        keyword_info_worker_manager.volume_updated.connect(self.on_keyword_volume_updated)
        keyword_info_worker_manager.keyword_info_finished.connect(self.on_keyword_info_finished)
    
    def setup_ui(self):
        """UI 구성 - 원본과 완전 동일"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        
        # 테이블 상단 버튼들
        button_layout = QHBoxLayout()
        
        # 키워드 삭제 버튼
        self.delete_keywords_button = ModernDangerButton("🗑️ 선택 삭제")
        self.delete_keywords_button.clicked.connect(self.delete_selected_keywords)
        self.delete_keywords_button.setEnabled(False)
        button_layout.addWidget(self.delete_keywords_button)
        
        # 진행상황 표시를 버튼 옆에 배치 (원본과 동일)
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        progress_layout = QHBoxLayout()  # 가로 배치로 변경
        progress_layout.setContentsMargins(5, 5, 5, 5)  # 여백 최소화
        progress_layout.setSpacing(8)  # 간격을 8px로 줄임
        
        from PySide6.QtWidgets import QProgressBar, QSizePolicy
        
        self.progress_label = QLabel("작업 진행 중...")
        self.progress_label.setFont(QFont("맑은 고딕", 10))  # 폰트 크기 줄임
        self.progress_label.setStyleSheet("color: #007ACC; font-weight: 500;")
        self.progress_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 고정
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(16)  # 높이 제한
        self.progress_bar.setFixedWidth(150)  # 폭 제한
        self.progress_bar.setVisible(False)  # 단계 진행시에만 표시
        self.progress_bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 크기 고정
        progress_layout.addWidget(self.progress_bar)
        
        progress_layout.addStretch()  # 오른쪽에 늘어나는 공간 추가
        
        self.progress_frame.setLayout(progress_layout)
        button_layout.addWidget(self.progress_frame)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 순위 테이블 (공용 ModernTableWidget 사용)
        self.ranking_table = ModernTableWidget(
            columns=["키워드", "카테고리", "월검색량"],
            has_checkboxes=True,
            has_header_checkbox=True
        )
        self.setup_ranking_table()
        layout.addWidget(self.ranking_table)
        
        # 하단 버튼들
        self.setup_buttons(layout)
        
        self.setLayout(layout)
        
        # 강제 새로고침 메서드 추가 (update_ranking_table로 대체)
        self.force_refresh_ranking_table = self.update_ranking_table
        self.rebuild_ranking_table = self.update_ranking_table
    
    
    
    def setup_ranking_table(self):
        """순위 테이블 설정 (공용 ModernTableWidget 사용)"""
        # 헤더 우클릭 메뉴 설정 (날짜 컬럼 삭제용)
        self.ranking_table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.ranking_table.horizontalHeader().customContextMenuRequested.connect(self.show_header_context_menu)
        
        # 컬럼 너비 설정 (체크박스 컬럼은 자동 처리됨)
        self.ranking_table.setColumnWidth(1, 200)      # 키워드
        self.ranking_table.setColumnWidth(2, 180)      # 카테고리  
        self.ranking_table.setColumnWidth(3, 100)      # 월검색량
        
        # 공용 테이블 시그널 연결
        self.ranking_table.selection_changed.connect(self.on_selection_changed)
        
    def on_selection_changed(self):
        """선택 상태 변경 처리"""
        # 선택된 항목 수 가져오기
        selected_count = self.ranking_table.get_selected_count()
        
        # 삭제 버튼 상태 및 텍스트 업데이트
        if selected_count > 0:
            self.delete_keywords_button.setEnabled(True)
            self.delete_keywords_button.setText(f"🗑️ 선택 삭제 ({selected_count}개)")
        else:
            self.delete_keywords_button.setEnabled(False)
            self.delete_keywords_button.setText("🗑️ 선택 삭제")
    
    def show_header_context_menu(self, position):
        """헤더 우클릭 컨텍스트 메뉴 표시"""
        if not self.current_project:
            return
            
        header = self.ranking_table.horizontalHeader()
        column = header.logicalIndexAt(position)
        
        # 날짜 컬럼인지 확인 (컬럼 3번 이후가 날짜 컬럼)
        # 0: 체크박스(자동), 1: 키워드, 2: 카테고리, 3: 월검색량
        if column < 4:  # 체크박스, 키워드, 카테고리, 월검색량 컬럼은 제외
            return
            
        # 헤더 텍스트에서 날짜 추출
        header_item = self.ranking_table.horizontalHeaderItem(column)
        if header_item:
            column_text = header_item.text()
            if not column_text or column_text == "-":
                return
                
            # 컨텍스트 메뉴 생성
            from PySide6.QtWidgets import QMenu
            
            context_menu = QMenu(self)
            delete_action = context_menu.addAction(f"🗑️ {column_text} 날짜 데이터 삭제")
            delete_action.triggered.connect(lambda: self.delete_date_column_data(column, column_text))
            
            # 메뉴 표시
            global_pos = header.mapToGlobal(position)
            context_menu.exec(global_pos)
    
    def delete_date_column_data(self, column_index: int, date_text: str):
        """날짜 컬럼 데이터 삭제"""
        if not self.current_project:
            return
            
        from src.toolbox.ui_kit import ModernConfirmDialog
        
        # 확인 다이얼로그
        reply = ModernConfirmDialog.warning(
            self,
            "날짜 데이터 삭제",
            f"{date_text} 날짜의 모든 순위 데이터를 삭제하시겠습니까?\n\n• 해당 날짜 컬럼이 테이블에서 제거됩니다\n• 이 작업은 되돌릴 수 없습니다",
            "삭제", "취소"
        )
        
        if reply:
            try:
                # ViewModel을 통한 프로젝트 개요 조회
                overview = rank_tracking_service.get_project_overview(self.current_project_id)
                dates = overview.get('dates', []) if overview else []
                
                # 헤더 인덱스에 맞는 날짜 찾기 (컬럼 4번부터 날짜)
                date_index = column_index - 4  # 컬럼 0,1,2,3은 체크박스(자동), 키워드, 카테고리, 월검색량
                if 0 <= date_index < len(dates):
                    actual_date = dates[date_index]
                    logger.info(f"삭제할 실제 날짜: '{actual_date}'")
                    
                    # ViewModel을 통한 데이터베이스 삭제
                    success = rank_tracking_service.delete_ranking_data_by_date(self.current_project_id, actual_date)
                    
                    if success:
                        log_manager.add_log(f"✅ {date_text} 날짜의 순위 데이터가 삭제되었습니다.", "success")
                        
                        # 해당 컬럼을 테이블에서 제거
                        # 모든 행의 해당 컬럼 데이터 제거
                        for i in range(self.ranking_table.topLevelItemCount()):
                            item = self.ranking_table.topLevelItem(i)
                            if item:
                                # 해당 컬럼의 데이터를 지우고 왼쪽으로 당기기
                                for col in range(column_index, self.ranking_table.columnCount() - 1):
                                    next_text = item.text(col + 1)
                                    next_data = item.data(col + 1, Qt.UserRole)
                                    next_color = item.foreground(col + 1)
                                    
                                    item.setText(col, next_text)
                                    item.setData(col, Qt.UserRole, next_data)
                                    item.setForeground(col, next_color)
                        
                        # 헤더도 왼쪽으로 당기기
                        for col in range(column_index, self.ranking_table.columnCount() - 1):
                            next_header = self.ranking_table.headerItem().text(col + 1)
                            self.ranking_table.headerItem().setText(col, next_header)
                        
                        # 마지막 컬럼 제거
                        self.ranking_table.setColumnCount(self.ranking_table.columnCount() - 1)
                        
                        # 테이블 업데이트
                        self.ranking_table.viewport().update()
                        self.ranking_table.repaint()
                    else:
                        log_manager.add_log(f"❌ {date_text} 날짜의 순위 데이터 삭제에 실패했습니다.", "error")
                        QMessageBox.information(self, "삭제 실패", "데이터베이스에서 해당 날짜의 데이터를 찾을 수 없거나 삭제에 실패했습니다.")
                else:
                    QMessageBox.information(self, "오류", "날짜 데이터를 찾을 수 없습니다.")
                    
            except Exception as e:
                log_manager.add_log(f"❌ 날짜 데이터 삭제 중 오류: {str(e)}", "error")
                QMessageBox.information(self, "오류", f"날짜 데이터 삭제 중 오류가 발생했습니다: {str(e)}")
    
    
    def set_project(self, project):
        """프로젝트 설정"""
        logger.info(f"🔧 프로젝트 설정: ID={project.id}, 이름={getattr(project, 'current_name', 'N/A')}")
        logger.info(f"   - 프로젝트 카테고리: '{getattr(project, 'category', 'N/A')}'")
        
        # ViewModel에 현재 프로젝트 설정
        if project:
            self.current_project = project
            self.current_project_id = project.id
            self.update_project_info(project.id)
            logger.info(f"✅ 프로젝트 설정 완료: current_project_id={self.current_project_id}")
        else:
            logger.error(f"프로젝트 설정 실패: {project.id}")
        
        # 버튼 활성화 및 상태 업데이트
        if hasattr(self, 'add_keyword_button'):
            self.add_keyword_button.setEnabled(True)
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(True)
        
        # 순위 확인 버튼 상태는 해당 프로젝트의 실행 상태에 따라 결정
        self.update_button_state_from_project_status(project.id)
        
        # 진행률 표시 상태도 프로젝트에 따라 업데이트
        self.update_progress_display_from_project_status(project.id)
    
    def update_button_state_from_project_status(self, project_id):
        """프로젝트 상태에 따른 버튼 상태 업데이트"""
        if hasattr(self, 'check_button') and hasattr(self, 'stop_button'):
            is_running = rank_tracking_service.is_ranking_in_progress(project_id)
            self.update_button_state_for_current_project(running=is_running)
            logger.info(f"프로젝트 {project_id} 버튼 상태 복원: 순위 확인 {'진행중' if is_running else '대기중'}")
    
    def update_progress_display_from_project_status(self, project_id):
        """프로젝트 상태에 따른 진행률 표시 업데이트"""
        logger.info(f"프로젝트 {project_id} 진행률 표시 업데이트 확인")
        
        current, total = rank_tracking_service.get_ranking_progress(project_id)
        if current > 0 and total > 0:
            self.show_progress(f"순위 확인 중... ({current}/{total})", show_bar=True)
            percentage = int((current / total) * 100) if total > 0 else 0
            self.progress_bar.setValue(percentage)
            logger.info(f"✅ 프로젝트 {project_id} 진행률 복원: {current}/{total} ({percentage}%)")
        else:
            self.hide_progress()
            logger.info(f"프로젝트 {project_id} 진행률 없음 - 진행률바 숨김")
    
    def clear_project(self):
        """프로젝트 초기화 - 삭제 시 호출"""
        # 프로젝트 정보 초기화
        self.current_project = None
        self.current_project_id = None
        
        # 테이블 초기화
        if hasattr(self, 'ranking_table'):
            self.ranking_table.clear()
        
        # 모든 버튼 비활성화
        if hasattr(self, 'add_keyword_button'):
            self.add_keyword_button.setEnabled(False)
        if hasattr(self, 'check_button'):
            self.check_button.setEnabled(False)
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(False)
        if hasattr(self, 'delete_keywords_button'):
            self.delete_keywords_button.setEnabled(False)
        
        # 진행 상태 숨기기
        if hasattr(self, 'progress_frame'):
            self.progress_frame.setVisible(False)
    
    def update_project_info(self, project_id: int):
        """프로젝트 정보 업데이트 - 키워드 테이블만"""
        self.current_project_id = project_id
        
        # 프로젝트 정보 조회
        project = rank_tracking_service.get_project_by_id(project_id)
        if project:
            self.current_project = project
        
        # 순위 현황 표시
        self.update_ranking_table(project_id)
    
    def update_ranking_table(self, project_id):
        """순위 테이블 업데이트 (진행 중인 순위 확인 상태 고려)"""
        try:
            # 현재 프로젝트에서 순위 확인이 진행 중인지 확인
            is_ranking_in_progress = ranking_worker_manager.is_ranking_in_progress(project_id)
            
            # 진행 중인 경우 진행률 상태만 복원하고 테이블은 정상 구성
            if is_ranking_in_progress:
                logger.info(f"프로젝트 {project_id}: 순위 확인 진행 중 - 진행 상태 복원하고 테이블 구성")
                self.update_progress_display_from_project_status(project_id)
            
            # ViewModel에서 테이블 데이터 준비
            table_data = rank_tracking_service.prepare_table_data(project_id)
            if not table_data.get("success", False):
                logger.error(f"테이블 데이터 준비 실패: {table_data.get('message')}")
                return
            
            # ViewModel에서 준비된 데이터 사용
            headers = table_data["headers"]
            keywords_data = table_data["overview"].get("keywords", {}) if table_data["overview"] else {}
            dates = table_data["dates"]
            project_category_base = table_data["project_category_base"]
            
            # 키워드 데이터가 없으면 직접 키워드 목록에서 가져오기
            if not keywords_data:
                keywords = table_data["keywords"]
                for keyword in keywords:
                    keywords_data[keyword.id] = {
                        'keyword': keyword.keyword,
                        'category': keyword.category or '-',
                        'monthly_volume': keyword.monthly_volume if keyword.monthly_volume is not None else -1,
                        'search_volume': getattr(keyword, 'search_volume', None),
                        'is_active': True,
                        'rankings': {}
                    }
            
            # 날짜 정보는 이미 ViewModel에서 처리됨
            all_dates = dates
            
            # 현재 진행 중인 순위 확인이 있다면 해당 시간도 포함 (기존 로직 유지)
            current_time = ranking_worker_manager.get_current_time(project_id)
            if current_time and current_time not in all_dates:
                all_dates = [current_time] + all_dates
                # 헤더도 다시 업데이트 필요
                headers = table_data["headers"][:4]  # 기본 4개 헤더
                for date in all_dates:
                    headers.append(format_date(date))
                
            # 마지막 확인 시간 표시 (ViewModel에서 준비됨)
            if hasattr(self, 'last_check_label'):
                self.last_check_label.setText(table_data["last_check_time"])
            
            # 테이블 완전 초기화 및 헤더 설정
            self.ranking_table.clear_table()
            
            # 동적으로 날짜 컬럼 추가 (체크박스 제외한 기본 3개 + 날짜들)
            date_headers = headers[3:]  # 키워드, 카테고리, 월검색량 뒤의 날짜들
            for date_header in date_headers:
                self.ranking_table.insertColumn(self.ranking_table.columnCount())
                self.ranking_table.setHorizontalHeaderItem(
                    self.ranking_table.columnCount() - 1, 
                    QTableWidgetItem(date_header)
                )
            
            # 헤더 체크박스는 ModernTableWidget에서 자동 처리됨
            
            # 키워드가 없어도 헤더는 표시됨
            if not keywords_data:
                return
            
            # 키워드별 행 추가
            for keyword_id, data in keywords_data.items():
                keyword = data['keyword']
                is_active = data.get('is_active', True)  # 기본값 True로 설정
                rankings = data.get('rankings', {})
                
                # ModernTableWidget용 데이터 준비 (체크박스 컬럼 제외)
                row_data = [keyword]  # 키워드
                
                # 카테고리 추가
                category = data.get('category', '') or '-'
                row_data.append(category)
                
                # 월검색량
                search_vol = data.get('search_volume')
                monthly_vol = data.get('monthly_volume', -1)
                volume = search_vol or monthly_vol
                
                # 월검색량 포맷팅
                if volume == -1:
                    volume_text = "-"  # 아직 API 호출 안됨 (UI에서는 "-"으로 표시)
                else:
                    volume_text = format_monthly_volume(volume)
                row_data.append(volume_text)
                
                # 날짜별 순위 추가 (진행 중인 날짜 포함)
                for date in all_dates:
                    # 진행 중인 날짜인 경우 임시 저장된 순위 데이터 확인
                    current_time = ranking_worker_manager.get_current_time(project_id)
                    if date == current_time:
                        current_rankings = ranking_worker_manager.get_current_rankings(project_id)
                        if keyword_id in current_rankings:
                            rank = current_rankings[keyword_id]
                            rank_display = format_rank_display(rank)
                            row_data.append(rank_display)
                        else:
                            row_data.append("-")
                    else:
                        # 저장된 순위 데이터 확인
                        rank_data = rankings.get(date)
                        if rank_data and rank_data.get('rank') is not None:
                            rank_display = format_rank_display(rank_data['rank'])
                            row_data.append(rank_display)
                        else:
                            row_data.append("-")
                
                # ModernTableWidget에 행 추가
                row = self.ranking_table.add_row_with_data(row_data, checkable=True)
                
                # 키워드 ID를 키워드 컬럼에 저장 (삭제 시 사용)
                keyword_item = self.ranking_table.item(row, 1)  # 키워드 컬럼
                if keyword_item:
                    keyword_item.setData(Qt.UserRole, keyword_id)
                
                # 색깔 적용: 순위별, 카테고리별
                for i, date in enumerate(all_dates):
                    column_index = 3 + i  # 0:체크박스, 1:키워드, 2:카테고리, 3+:순위
                    rank_item = self.ranking_table.item(row, column_index)
                    if rank_item:
                        rank_text = rank_item.text()
                        if rank_text != "-":
                            try:
                                actual_rank = int(rank_text.replace("위", ""))
                                color = get_rank_color(actual_rank, "foreground")
                                rank_item.setForeground(QColor(color))
                            except:
                                pass
                
                # 카테고리 색상 적용
                if project_category_base and category != '-':
                    category_item = self.ranking_table.item(row, 2)  # 카테고리 컬럼
                    if category_item:
                        keyword_category_clean = category.split('(')[0].strip()
                        color = get_category_match_color(project_category_base, keyword_category_clean)
                        category_item.setForeground(QColor(color))
            
            # 월검색량 기준 내림차순 자동 정렬 (키워드가 있을 때만)
            if keywords_data:
                self.ranking_table.sortByColumn(3, Qt.DescendingOrder)  # 월검색량 컬럼
            
            # 헤더 체크박스는 ModernTableWidget에서 자동 처리됨
                
        except Exception as e:
            logger.error(f"순위 테이블 업데이트 실패: {e}")
    
    
    
    def delete_selected_keywords(self):
        """선택된 키워드들 삭제"""
        if not self.current_project:
            return
        
        # 선택된 키워드 수집 (공용 테이블 사용)
        selected_keyword_ids = []
        selected_keywords = []
        checked_rows = self.ranking_table.get_checked_rows()
        
        for row in checked_rows:
            keyword_item = self.ranking_table.item(row, 1)  # 키워드 컬럼
            if keyword_item:
                keyword_id = keyword_item.data(Qt.UserRole)
                keyword_text = keyword_item.text()
                if keyword_id:
                    selected_keyword_ids.append(keyword_id)
                    selected_keywords.append(keyword_text)
        
        if not selected_keyword_ids:
            return
        
        # 확인 다이얼로그 (화면 중앙에 표시)
        from src.toolbox.ui_kit import ModernConfirmDialog
        
        # 메인 윈도우를 부모로 설정하여 중앙에 표시
        main_window = self.window()
        if ModernConfirmDialog.question(
            main_window,
            "키워드 삭제 확인",
            f"선택한 {len(selected_keywords)}개 키워드를 삭제하시겠습니까?\n\n" +
            "삭제할 키워드:\n" + "\n".join([f"• {kw}" for kw in selected_keywords[:5]]) +
            (f"\n... 외 {len(selected_keywords)-5}개" if len(selected_keywords) > 5 else ""),
            "삭제", "취소"
        ):
            # 키워드 삭제 실행
            success_count = 0
            for keyword_text in selected_keywords:
                try:
                    if rank_tracking_service.delete_keyword(self.current_project_id, keyword_text):
                        success_count += 1
                except Exception as e:
                    logger.error(f"키워드 삭제 실패: {e}")
            
            if success_count > 0:
                log_manager.add_log(f"✅ {success_count}개 키워드가 삭제되었습니다.", "success")
                # 테이블 새로고침
                self.update_ranking_table(self.current_project_id)
    
    
    
    
    
    def show_progress(self, message: str, show_bar: bool = False):
        """진행 상황 표시"""
        self.progress_frame.setVisible(True)
        self.progress_label.setText(message)
        if show_bar:
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)
    
    def hide_progress(self):
        """진행 상황 숨기기"""
        self.progress_frame.setVisible(False)
        self.progress_bar.setVisible(False)
    
    def set_selected_projects(self, selected_projects):
        """다중 선택된 프로젝트들 설정"""
        try:
            self.selected_projects = selected_projects or []
            logger.info(f"선택된 프로젝트 수: {len(self.selected_projects)}")
            
            # 저장 버튼 텍스트 업데이트
            if len(self.selected_projects) > 1:
                self.save_button.setText(f"💾 저장 ({len(self.selected_projects)}개)")
            elif len(self.selected_projects) == 1:
                self.save_button.setText("💾 저장")
            else:
                self.save_button.setText("💾 저장")
                
        except Exception as e:
            logger.error(f"선택된 프로젝트 설정 오류: {e}")
    
    
    def on_ranking_check_finished(self, project_id, success, message, results):
        """순위 확인 완료 - 프로젝트별 처리"""
        # 워커 정리는 ranking_worker_manager에서 처리
        
        # 현재 보고 있는 프로젝트인 경우에만 UI 업데이트
        if self.current_project_id and self.current_project_id == project_id:
            self.update_button_state_for_current_project(running=False)
            self.update_ranking_table(project_id)
            self.hide_progress()
        
        # 워커에서 이미 상품명으로 로그를 출력하므로 여기서는 중복 로그 제거
        if success:
            pass  # 워커에서 이미 로그 출력
        else:
            log_manager.add_log(f"❌ {self.current_project.current_name if self.current_project else '프로젝트'} 순위 확인 실패: {message}", "error")
        
        logger.info(f"프로젝트 {project_id} 순위 확인 완료: {message}")
    
    def on_progress_updated(self, project_id, current, total):
        """진행률 업데이트 - 프로젝트별 처리"""
        # 현재 보고 있는 프로젝트인 경우에만 UI 업데이트
        if self.current_project_id and self.current_project_id == project_id:
            self.show_progress(f"순위 확인 중... ({current}/{total})", show_bar=True)
            percentage = int((current / total) * 100) if total > 0 else 0
            self.progress_bar.setValue(percentage)
    
    def on_keyword_rank_updated(self, project_id, keyword_id, keyword, rank, volume):
        """키워드 순위 업데이트 - 프로젝트별 처리"""
        logger.info(f"🎯🎯🎯 순위 업데이트 시그널 수신! 프로젝트={project_id}, 키워드ID={keyword_id}, 키워드={keyword}, 순위={rank}")
        
        # 현재 보고 있는 프로젝트인 경우에만 UI 업데이트
        if self.current_project_id and self.current_project_id == project_id:
            logger.info(f"🎯🎯🎯 현재 보고 있는 프로젝트와 일치함. UI 업데이트 실행")
            # 실시간 테이블 업데이트 로직
            self.update_single_keyword_rank(keyword_id, keyword, rank, volume)
        else:
            logger.info(f"🎯🎯🎯 현재 프로젝트 ID({self.current_project_id})와 다름. UI 업데이트 건너뜀")
    
    def add_new_ranking_column_with_time(self, time_str: str):
        """새로운 순위 컬럼을 월검색량 바로 다음(4번째)에 삽입"""
        try:
            logger.info(f"새 순위 컬럼 추가 시작: {time_str}")
            
            # 삽입할 위치 (월검색량 다음 = 4번째 인덱스)
            insert_position = 4
            
            column_count = self.ranking_table.columnCount()
            row_count = self.ranking_table.topLevelItemCount()
            logger.info(f"현재 컬럼 수: {column_count}, 행 수: {row_count}")
            
            # 새 컬럼 추가 (맨 뒤에 임시로 추가)
            self.ranking_table.setColumnCount(column_count + 1)
            
            # 헤더 재배치: 4번째 위치에 새 시간 헤더 삽입
            formatted_time = format_date(time_str)
            
            # 기존 헤더들을 수집하고 4번째 위치에 새 헤더 삽입
            new_headers = []
            header_item = self.ranking_table.headerItem()
            
            for i in range(column_count + 1):  # 새로 추가된 컬럼까지 포함
                if i < insert_position:
                    # 4번째 위치 전까지는 기존 헤더 유지
                    if header_item and i < column_count:
                        new_headers.append(header_item.text(i))
                    else:
                        new_headers.append("")
                elif i == insert_position:
                    # 4번째 위치에 새 시간 헤더 삽입
                    new_headers.append(formatted_time)
                else:
                    # 4번째 위치 이후는 기존 헤더를 한 칸씩 뒤로 이동
                    original_index = i - 1
                    if header_item and original_index < column_count:
                        new_headers.append(header_item.text(original_index))
                    else:
                        new_headers.append("")
            
            # 새 헤더 적용
            self.ranking_table.setHeaderLabels(new_headers)
            
            # 모든 행의 데이터 재배치: 4번째 위치에 "-" 삽입
            total_items = self.ranking_table.topLevelItemCount()
            
            for i in range(total_items):
                try:
                    item = self.ranking_table.topLevelItem(i)
                    if item:
                        keyword_name = item.text(1)  # 키워드명
                        
                        # 기존 데이터를 뒤에서부터 한 칸씩 뒤로 이동
                        for col in range(column_count, insert_position, -1):
                            old_text = item.text(col - 1) if col - 1 < item.columnCount() else ""
                            item.setText(col, old_text)
                        
                        # 4번째 위치에 "-" 삽입
                        item.setText(insert_position, "-")
                except Exception as item_e:
                    logger.error(f"행 {i} 처리 실패: {item_e}")
            
            # UI 강제 업데이트
            self.ranking_table.viewport().update()
            self.ranking_table.header().updateGeometry()  # update() 대신 updateGeometry() 사용
            self.ranking_table.resizeColumnToContents(insert_position)  # 새 컬럼 크기 조정
            QApplication.processEvents()
            
            logger.info(f"4번째 위치에 새 순위 컬럼 '{formatted_time}' 삽입 완료")
            
        except Exception as e:
            logger.error(f"새 순위 컬럼 추가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_ranking_table_for_new_check(self, project_id: int, current_time: str):
        """순위 확인용 기본 테이블 구성 (키워드만 + 새 시간 컬럼)"""
        try:
            logger.info(f"순위 확인용 테이블 구성: 프로젝트 {project_id}")
            
            # 기본 헤더 설정
            headers = ["", "키워드", "카테고리", "월검색량"]
            
            # 새로운 시간 컬럼 추가
            formatted_time = self.format_date(current_time)
            headers.append(formatted_time)
            
            # 테이블 완전 초기화
            self.ranking_table.clear()
            self.ranking_table.setColumnCount(len(headers))
            self.ranking_table.setHeaderLabels(headers)
            
            # 키워드만 가져와서 테이블 구성 (기존 순위 데이터 무시)
            keywords = rank_tracking_service.get_project_keywords(project_id)
            
            for keyword in keywords:
                # 리스트로 아이템 데이터 준비
                row_data = ["", keyword.keyword]  # 첫 번째는 체크박스용 빈 문자열
                
                # 카테고리 추가
                category = keyword.category or '-'
                row_data.append(category)
                
                # 월검색량
                monthly_vol = keyword.monthly_volume if keyword.monthly_volume is not None else -1
                if monthly_vol == -1:
                    volume_text = "-"
                elif monthly_vol == 0:
                    volume_text = "0"
                else:
                    volume_text = f"{monthly_vol:,}"
                row_data.append(volume_text)
                
                # 새 시간 컬럼에 "-" 추가
                row_data.append("-")
                
                # QTreeWidgetItem 생성 및 추가
                item = QTreeWidgetItem(row_data)
                item.setData(1, Qt.UserRole, keyword.id)  # 키워드 ID 저장
                
                # 체크박스 설정
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Checked if keyword.is_active else Qt.Unchecked)
                
                self.ranking_table.addTopLevelItem(item)
            
            # 헤더 체크박스 설정
            self.setup_header_checkbox()
            
            logger.info(f"✅ 순위 확인용 테이블 구성 완료: {len(keywords)}개 키워드, 새 컬럼 '{formatted_time}'")
            
        except Exception as e:
            logger.error(f"❌ 순위 확인용 테이블 구성 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def update_single_keyword_rank(self, keyword_id, keyword, rank, volume):
        """단일 키워드의 순위를 실시간으로 업데이트"""
        try:
            logger.info(f"실시간 순위 업데이트 요청: 키워드ID={keyword_id}, 키워드={keyword}, 순위={rank}")
            
            # 테이블에서 해당 키워드 찾기
            found = False
            for i in range(self.ranking_table.topLevelItemCount()):
                item = self.ranking_table.topLevelItem(i)
                stored_keyword_id = item.data(1, Qt.UserRole) if item else None
                logger.debug(f"행 {i}: 저장된 키워드ID={stored_keyword_id}, 찾는 키워드ID={keyword_id}")
                
                if item and stored_keyword_id == keyword_id:
                    found = True
                    # 새로 생성한 순위 컬럼(4번째)에 순위 업데이트
                    ranking_column = 4  # 월검색량(3) 다음 위치
                    logger.info(f"키워드 찾음! 업데이트할 컬럼: {ranking_column} (4번째 컬럼)")
                    
                    # 순위 표시
                    rank_display = format_rank_display(rank)
                    item.setText(ranking_column, rank_display)
                    logger.info(f"순위 텍스트 설정 완료: {rank_display}")
                    
                    # 순위에 따른 색상 설정
                    color = get_rank_color(rank, "foreground")
                    item.setForeground(ranking_column, QColor(color))
                    
                    # 정렬용 데이터 설정
                    sort_rank = 201 if (rank == 0 or rank > 200) else rank
                    item.setData(ranking_column, Qt.UserRole, sort_rank)
                    logger.info(f"키워드 {keyword} 실시간 업데이트 완료")
                    break
            
            if not found:
                logger.warning(f"키워드 ID {keyword_id} ('{keyword}')에 해당하는 테이블 행을 찾을 수 없음")
                    
        except Exception as e:
            logger.error(f"키워드 순위 실시간 업데이트 실패: {e}")
    
    def _apply_category_color(self, item, category: str):
        """카테고리 색상 적용 (기본정보에서 카테고리 바로 확인)"""
        if not category or category == "-":
            return
            
        try:
            # 기본정보 화면에서 카테고리 정보 바로 가져오기
            if hasattr(self, 'category_label') and self.category_label:
                project_category = self.category_label.text()
                
                if project_category and project_category != "-":
                    logger.info(f"🔍 카테고리 비교: 프로젝트='{project_category}' vs 키워드='{category}'")
                    color = get_category_match_color(project_category, category)
                    item.setForeground(2, QColor(color))
                    logger.info(f"✅ 색상 적용: {color} ({'초록' if color == '#059669' else '빨강' if color == '#DC2626' else '회색'})")
                else:
                    logger.warning("기본정보의 카테고리가 비어있음")
            else:
                logger.warning("category_label이 없음")
                    
        except Exception as e:
            logger.error(f"카테고리 색상 설정 실패: {e}")
    
    def _update_monthly_volume_display(self, item, monthly_volume: int):
        """월검색량 표시 업데이트 (중복 코드 제거)"""
        formatted_volume = format_monthly_volume(monthly_volume)
        item.setText(3, formatted_volume)
        item.setData(3, Qt.UserRole, monthly_volume)
    
    def _find_keyword_item(self, keyword: str):
        """테이블에서 키워드 아이템 찾기 (중복 코드 제거)"""
        root = self.ranking_table.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item and item.text(1) == keyword:
                return item
        return None
    
    # show_keyword_addition_progress, update_keyword_progress 함수들 제거됨
    # 백그라운드 처리에서 기존 progress_frame 사용
    
    # 사용하지 않는 진행률 관련 함수들 제거됨
    # 기존 progress_frame과 progress_bar를 재사용
    
    def add_keywords_to_table_immediately(self, keywords: list):
        """테이블에 키워드 즉시 추가 (월검색량/카테고리는 나중에, 원본과 동일)"""
        try:
            for keyword in keywords:
                # 새 항목 생성 (SortableTreeWidgetItem는 같은 파일에 정의되어 있음)
                item = SortableTreeWidgetItem([])
                
                # 체크박스 생성 (컬럼 0)
                checkbox = self._create_item_checkbox()
                self.ranking_table.addTopLevelItem(item)
                self.ranking_table.setItemWidget(item, 0, checkbox)
                
                # 키워드 (컬럼 1)
                item.setText(1, keyword)
                item.setData(1, Qt.UserRole, keyword)  # 키워드 ID는 나중에 설정
                
                # 카테고리 (컬럼 2) - 일단 "-"로 표시
                item.setText(2, "-")
                item.setData(2, Qt.UserRole, 0)
                
                # 월검색량 (컬럼 3) - 일단 "-"로 표시 (아직 검색하지 않음)
                item.setText(3, "-")
                item.setData(3, Qt.UserRole, -1)
                
                # 순위 컬럼들 (4번 이후) - 모두 "-"로 초기화
                column_count = self.ranking_table.columnCount()
                for col in range(4, column_count):
                    item.setText(col, "-")
                    item.setData(col, Qt.UserRole, 202)  # 정렬 시 맨 아래
                
            # 헤더 체크박스 재설정
            self.reset_header_checkbox()
            
            log_manager.add_log(f"✅ 테이블에 {len(keywords)}개 키워드 추가 완료", "success")
            
        except Exception as e:
            log_manager.add_log(f"❌ 테이블 업데이트 실패: {e}", "error")
    
    
    def check_rankings(self):
        """순위 확인 - service 계층 호출"""
        if not self.current_project:
            logger.warning("현재 프로젝트가 선택되지 않음")
            return
        
        project_id = self.current_project_id
        
        # service 계층을 통해 순위 확인 시작
        success = rank_tracking_service.start_ranking_check(project_id)
        if success:
            # UI 상태 업데이트
            self.update_button_state_for_current_project(running=True)
            
            # 현재 저장된 시간으로 컬럼 추가
            current_time = rank_tracking_service.get_ranking_current_time(project_id)
            if current_time:
                self.add_new_ranking_column_with_time(current_time)
            
            # 즉시 진행률 표시 시작
            self.show_progress("순위 확인 준비 중...", show_bar=True)
            self.progress_bar.setValue(0)
    
    def update_button_state_for_current_project(self, running=False):
        """현재 프로젝트의 버튼 상태 업데이트"""
        if running:
            self.check_button.setEnabled(False)
            self.check_button.setText("⏳ 확인 중...")
            self.stop_button.setEnabled(True)
        else:
            self.check_button.setEnabled(True)
            self.check_button.setText("🏆 순위 확인")
            self.stop_button.setEnabled(False)
    

    def on_ranking_finished(self, project_id, success, message, results):
        """순위 확인 완료 처리"""
        logger.info(f"프로젝트 {project_id} 순위 확인 완료: {success}")
            
        # 현재 프로젝트인 경우 UI 업데이트
        if project_id == self.current_project_id:
            self.update_button_state_for_current_project(running=False)
            self.hide_progress()
            # 테이블 새로고침하여 완료된 순위 결과 표시
            self.update_ranking_table(project_id)

    def stop_ranking_check(self):
        """순위 확인 정지 - service 계층 호출"""
        if not self.current_project:
            return
            
        project_id = self.current_project_id
        rank_tracking_service.stop_ranking_check(project_id)
    
    def add_keyword(self):
        """키워드 추가 다이얼로그"""
        if not self.current_project_id:
            from src.toolbox.ui_kit import ModernInfoDialog
            ModernInfoDialog.warning(
                self, 
                "프로젝트 선택 필요", 
                "📋 기존 프로젝트에 추가하려면: 왼쪽 목록에서 프로젝트를 클릭하세요\n\n" +
                "➕ 새 프로젝트를 만들려면: \"새 프로젝트\" 버튼을 클릭하세요"
            )
            return
        
        # 원본과 동일한 키워드 추가 다이얼로그 사용
        dialog = AddKeywordsDialog(self.current_project, self)
        
        if dialog.exec() == QDialog.Accepted:
            # 키워드 가져오기
            keywords = dialog.get_keywords()
            if keywords:
                # service 계층을 통한 키워드 배치 추가
                result = rank_tracking_service.add_keywords_batch_with_background_update(
                    self.current_project_id, keywords
                )
                
                # 결과에 따른 로그 출력
                if result['success']:
                    added_count = result['total_added']
                    duplicate_count = len(result['duplicate_keywords'])
                    
                    # 성공 로그
                    for keyword in result['added_keywords']:
                        log_manager.add_log(f"✅ '{keyword}' 키워드 추가 완료", "success")
                    
                    # 중복 로그  
                    for keyword in result['duplicate_keywords']:
                        log_manager.add_log(f"⚠️ '{keyword}' 키워드는 중복입니다.", "warning")
                    
                    # 실패 로그
                    for keyword in result['failed_keywords']:
                        log_manager.add_log(f"❌ '{keyword}' 키워드 추가 실패", "error")
                    
                    # 즉시 테이블 새로고침
                    self.update_ranking_table(self.current_project_id)
                    log_manager.add_log(f"🎉 {added_count}개 키워드 추가 완료!", "success")
                    log_manager.add_log(f"🔍 월검색량/카테고리 조회를 시작합니다.", "info")
                    
                    if duplicate_count > 0:
                        log_manager.add_log(f"⚠️ {duplicate_count}개 키워드는 중복으로 건너뜀", "warning")
                else:
                    log_manager.add_log("❌ 키워드 추가에 실패했습니다.", "error")
    
    
    # 키워드 정보 워커 매니저 시그널 핸들러들
    def on_keyword_info_progress_updated(self, project_id: int, current: int, total: int, current_keyword: str):
        """키워드 정보 업데이트 진행률 처리"""
        # 현재 프로젝트의 진행률만 표시
        if project_id == self.current_project_id:
            if hasattr(self, 'progress_bar') and hasattr(self, 'progress_label'):
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(current)
                self.progress_label.setText(f"🔍 월검색량/카테고리 조회 중... ({current}/{total}) - {current_keyword}")
                self.progress_frame.setVisible(True)
                self.progress_bar.setVisible(True)
    
    def on_keyword_category_updated(self, project_id: int, keyword: str, category: str):
        """키워드 카테고리 업데이트 처리"""
        # 현재 프로젝트의 카테고리만 업데이트
        if project_id == self.current_project_id:
            self._update_keyword_category_in_table(keyword, category)
    
    def on_keyword_volume_updated(self, project_id: int, keyword: str, volume: int):
        """키워드 월검색량 업데이트 처리"""
        # 현재 프로젝트의 월검색량만 업데이트
        if project_id == self.current_project_id:
            self._update_keyword_volume_in_table(keyword, volume)
    
    def on_keyword_info_finished(self, project_id: int, success: bool, message: str):
        """키워드 정보 업데이트 완료 처리"""
        # 현재 프로젝트의 완료만 처리
        if project_id == self.current_project_id:
            self.hide_progress()
        
        # 로그는 해당 프로젝트 이름으로 표시
        try:
            from .service import rank_tracking_service
            project = rank_tracking_service.get_project_by_id(project_id)
            project_name = project.current_name if project else f"프로젝트 ID {project_id}"
            
            if success:
                log_manager.add_log(f"✅ {project_name} - {message}", "success")
            else:
                log_manager.add_log(f"❌ {project_name} - {message}", "error")
        except Exception as e:
            logger.error(f"키워드 정보 완료 로그 처리 실패: {e}")
    
    def _update_keyword_category_in_table(self, keyword: str, category: str):
        """테이블에서 키워드 카테고리만 업데이트"""
        try:
            item = self._find_keyword_item(keyword)
            if not item:
                return
            
            # 카테고리 업데이트
            item.setText(2, category or '-')
            
            # 카테고리 색상 적용
            if category != '-' and hasattr(self, 'category_label') and self.category_label:
                project_category = self.category_label.text()
                if project_category and project_category != "-":
                    from .adapters import get_category_match_color
                    from PySide6.QtGui import QColor
                    # 키워드 카테고리에서 괄호 앞 부분만 추출
                    keyword_category_clean = category.split('(')[0].strip()
                    # 프로젝트 카테고리에서 마지막 부분만 추출
                    project_category_base = project_category.split(' > ')[-1] if ' > ' in project_category else project_category
                    color = get_category_match_color(project_category_base, keyword_category_clean)
                    item.setForeground(2, QColor(color))
            
            # 테이블 즉시 새로고침
            self.ranking_table.viewport().update()
            
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 카테고리 테이블 업데이트 실패: {e}")
    
    def _update_keyword_volume_in_table(self, keyword: str, volume: int):
        """테이블에서 키워드 월검색량만 업데이트"""
        try:
            item = self._find_keyword_item(keyword)
            if not item:
                return
            
            # 월검색량 업데이트
            if volume >= 0:
                from .adapters import format_monthly_volume
                volume_text = format_monthly_volume(volume)
                item.setText(3, volume_text)
                item.setData(3, Qt.UserRole, volume)
            else:
                item.setText(3, "-")
                item.setData(3, Qt.UserRole, -1)
            
            # 테이블 즉시 새로고침
            self.ranking_table.viewport().update()
            
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 월검색량 테이블 업데이트 실패: {e}")
    
    def setup_buttons(self, layout):
        """하단 버튼들 설정"""
        # 하단 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)
        
        # 키워드 추가 버튼 (새 프로젝트 생성과 동일한 색상)
        self.add_keyword_button = ModernPrimaryButton("➕ 키워드 추가")
        self.add_keyword_button.clicked.connect(self.add_keyword)
        self.add_keyword_button.setEnabled(False)  # 프로젝트 선택 시에만 활성화
        self.add_keyword_button.setMinimumWidth(130)
        self.add_keyword_button.setMaximumWidth(130)
        button_layout.addWidget(self.add_keyword_button)
        
        # 순위 확인 버튼 (키워드 검색기 클리어 버튼과 동일한 warning 색상)
        self.check_button = ModernSuccessButton("🔍 순위 확인")
        self.check_button.clicked.connect(self.check_rankings)
        self.check_button.setEnabled(False)  # 프로젝트 선택 시에만 활성화
        self.check_button.setMinimumWidth(120)
        self.check_button.setMaximumWidth(120)
        button_layout.addWidget(self.check_button)
        
        # 정지 버튼
        self.stop_button = ModernCancelButton("⏹️ 정지")
        self.stop_button.clicked.connect(self.stop_ranking_check)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumWidth(120)
        self.stop_button.setMaximumWidth(120)
        button_layout.addWidget(self.stop_button)
        
        # 오른쪽 끝으로 밀기 위한 스트레치
        button_layout.addStretch()
        
        # 저장 버튼 (오른쪽 끝)
        self.save_button = ModernSuccessButton("💾 저장")
        self.save_button.clicked.connect(self.export_data)
        self.save_button.setEnabled(False)  # 프로젝트 선택 시에만 활성화
        self.save_button.setMinimumWidth(120)
        self.save_button.setMaximumWidth(120)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
        
    def get_latest_check_time(self):
        """DB에서 가장 최근 순위 확인 시간 가져오기"""
        try:
            if not self.current_project_id:
                return None
            
            # Foundation DB를 통해 가장 최근 순위 확인 시간 조회
            from src.foundation.db import get_db
            
            db = get_db()
            latest_rankings = db.get_latest_rankings(self.current_project_id, limit=1)
            
            if latest_rankings:
                latest_time = latest_rankings[0].get('created_at')
                if latest_time:
                    # 날짜 포맷팅 - "2025-08-15 22:17:32" 형태로 반환
                    from datetime import datetime
                    if isinstance(latest_time, str):
                        try:
                            dt = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                            return dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            return str(latest_time)
                    elif isinstance(latest_time, datetime):
                        return latest_time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        return str(latest_time)
            
            return None
            
        except Exception as e:
            logger.error(f"최신 확인 시간 조회 실패: {e}")
            return None
    
    def get_header_times(self):
        """테이블 헤더에서 시간 정보 가져오기"""
        try:
            header_times = []
            header_item = self.ranking_table.headerItem()
            
            if header_item:
                for col in range(4, self.ranking_table.columnCount()):  # 4번째 컬럼부터 날짜
                    header_text = header_item.text(col)
                    if header_text and "/" in header_text:
                        header_times.append(header_text.strip())
            
            return header_times
            
        except Exception as e:
            logger.error(f"헤더 시간 정보 가져오기 실패: {e}")
            return []
    
    
    def set_selected_projects(self, selected_projects):
        """선택된 프로젝트들 설정 (다중 선택 지원)"""
        try:
            self.selected_projects = selected_projects or []
            logger.info(f"선택된 프로젝트 수: {len(self.selected_projects)}")
            
            # 저장 버튼 텍스트 업데이트
            if len(self.selected_projects) > 1:
                self.save_button.setText(f"💾 저장 ({len(self.selected_projects)}개)")
            else:
                self.save_button.setText("💾 저장")
                
        except Exception as e:
            logger.error(f"선택된 프로젝트 설정 오류: {e}")
            self.selected_projects = []
    
    def export_data(self):
        """순위 이력 데이터 Excel로 내보내기 (service 계층 사용)"""
        try:
            # 선택된 프로젝트 확인
            if len(self.selected_projects) > 1:
                # 다중 프로젝트 내보내기
                rank_tracking_service.export_multiple_projects(self.selected_projects, self)
            elif self.current_project_id:
                # 단일 프로젝트 내보내기
                rank_tracking_service.export_single_project(self.current_project_id, self)
            else:
                log_manager.add_log("⚠️ 내보낼 프로젝트가 선택되지 않았습니다.", "warning")
        except Exception as e:
            logger.error(f"데이터 내보내기 오류: {e}")
            log_manager.add_log(f"❌ 데이터 내보내기 중 오류가 발생했습니다: {str(e)}", "error")
    
    


