"""
순위 테이블 위젯 - 키워드 순위 관리 및 표시
기존 UI와 완전 동일한 스타일 및 기능
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QDialog, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from src.toolbox.ui_kit.modern_table import ModernTableWidget
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernDangerButton, ModernSuccessButton, ModernCancelButton
from src.desktop.common_log import log_manager
from src.foundation.logging import get_logger

from .worker import ranking_worker_manager, keyword_info_worker_manager
from .adapters import format_rank_display, get_rank_color, get_category_match_color, format_date
from src.toolbox.formatters import format_monthly_volume, format_rank
from .service import rank_tracking_service
# view_model은 service로 통합됨

logger = get_logger("features.rank_tracking.ranking_table_widget")


class AddKeywordsDialog(QDialog):
    """키워드 추가 다이얼로그"""
    
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
        
        self.cancel_button = ModernCancelButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFixedWidth(80)
        # 강제로 동일한 크기 적용
        self.cancel_button.setStyleSheet(self.cancel_button.styleSheet() + "QPushButton { width: 80px; min-width: 80px; max-width: 80px; }")
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = ModernPrimaryButton("추가")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFixedWidth(80)
        # 강제로 동일한 크기 적용
        self.ok_button.setStyleSheet(self.ok_button.styleSheet() + "QPushButton { width: 80px; min-width: 80px; max-width: 80px; }")
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
    last_check_time_changed = Signal(str)  # 마지막 확인 시간 변경 시그널
    
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
            columns=["", "키워드", "카테고리", "월검색량"],  # 기본 4개 컬럼만
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
        
        # 컬럼 너비 설정 (기본 4개 컬럼)
        self.ranking_table.setColumnWidth(0, 50)       # 체크박스
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
                        
                        # ModernTableWidget의 컬럼 삭제 기능 사용
                        # 먼저 컬럼 제목으로 삭제 시도
                        if self.ranking_table.remove_column_by_title(date_text):
                            log_manager.add_log(f"✅ 컬럼 '{date_text}' 삭제 완료", "success")
                        else:
                            # 제목으로 찾지 못한 경우 직접 인덱스로 삭제
                            if column_index < self.ranking_table.columnCount():
                                self.ranking_table.removeColumn(column_index)
                        
                        # 테이블 업데이트
                        self.ranking_table.viewport().update()
                        self.ranking_table.repaint()
                    else:
                        log_manager.add_log(f"❌ {date_text} 날짜의 순위 데이터 삭제에 실패했습니다.", "error")
                        from src.toolbox.ui_kit import ModernInfoDialog
                        ModernInfoDialog.error(self, "삭제 실패", "데이터베이스에서 해당 날짜의 데이터를 찾을 수 없거나 삭제에 실패했습니다.")
                else:
                    from src.toolbox.ui_kit import ModernInfoDialog
                    ModernInfoDialog.error(self, "오류", "날짜 데이터를 찾을 수 없습니다.")
                    
            except Exception as e:
                log_manager.add_log(f"❌ 날짜 데이터 삭제 중 오류: {str(e)}", "error")
                from src.toolbox.ui_kit import ModernInfoDialog
                ModernInfoDialog.error(self, "오류", f"날짜 데이터 삭제 중 오류가 발생했습니다: {str(e)}")
    
    
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
        if hasattr(self, 'check_button'):
            self.check_button.setEnabled(True)  # 순위 확인 버튼 활성화
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(True)
        
        # 순위 확인 버튼 상태는 해당 프로젝트의 실행 상태에 따라 결정
        self.refresh_button_state(project.id)
        
        # 진행률 표시 상태도 프로젝트에 따라 업데이트
        self.update_progress_display_from_project_status(project.id)
    
    def refresh_button_state(self, project_id: int):
        """프로젝트 상태를 조회해서 버튼 상태 업데이트"""
        if hasattr(self, 'check_button') and hasattr(self, 'stop_button'):
            is_running = rank_tracking_service.is_ranking_in_progress(project_id)
            
            if is_running:
                self.check_button.setEnabled(False)
                self.check_button.setText("⏳ 확인 중...")
                self.stop_button.setEnabled(True)
            else:
                self.check_button.setEnabled(True)
                self.check_button.setText("🏆 순위 확인")
                self.stop_button.setEnabled(False)
                
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
        
        # 테이블 초기화 (중복 제거 - _reset_table_columns 활용)
        if hasattr(self, 'ranking_table'):
            self._reset_table_columns()
        
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
        """순위 테이블 업데이트 (service 계층 활용으로 단순화)"""
        try:
            # 진행 중인 순위 확인 상태 복원
            is_ranking_in_progress = ranking_worker_manager.is_ranking_in_progress(project_id)
            if is_ranking_in_progress:
                logger.info(f"프로젝트 {project_id}: 순위 확인 진행 중 - 진행 상태 복원")
                self.update_progress_display_from_project_status(project_id)
            
            # service에서 테이블 데이터 준비
            table_data = rank_tracking_service.prepare_table_data(project_id)
            if not table_data.get("success", False):
                logger.error(f"테이블 데이터 준비 실패: {table_data.get('message')}")
                return
            
            # 기본 데이터 추출
            headers = table_data["headers"]
            dates = table_data["dates"]
            project_category_base = table_data["project_category_base"]
            
            # 키워드 데이터 구성 (항상 keywords 목록에서 가져오기)
            keywords_data = {}
            keywords = table_data["keywords"]
            overview_keywords = table_data["overview"].get("keywords", {}) if table_data["overview"] else {}
            
            for keyword in keywords:
                keywords_data[keyword.id] = {
                    'id': keyword.id,
                    'keyword': keyword.keyword,
                    'category': keyword.category or '-',
                    'monthly_volume': keyword.monthly_volume if keyword.monthly_volume is not None else -1,
                    'search_volume': getattr(keyword, 'search_volume', None),
                    'is_active': True,
                    'rankings': overview_keywords.get(keyword.keyword, {})
                }
            
            # 날짜 컬럼 표시 여부 결정 (service 활용)
            should_show_dates = rank_tracking_service.should_show_date_columns(project_id)
            if not should_show_dates:
                logger.info(f"프로젝트 {project_id} - 키워드 없음: 날짜 컬럼 숨김")
                all_dates = []
            else:
                all_dates = dates
                # 진행 중인 시간 추가
                current_time = ranking_worker_manager.get_current_time(project_id)
                if current_time and current_time not in all_dates:
                    all_dates = [current_time] + all_dates
                    # 헤더 재구성
                    headers = table_data["headers"][:4]
                    for date in all_dates:
                        headers.append(format_date(date))
            
            # 마지막 확인 시간 변경 시그널 발송 (메인 UI 업데이트용)
            self.last_check_time_changed.emit(table_data["last_check_time"])
            
            # 테이블 초기화 및 기본 컬럼 설정 (헤더 체크박스 설정하지 않음)
            self._reset_table_columns()
            
            # 동적 날짜 컬럼 추가
            for date in all_dates:
                date_title = format_date(date)
                self.ranking_table.add_dynamic_column(date_title, column_width=100)
            
            # 키워드 행 추가
            if keywords_data:
                self._populate_keyword_rows(keywords_data, all_dates, project_id, project_category_base)
                # 월검색량 기준 정렬
                self.ranking_table.sortByColumn(3, Qt.DescendingOrder)
            
            # 🔧 FIX: 테이블 구성 완료 후 헤더 체크박스 설정 (원본 방식)
            self.ranking_table.setup_header_checkbox()
            
            # 🔧 FIX: 삭제 버튼 상태 업데이트 (원본 방식)
            self.on_selection_changed()
                
        except Exception as e:
            logger.error(f"순위 테이블 업데이트 실패: {e}")
    
    def _reset_table_columns(self):
        """테이블 컬럼 초기화 (헤더 체크박스 설정 제외) - 원본 방식"""
        self.ranking_table.clear_table()
        self.ranking_table.setColumnCount(0)
        
        # 🔧 FIX: 기존 헤더 체크박스 명시적 제거 (원본 방식)
        if hasattr(self.ranking_table, 'header_checkbox') and self.ranking_table.header_checkbox:
            try:
                self.ranking_table.header_checkbox.setParent(None)
                self.ranking_table.header_checkbox.deleteLater()
                self.ranking_table.header_checkbox = None
            except:
                pass
        
        # 기본 4개 컬럼 설정 (헤더 체크박스 설정 제외)
        base_columns = ["", "키워드", "카테고리", "월검색량"]
        self.ranking_table.setColumnCount(len(base_columns))
        self.ranking_table.setHorizontalHeaderLabels(base_columns)
        # setup_header_checkbox() 호출하지 않음 - 나중에 호출
        
        # 컬럼 너비 설정
        self.ranking_table.setColumnWidth(0, 50)   # 체크박스
        self.ranking_table.setColumnWidth(1, 200)  # 키워드
        self.ranking_table.setColumnWidth(2, 180)  # 카테고리
        self.ranking_table.setColumnWidth(3, 100)  # 월검색량
    
    def _populate_keyword_rows(self, keywords_data: dict, all_dates: list, project_id: int, project_category_base: str):
        """키워드 행 채우기 (service 활용)"""
        for keyword_id, data in keywords_data.items():
            # service에서 행 데이터 준비
            row_data = rank_tracking_service.prepare_table_row_data(project_id, data, all_dates, project_category_base)
            
            # 순위 컬럼 인덱스 계산
            rank_column_indices = list(range(3, len(row_data)))
            row = self.ranking_table.add_row_with_data(row_data, checkable=True, rank_columns=rank_column_indices)
            
            # 키워드 ID 저장
            keyword_item = self.ranking_table.item(row, 1)
            if keyword_item:
                keyword_item.setData(Qt.UserRole, keyword_id)
            
            # 색상 및 정렬 데이터 적용
            self._apply_row_styling(row, data, all_dates, project_category_base)
    
    def _apply_row_styling(self, row: int, keyword_data: dict, all_dates: list, project_category_base: str):
        """행 스타일링 적용 (중복 제거)"""
        from src.toolbox.ui_kit.sortable_items import set_rank_sort_data
        
        # 순위 컬럼 색상 및 정렬 데이터
        for i, date in enumerate(all_dates):
            column_index = 4 + i
            rank_item = self.ranking_table.item(row, column_index)
            if rank_item:
                rank_text = rank_item.text()
                set_rank_sort_data(rank_item, column_index, rank_text)
                
                # 순위 색상 적용
                if rank_text != "-":
                    try:
                        actual_rank = int(rank_text.replace("위", ""))
                        color = get_rank_color(actual_rank, "foreground")
                        rank_item.setForeground(QColor(color))
                    except:
                        pass
        
        # 카테고리 색상 적용 (전체 카테고리 경로로 비교)
        category = keyword_data.get('category', '-')
        if project_category_base and category != '-':
            category_item = self.ranking_table.item(row, 2)
            if category_item:
                keyword_category_clean = category.split('(')[0].strip()
                color = get_category_match_color(project_category_base, keyword_category_clean)
                category_item.setForeground(QColor(color))
    
    
    
    def delete_selected_keywords(self):
        """선택된 키워드들 삭제 (UI 오케스트레이션만)"""
        if not self.current_project:
            return
        
        # 선택된 키워드 수집
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
        
        # 확인 다이얼로그
        from src.toolbox.ui_kit import ModernConfirmDialog
        main_window = self.window()
        if ModernConfirmDialog.question(
            main_window,
            "키워드 삭제 확인",
            f"선택한 {len(selected_keywords)}개 키워드를 삭제하시겠습니까?\n\n" +
            "삭제할 키워드:\n" + "\n".join([f"• {kw}" for kw in selected_keywords[:5]]) +
            (f"\n... 외 {len(selected_keywords)-5}개" if len(selected_keywords) > 5 else ""),
            "삭제", "취소"
        ):
            # service 계층을 통한 삭제 (비즈니스 로직 분리)
            success, message = rank_tracking_service.delete_selected_keywords_by_ids(
                self.current_project_id, selected_keyword_ids, selected_keywords
            )
            
            # 결과 처리
            if success:
                log_manager.add_log(message, "success")
                self.update_ranking_table(self.current_project_id)
            else:
                log_manager.add_log(message, "error")
    
    
    
    
    
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
            
            formatted_time = format_date(time_str)
            
            # ModernTableWidget의 동적 컬럼 추가 기능 사용
            # 각 키워드에 대해 빈 순위 데이터("-") 준비
            column_data = []
            for row in range(self.ranking_table.rowCount()):
                column_data.append("-")
            
            # 동적 컬럼 추가 (월검색량 바로 다음인 4번째 위치에 삽입)
            insert_position = 4
            success = self.ranking_table.insert_column_at_position(insert_position, formatted_time, column_data, 100)
            
            if not success:
                # 삽입 실패시 맨 뒤에 추가 (fallback)
                logger.warning(f"4번째 위치 삽입 실패, 맨 뒤에 추가: {formatted_time}")
                self.ranking_table.add_dynamic_column(formatted_time, column_data, 100)
            
            logger.info(f"새 순위 컬럼 '{formatted_time}' 추가 완료")
            
        except Exception as e:
            logger.error(f"새 순위 컬럼 추가 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_ranking_table_for_new_check(self, project_id: int, current_time: str):
        """순위 확인용 기본 테이블 구성 (키워드만 + 새 시간 컬럼)"""
        try:
            logger.info(f"순위 확인용 테이블 구성: 프로젝트 {project_id}")
            
            # 테이블 완전 초기화
            self.ranking_table.clear_table()
            
            # 새로운 시간 컬럼 추가 (ModernTableWidget의 동적 컬럼 기능 사용)
            formatted_time = format_date(current_time)
            self.ranking_table.add_dynamic_column(formatted_time, column_width=100)
            
            # 키워드만 가져와서 테이블 구성 (기존 순위 데이터 무시)
            keywords = rank_tracking_service.get_project_keywords(project_id)
            
            for keyword in keywords:
                # ModernTableWidget용 데이터 준비 (체크박스 자동 포함)
                row_data = [
                    keyword.keyword,  # 키워드
                    keyword.category or '-',  # 카테고리
                ]
                
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
                
                # ModernTableWidget에 행 추가 (순위 컬럼들 지정)
                # 마지막 컬럼이 순위 컬럼
                rank_column_indices = [3] if len(row_data) > 3 else []  # 3번이 순위 컬럼
                row = self.ranking_table.add_row_with_data(row_data, checkable=True, rank_columns=rank_column_indices)
                
                # 키워드 ID를 키워드 컬럼에 저장
                keyword_item = self.ranking_table.item(row, 1)  # 키워드 컬럼
                if keyword_item:
                    keyword_item.setData(Qt.UserRole, keyword.id)
            
            logger.info(f"✅ 순위 확인용 테이블 구성 완료: {len(keywords)}개 키워드, 새 컬럼 '{formatted_time}'")
            
        except Exception as e:
            logger.error(f"❌ 순위 확인용 테이블 구성 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def update_single_keyword_rank(self, keyword_id, keyword, rank, volume):
        """단일 키워드의 순위를 실시간으로 업데이트"""
        try:
            logger.info(f"실시간 순위 업데이트 요청: 키워드ID={keyword_id}, 키워드={keyword}, 순위={rank}")
            
            # 🔧 FIX: 현재 진행 중인 순위 확인 시간으로 컬럼 찾기
            current_time = rank_tracking_service.get_ranking_current_time(self.current_project_id)
            if not current_time:
                logger.warning("현재 진행 중인 순위 확인 시간을 찾을 수 없음")
                return
            
            formatted_time = format_date(current_time)
            logger.info(f"찾을 컬럼 헤더: '{formatted_time}'")
            
            # 헤더에서 해당 시간의 컬럼 인덱스 찾기
            ranking_column = None
            for col in range(self.ranking_table.columnCount()):
                header_item = self.ranking_table.horizontalHeaderItem(col)
                if header_item and header_item.text() == formatted_time:
                    ranking_column = col
                    logger.info(f"순위 업데이트 컬럼 찾음: {col}번째 ('{formatted_time}')")
                    break
            
            if ranking_column is None:
                logger.warning(f"순위 컬럼을 찾을 수 없음: '{formatted_time}'")
                return
            
            # 테이블에서 해당 키워드 찾기 (ModernTableWidget 사용)
            found = False
            for row in range(self.ranking_table.rowCount()):
                keyword_item = self.ranking_table.item(row, 1)  # 키워드 컬럼
                if keyword_item:
                    stored_keyword_id = keyword_item.data(Qt.UserRole)
                    logger.debug(f"행 {row}: 저장된 키워드ID={stored_keyword_id}, 찾는 키워드ID={keyword_id}")
                    
                    if stored_keyword_id == keyword_id:
                        found = True
                        logger.info(f"키워드 찾음! 업데이트할 컬럼: {ranking_column}")
                        
                        rank_item = self.ranking_table.item(row, ranking_column)
                        if not rank_item:
                            # 아이템이 없으면 새로 생성
                            from PySide6.QtWidgets import QTableWidgetItem
                            rank_item = QTableWidgetItem("")
                            self.ranking_table.setItem(row, ranking_column, rank_item)
                            logger.info(f"행 {row}, 컬럼 {ranking_column}에 새 아이템 생성")
                        
                        # 순위 표시
                        rank_display = format_rank_display(rank)
                        rank_item.setText(rank_display)
                        logger.info(f"순위 텍스트 설정 완료: {rank_display}")
                        
                        # 순위에 따른 색상 설정
                        color = get_rank_color(rank, "foreground")
                        rank_item.setForeground(QColor(color))
                        
                        # 정렬용 데이터 설정 (통일된 방식 사용)
                        from src.toolbox.ui_kit.sortable_items import set_rank_sort_data
                        set_rank_sort_data(rank_item, ranking_column, rank_display)
                        logger.info(f"키워드 {keyword} 실시간 업데이트 완료")
                        break
            
            if not found:
                logger.warning(f"키워드 ID {keyword_id} ('{keyword}')에 해당하는 테이블 행을 찾을 수 없음")
                    
        except Exception as e:
            logger.error(f"키워드 순위 실시간 업데이트 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    
    def _find_keyword_item(self, keyword: str):
        """테이블에서 키워드 아이템 찾기 (ModernTableWidget용)"""
        for row in range(self.ranking_table.rowCount()):
            keyword_item = self.ranking_table.item(row, 1)  # 키워드 컬럼
            if keyword_item and keyword_item.text() == keyword:
                return row  # 행 번호 반환
        return None
    
    
    def add_keywords_to_table_immediately(self, keywords: list):
        """테이블에 키워드 즉시 추가 (중복 제거)"""
        try:
            current_column_count = self.ranking_table.columnCount()
            ranking_column_count = max(0, current_column_count - 4)  # 순위 컬럼 수
            
            for keyword in keywords:
                # 기본 행 데이터 구성
                row_data = [keyword, "-", "-"] + ["-"] * ranking_column_count
                
                # 순위 컬럼 인덱스
                rank_column_indices = list(range(3, len(row_data)))
                row = self.ranking_table.add_row_with_data(row_data, checkable=True, rank_columns=rank_column_indices)
                
                # 월검색량 컬럼에 정렬 데이터 설정
                volume_item = self.ranking_table.item(row, 3)
                if volume_item:
                    volume_item.setData(Qt.UserRole, -1)
            
            log_manager.add_log(f"✅ 테이블에 {len(keywords)}개 키워드 추가 완료", "success")
            
        except Exception as e:
            log_manager.add_log(f"❌ 테이블 업데이트 실패: {e}", "error")
    
    
    def check_rankings(self):
        """순위 확인 - service 계층 호출"""
        try:
            logger.info("순위 확인 버튼 클릭됨")
            
            if not self.current_project:
                logger.warning("현재 프로젝트가 선택되지 않음")
                return
            
            project_id = self.current_project_id
            logger.info(f"순위 확인 시작: 프로젝트 ID {project_id}")
            
            # 순위 확인 시작 로그 추가
            from src.desktop.common_log import log_manager
            log_manager.add_log(f"🏆 {self.current_project.current_name} 순위 확인을 시작합니다.", "info")
            
            # service 계층을 통해 순위 확인 시작
            success = rank_tracking_service.start_ranking_check(project_id)
            logger.info(f"순위 확인 시작 결과: {success}")
            
            if success:
                # UI 상태 업데이트
                if hasattr(self, 'current_project_id'):
                    self.refresh_button_state(self.current_project_id)
                
                # 현재 저장된 시간으로 컬럼 추가
                current_time = rank_tracking_service.get_ranking_current_time(project_id)
                if current_time:
                    self.add_new_ranking_column_with_time(current_time)
                
                # 즉시 진행률 표시 시작
                self.show_progress("순위 확인 준비 중...", show_bar=True)
                self.progress_bar.setValue(0)
                logger.info("순위 확인 UI 상태 업데이트 완료")
            else:
                log_manager.add_log("❌ 순위 확인 시작에 실패했습니다.", "error")
                logger.error("순위 확인 시작 실패")
                
        except Exception as e:
            logger.error(f"순위 확인 중 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            from src.desktop.common_log import log_manager
            log_manager.add_log(f"❌ 순위 확인 중 오류: {str(e)}", "error")
    
    

    def on_ranking_finished(self, project_id, success, message, results):
        """순위 확인 완료 처리"""
        logger.info(f"프로젝트 {project_id} 순위 확인 완료: {success}")
        
        # 완료 로그 추가
        from src.desktop.common_log import log_manager
        if success:
            log_manager.add_log(f"✅ {message}", "success")
        else:
            log_manager.add_log(f"❌ {message}", "error")
            
        # 현재 프로젝트인 경우 UI 업데이트
        if project_id == self.current_project_id:
            self.refresh_button_state(project_id)
            self.hide_progress()
            # 테이블 새로고침하여 완료된 순위 결과 표시
            self.update_ranking_table(project_id)

    def stop_ranking_check(self):
        """순위 확인 정지 - service 계층 호출"""
        if not self.current_project:
            return
            
        project_id = self.current_project_id
        
        # 정지 로그 추가
        from src.desktop.common_log import log_manager
        log_manager.add_log(f"⏹️ {self.current_project.current_name} 순위 확인을 정지했습니다.", "warning")
        
        rank_tracking_service.stop_ranking_check(project_id)
        
        # 즉시 UI 상태 업데이트
        self.refresh_button_state(project_id)
        self.hide_progress()
    
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
        
        # 키워드 추가 다이얼로그 사용
        dialog = AddKeywordsDialog(self.current_project, self)
        
        if dialog.exec() == QDialog.Accepted:
            # 키워드 가져오기
            keywords = dialog.get_keywords()
            if keywords:
                # 키워드 배치 추가 (즉시 DB 추가 + 백그라운드 업데이트)
                result = rank_tracking_service.add_keywords_batch_with_background_update(
                    self.current_project_id, keywords
                )
                
                # 결과 처리 (로그는 service에서 이미 처리됨)
                if result['success']:
                    # 전체 테이블 다시 로드 (프로젝트 선택과 동일한 방식)
                    self.update_ranking_table(self.current_project_id)
                    
                    # 백그라운드 작업이 시작된 경우 진행률 표시
                    added_keywords = result.get('added_keywords', [])
                    if added_keywords:
                        # 즉시 진행률 표시 시작
                        self.show_progress(f"🔍 월검색량/카테고리 조회 준비 중... (0/{len(added_keywords)})", True)
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
            row = self._find_keyword_item(keyword)
            if row is None:
                return
            
            # 카테고리 업데이트 (표시용으로는 마지막 부분만)
            category_item = self.ranking_table.item(row, 2)  # 카테고리 컬럼
            if category_item:
                if category and category != '-':
                    # 괄호 앞 부분에서 마지막 세그먼트만 추출
                    category_clean = category.split('(')[0].strip()
                    if ' > ' in category_clean:
                        category_display = category_clean.split(' > ')[-1]
                        # 비율 정보가 있으면 마지막에 추가
                        if '(' in category:
                            percentage_part = category.split('(')[-1]
                            category_display = f"{category_display}({percentage_part}"
                    else:
                        category_display = category
                else:
                    category_display = '-'
                category_item.setText(category_display)
            
            # 카테고리 색상 즉시 적용 (키워드 추가 시 바로 색상 표시)
            if category != '-' and self.current_project:
                # 현재 프로젝트에서 카테고리 직접 가져오기
                project_category = getattr(self.current_project, 'category', None)
                if project_category and project_category != "-":
                    from .adapters import get_category_match_color
                    from PySide6.QtGui import QColor
                    # 전체 카테고리 경로로 비교 (괄호 부분만 제거)
                    keyword_category_clean = category.split('(')[0].strip()
                    color = get_category_match_color(project_category, keyword_category_clean)
                    if category_item:
                        category_item.setForeground(QColor(color))
                        logger.info(f"🎨 키워드 '{keyword}' 카테고리 색상 즉시 적용: {color} (프로젝트: {project_category}, 키워드: {keyword_category_clean})")
            
            # 테이블 즉시 새로고침
            self.ranking_table.viewport().update()
            
        except Exception as e:
            logger.error(f"키워드 '{keyword}' 카테고리 테이블 업데이트 실패: {e}")
    
    def _update_keyword_volume_in_table(self, keyword: str, volume: int):
        """테이블에서 키워드 월검색량만 업데이트"""
        try:
            row = self._find_keyword_item(keyword)
            if row is None:
                return
            
            # 월검색량 업데이트
            volume_item = self.ranking_table.item(row, 3)  # 월검색량 컬럼
            if volume_item:
                if volume >= 0:
                    volume_text = format_monthly_volume(volume)
                    volume_item.setText(volume_text)
                    volume_item.setData(Qt.UserRole, volume)
                else:
                    volume_item.setText("-")
                    volume_item.setData(Qt.UserRole, -1)
            
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
    
    def export_data(self):
        """순위 이력 데이터 Excel로 내보내기 (UI에서 다이얼로그 처리)"""
        try:
            # 선택된 프로젝트 확인
            if len(self.selected_projects) > 1:
                # 다중 프로젝트 내보내기
                self.export_multiple_projects_dialog(self.selected_projects)
            elif self.current_project_id:
                # 단일 프로젝트 내보내기
                self.export_single_project_dialog(self.current_project_id)
            else:
                log_manager.add_log("⚠️ 내보낼 프로젝트가 선택되지 않았습니다.", "warning")
        except Exception as e:
            logger.error(f"데이터 내보내기 오류: {e}")
            log_manager.add_log(f"❌ 데이터 내보내기 중 오류가 발생했습니다: {str(e)}", "error")
    
    def export_single_project_dialog(self, project_id: int) -> bool:
        """단일 프로젝트 Excel 내보내기 다이얼로그 (UI 계층)"""
        try:
            from PySide6.QtWidgets import QFileDialog
            from .adapters import rank_tracking_excel_exporter
            from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
            from datetime import datetime
            
            # 기본 파일명 생성
            default_filename = rank_tracking_excel_exporter.get_default_filename(project_id)
            
            # 파일 저장 다이얼로그
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "순위 이력 Excel 저장", 
                default_filename,
                "Excel 파일 (*.xlsx);;모든 파일 (*)"
            )
            
            if file_path:
                # adapters를 통한 엑셀 저장 (service 레이어 우회)
                success = rank_tracking_excel_exporter.export_ranking_history_to_excel(
                    project_id, file_path
                )
                if success:
                    project = rank_tracking_service.get_project_by_id(project_id)
                    project_name = project.current_name if project else f"프로젝트 {project_id}"
                    
                    log_manager.add_log(f"✅ 순위 이력 Excel 파일이 저장되었습니다: {file_path}", "success")
                    
                    # 공용 저장 완료 다이얼로그
                    main_window = self.window()
                    ModernSaveCompletionDialog.show_save_completion(
                        main_window,
                        "저장 완료",
                        f"순위 이력이 성공적으로 저장되었습니다.\n\n프로젝트: {project_name}",
                        file_path
                    )
                    return True
                else:
                    log_manager.add_log("❌ Excel 파일 저장에 실패했습니다.", "error")
                    return False
            return False
            
        except Exception as e:
            logger.error(f"단일 프로젝트 내보내기 오류: {e}")
            return False
    
    def export_multiple_projects_dialog(self, project_ids: list) -> bool:
        """다중 프로젝트 Excel 내보내기 다이얼로그 (UI 계층)"""
        try:
            from PySide6.QtWidgets import QFileDialog
            from .adapters import rank_tracking_excel_exporter
            from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
            from datetime import datetime
            
            # 기본 파일명 생성 (다중 프로젝트)
            default_filename = f"순위이력_다중프로젝트_{len(project_ids)}개_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # 파일 저장 다이얼로그
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "다중 프로젝트 순위 이력 Excel 저장",
                default_filename,
                "Excel 파일 (*.xlsx);;모든 파일 (*)"
            )
            
            if file_path:
                # adapters를 통한 다중 프로젝트 엑셀 저장 (service 레이어 우회)
                success = rank_tracking_excel_exporter.export_multiple_projects_to_excel(
                    project_ids, file_path
                )
                if success:
                    log_manager.add_log(f"✅ 다중 프로젝트 순위 이력 Excel 파일이 저장되었습니다: {file_path}", "success")
                    
                    # 공용 저장 완료 다이얼로그
                    main_window = self.window()
                    ModernSaveCompletionDialog.show_save_completion(
                        main_window,
                        "저장 완료",
                        f"다중 프로젝트 순위 이력이 성공적으로 저장되었습니다.\n\n프로젝트 개수: {len(project_ids)}개",
                        file_path
                    )
                    return True
                else:
                    log_manager.add_log("❌ 다중 프로젝트 Excel 파일 저장에 실패했습니다.", "error")
                    return False
            return False
            
        except Exception as e:
            logger.error(f"다중 프로젝트 내보내기 오류: {e}")
            return False

