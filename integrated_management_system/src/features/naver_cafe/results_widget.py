"""
네이버 카페 DB 추출기 결과 위젯 (우측 패널)
추출된 사용자, 추출 기록 탭으로 구성된 테이블 위젯
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QTableWidget, QTableWidgetItem, 
    QHeaderView, QApplication, QCheckBox
)
from PySide6.QtCore import Qt

from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.components import ModernButton
from src.desktop.common_log import log_manager
from src.foundation.logging import get_logger
from .models import ExtractedUser, ExtractionTask
from .service import NaverCafeExtractionService

logger = get_logger("features.naver_cafe.results_widget")


class NaverCafeResultsWidget(QWidget):
    """네이버 카페 추출 결과 위젯 (우측 패널)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # service 초기화 (CLAUDE.md: UI는 service 경유)
        self.service = NaverCafeExtractionService()
        self.setup_ui()
        # 초기 데이터 로드
        self.load_initial_data()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
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
        
        # 추출된 사용자 탭
        users_tab = self.create_users_tab()
        self.tabs.addTab(users_tab, "👥 추출된 사용자")
        
        # 추출 기록 탭
        history_tab = self.create_history_tab()
        self.tabs.addTab(history_tab, "📜 추출 기록")
        
        layout.addWidget(self.tabs)
    
    def load_initial_data(self):
        """초기 데이터 로드"""
        try:
            # 기존 사용자 데이터 로드
            self.refresh_users_table()
            
            # 기존 추출 기록 로드
            self.refresh_history_table()
            
            logger.info("초기 데이터 로드 완료")
        except Exception as e:
            logger.error(f"초기 데이터 로드 실패: {e}")
        
    def create_users_tab(self) -> QWidget:
        """추출된 사용자 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 사용자 테이블
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["번호", "사용자 ID", "닉네임", "추출 시간"])
        
        # 테이블 스타일 (선택 시 파란 배경 + 흰색 글씨)
        self.users_table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                alternate-background-color: {ModernStyle.COLORS['bg_input']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
                color: {ModernStyle.COLORS['text_primary']};
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
        
        # 헤더 설정
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.verticalHeader().setVisible(False)
        
        # 컬럼 너비 설정
        header = self.users_table.horizontalHeader()
        header.resizeSection(0, int(80 * 0.8))   # 번호 (80 → 64)
        header.resizeSection(1, 200)  # 사용자 ID
        header.resizeSection(2, int(180 * 0.8))  # 닉네임 (180 → 144)
        header.resizeSection(3, 150)  # 추출 시간
        
        layout.addWidget(self.users_table)
        
        # 하단 통계 및 버튼
        bottom_layout = QHBoxLayout()
        
        # 통계 라벨
        self.users_count_label = QLabel("추출된 사용자: 0명")
        self.users_count_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['primary']};
            }}
        """)
        
        # 버튼들
        self.copy_button = ModernButton("📋 복사", "secondary")
        self.copy_button.setMinimumSize(130, int(36 * 0.8))  # 너비 130, 높이는 0.8배 (130x29)
        
        self.save_button = ModernButton("💾 저장", "success")
        self.save_button.setMinimumSize(130, int(36 * 0.8))  # 너비 130, 높이는 0.8배 (130x29)
        
        bottom_layout.addWidget(self.users_count_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.copy_button)
        bottom_layout.addWidget(self.save_button)
        
        layout.addLayout(bottom_layout)
        
        # 버튼 연결
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.save_button.clicked.connect(self.show_save_dialog)
        
        return tab
        
    def create_history_tab(self) -> QWidget:
        """추출 기록 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # 상단 정보
        top_layout = QHBoxLayout()
        
        self.history_count_label = QLabel("총 기록: 0개")
        self.history_count_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        
        self.download_selected_button = ModernButton("💾 선택 다운로드", "success")
        self.delete_selected_button = ModernButton("🗑️ 선택 삭제", "danger")
        
        top_layout.addWidget(self.history_count_label)
        top_layout.addStretch()
        top_layout.addWidget(self.download_selected_button)
        top_layout.addWidget(self.delete_selected_button)
        
        layout.addLayout(top_layout)
        
        # 기록 테이블
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "", "날짜", "카페명", "게시판명", "추출수", "페이지"
        ])
        
        # 테이블 스타일 (원본과 동일하게 선택 배경색 파란색, 텍스트 흰색)
        self.history_table.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                alternate-background-color: {ModernStyle.COLORS['bg_input']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 12px 8px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
                min-height: 30px;
                color: {ModernStyle.COLORS['text_primary']};
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
                min-height: 25px;
                max-height: 25px;
            }}
        """)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.verticalHeader().setVisible(False)
        
        # 컬럼 너비 설정 (원본과 동일하게)
        history_header = self.history_table.horizontalHeader()
        history_header.resizeSection(0, 80)   # 선택 체크박스
        history_header.resizeSection(1, 130)  # 날짜 + 시간 (더 넓게)
        history_header.resizeSection(2, 200)  # 카페명
        history_header.resizeSection(3, 144)  # 게시판명 
        history_header.resizeSection(4, 100)  # 추출수
        history_header.resizeSection(5, 120)  # 페이지
        
        # 행 높이 설정 (더 넓게)
        self.history_table.verticalHeader().setDefaultSectionSize(45)  # 행 높이 45px
        
        layout.addWidget(self.history_table)
        
        # 버튼 연결
        self.download_selected_button.clicked.connect(self.download_selected_history)
        self.delete_selected_button.clicked.connect(self.delete_selected_history)
        
        # 헤더에 체크박스 설정 (원본과 동일하게) - 테이블 생성 후 지연 실행
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.setup_header_checkbox)
        
        return tab
    
    def update_selection_buttons(self):
        """선택된 항목 수에 따라 버튼 텍스트 업데이트"""
        selected_count = 0
        
        # 선택된 체크박스 수 계산
        for row in range(self.history_table.rowCount()):
            checkbox_widget = self.history_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                        selected_count += 1
        
        # 버튼 텍스트 업데이트
        if selected_count > 0:
            self.download_selected_button.setText(f"💾 선택 다운로드 ({selected_count})")
            self.delete_selected_button.setText(f"🗑️ 선택 삭제 ({selected_count})")
        else:
            self.download_selected_button.setText("💾 선택 다운로드")
            self.delete_selected_button.setText("🗑️ 선택 삭제")
        
    def add_user_to_table(self, user: ExtractedUser):
        """테이블에 사용자 추가"""
        row = self.users_table.rowCount()
        self.users_table.insertRow(row)
        
        # 번호
        self.users_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        
        # 사용자 ID
        self.users_table.setItem(row, 1, QTableWidgetItem(user.user_id))
        
        # 닉네임
        self.users_table.setItem(row, 2, QTableWidgetItem(user.nickname))
        
        # 추출 시간
        time_str = user.last_seen.strftime("%Y-%m-%d %H:%M:%S") if user.last_seen else ""
        self.users_table.setItem(row, 3, QTableWidgetItem(time_str))
        
        # 통계 업데이트
        self.update_users_count()
        
    def update_users_count(self):
        """사용자 수 업데이트"""
        count = self.users_table.rowCount()
        self.users_count_label.setText(f"추출된 사용자: {count}명")
        
    def refresh_users_table(self):
        """사용자 테이블 새로고침 - 메모리 기반 (세션 중에만 유지)"""
        # 테이블 클리어
        self.users_table.setRowCount(0)
        
        # 메모리 기반 사용자 목록은 세션 중에만 유지되므로 초기화 시에는 비어있음
        # 실제 추출 시에만 실시간으로 추가됨
            
    def refresh_history_table(self):
        """기록 테이블 새로고침 - service 경유 (CLAUDE.md 구조 준수)"""
        try:
            # 테이블 클리어
            self.history_table.setRowCount(0)
            
            # service 경유로 기록 가져오기 (CLAUDE.md: UI는 service 경유만)
            tasks = self.service.get_extraction_history()
            
            # ExtractionTask 객체를 테이블에 표시 (service에서 이미 변환됨)
            for task in tasks:
                try:
                    self.add_history_to_table(task)
                except Exception as e:
                    logger.error(f"추출 기록 표시 실패: {e}")
                    continue
            
            # 기록 수 업데이트
            self.history_count_label.setText(f"총 기록: {len(tasks)}개")
            
        except Exception as e:
            logger.error(f"추출 기록 테이블 새로고침 실패: {e}")
        
    def add_history_to_table(self, task: ExtractionTask):
        """기록 테이블에 추가 (원본과 동일하게)"""
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        # 선택 체크박스 (중앙 정렬을 위한 컨테이너 위젯 사용)
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        
        checkbox = QCheckBox()
        checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAxNCAxNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjUgMy41TDUuNSA5LjVMMi41IDYuNSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            QCheckBox::indicator:hover {
                border-color: #999999;
                background-color: #f8f9fa;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }
        """)
        
        # 체크박스를 레이아웃에 추가
        checkbox_layout.addWidget(checkbox)
        
        # 체크박스 상태 변경 시 버튼 텍스트 업데이트
        checkbox.stateChanged.connect(self.update_selection_buttons)
        self.history_table.setCellWidget(row, 0, checkbox_widget)
        
        # 날짜 (생성 시간)
        date_str = task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else ""
        date_item = QTableWidgetItem(date_str)
        # task_id를 숨김 데이터로 저장
        date_item.setData(Qt.UserRole, task.task_id)
        self.history_table.setItem(row, 1, date_item)
        
        # 카페명
        self.history_table.setItem(row, 2, QTableWidgetItem(task.cafe_info.name))
        
        # 게시판명
        self.history_table.setItem(row, 3, QTableWidgetItem(task.board_info.name))
        
        # 추출수
        self.history_table.setItem(row, 4, QTableWidgetItem(str(task.total_extracted)))
        
        # 페이지 (시작페이지-종료페이지 형식)
        page_range = f"{task.start_page}-{task.end_page}"
        self.history_table.setItem(row, 5, QTableWidgetItem(page_range))
        
    def copy_to_clipboard(self):
        """엑셀 호환 형식으로 클립보드 복사 (원본과 동일)"""
        if self.users_table.rowCount() == 0:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "데이터 없음", "복사할 데이터가 없습니다.")
            return
        
        try:
            # 엑셀 호환 형식으로 데이터 구성 (탭으로 구분, 줄바꿈으로 행 구분)
            lines = []
            
            # 헤더 추가
            headers = ["번호", "사용자 ID", "닉네임", "추출 시간"]
            lines.append("\t".join(headers))
            
            # 데이터 행들 추가
            for row in range(self.users_table.rowCount()):
                row_data = []
                for col in range(self.users_table.columnCount()):
                    item = self.users_table.item(row, col)
                    row_data.append(item.text() if item else "")
                lines.append("\t".join(row_data))
            
            # 전체 텍스트 구성
            clipboard_text = "\n".join(lines)
            
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_text)
            
            log_manager.add_log(f"{self.users_table.rowCount()}개 사용자 데이터 엑셀 호환 형식으로 클립보드 복사 완료", "success")
            
            # 모던한 복사 완료 다이얼로그
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.success(
                self,
                "복사 완료",
                f"엑셀에 붙여넣을 수 있는 형식으로 복사되었습니다.\n\n"
                f"데이터: {self.users_table.rowCount()}행 (헤더 포함 {self.users_table.rowCount()+1}행)\n"
                f"컬럼: 번호, 사용자 ID, 닉네임, 추출 시간"
            )
            
        except Exception as e:
            # 모던한 에러 다이얼로그
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "복사 오류", f"클립보드 복사 중 오류가 발생했습니다: {str(e)}")
            logger.error(f"클립보드 복사 오류: {e}")
        
    def show_save_dialog(self):
        """저장 다이얼로그 표시 - CLAUDE.md: UI는 service 경유"""
        # 테이블 데이터 검증 먼저 수행
        if self.users_table.rowCount() == 0:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "데이터 없음", "내보낼 사용자 데이터가 없습니다.\n\n먼저 카페에서 사용자를 추출해주세요.")
            return
        
        # 테이블 데이터를 리스트로 변환
        users_data = []
        for row in range(self.users_table.rowCount()):
            row_data = []
            for col in range(self.users_table.columnCount()):
                item = self.users_table.item(row, col)
                row_data.append(item.text() if item else "")
            users_data.append(row_data)
        
        # 변환된 데이터가 실제로 있는지 재확인
        if not users_data:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "데이터 없음", "내보낼 사용자 데이터가 없습니다.")
            return
        
        # service 경유로 저장 방식 선택 및 내보내기 (CLAUDE.md: UI 오케스트레이션은 service)
        self.service.show_save_format_dialog_and_export(users_data, self)
    
            
    def download_selected_history(self):
        """선택된 기록 다운로드 - Excel/Meta CSV 선택 다이얼로그"""
        selected_tasks = []
        selected_data = []
        
        # 선택된 항목 찾기
        for row in range(self.history_table.rowCount()):
            checkbox_widget = self.history_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                        date_item = self.history_table.item(row, 1)
                        if date_item:
                            # 숨김 데이터에서 task_id 가져오기
                            task_id = date_item.data(Qt.UserRole)
                            if task_id:
                                selected_tasks.append(task_id)
                                
                                # 해당 기록의 사용자 데이터 가져오기 - service 경유 (CLAUDE.md: UI는 service 경유)
                                task_users = self.service.get_users_by_task_id(task_id)
                                for user in task_users:
                                    user_data = [
                                        str(len(selected_data) + 1),  # 번호
                                        user.user_id,                # 사용자 ID
                                        user.nickname,               # 닉네임
                                        user.last_seen.strftime("%Y-%m-%d %H:%M:%S") if user.last_seen else ""  # 추출 시간
                                    ]
                                    selected_data.append(user_data)
        
        if not selected_tasks:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "선택 없음", "다운로드할 기록을 선택해주세요.")
            return
        
        if not selected_data:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "데이터 없음", "선택된 기록에 다운로드할 사용자 데이터가 없습니다.")
            return
        
        # service 경유로 저장 방식 선택 및 내보내기 (CLAUDE.md: UI 오케스트레이션은 service)
        success = self.service.show_save_format_dialog_and_export(selected_data, self)
        
        if success:
            log_manager.add_log(f"선택된 {len(selected_tasks)}개 기록의 사용자 데이터 다운로드 완료 (총 {len(selected_data)}명)", "success")
        
            
    def on_user_extracted(self, user: ExtractedUser):
        """사용자 추출 시 실시간 테이블 업데이트"""
        self.add_user_to_table(user)
        
    def on_extraction_completed(self, result):
        """추출 완료 시 처리"""
        # 테이블 새로고침
        self.refresh_users_table()
        self.refresh_history_table()
    
    def refresh_users_table(self):
        """사용자 테이블 새로고침 - 메모리 기반 (세션 중에만 유지)"""
        # 메모리 기반 사용자 목록은 세션 중에만 유지됨
        
        # 테이블 클리어
        self.users_table.setRowCount(0)
        
        # 메모리 기반으로 현재 세션의 추출 데이터만 표시
        
        self.update_users_count()
    
    def on_data_cleared(self):
        """새로운 추출 시작 시 사용자 테이블만 클리어 (기록은 유지)"""
        self.users_table.setRowCount(0)
        self.update_users_count()
        log_manager.add_log("새로운 추출 시작 - 사용자 테이블 클리어", "info")
    
    
    def delete_selected_history(self):
        """선택된 기록 삭제"""
        selected_tasks = []
        selected_rows = []
        
        # 선택된 항목 찾기
        for row in range(self.history_table.rowCount()):
            checkbox_widget = self.history_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                        date_item = self.history_table.item(row, 1)
                        if date_item:
                            # 숨김 데이터에서 task_id 가져오기
                            task_id = date_item.data(Qt.UserRole)
                            if task_id:
                                selected_tasks.append(task_id)
                                selected_rows.append(row)
        
        if not selected_tasks:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "선택 없음", "삭제할 기록을 선택해주세요.")
            return
        
        # 확인 다이얼로그 - 순위추적과 동일한 스타일
        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
        reply = ModernConfirmDialog.question(
            self,
            "추출 기록 삭제",
            f"선택된 {len(selected_tasks)}개의 추출 기록을 삭제하시겠습니까?\n\n⚠️ 모든 추출 결과가 함께 삭제됩니다.\n\n이 작업은 되돌릴 수 없습니다.",
            "삭제",
            "취소"
        )
        
        if reply:
            # Foundation DB에서 직접 선택된 기록들 삭제 (순위추적과 동일한 방식)
            from src.foundation.db import get_db
            db = get_db()
            for task_id in selected_tasks:
                db.delete_cafe_extraction_task(task_id)
            
            # 테이블에서 선택된 행들 삭제 (역순으로 삭제)
            for row in sorted(selected_rows, reverse=True):
                self.history_table.removeRow(row)
            
            # 기록 수 업데이트
            self.history_count_label.setText(f"총 기록: {self.history_table.rowCount()}개")
            
            # 버튼 텍스트 업데이트
            self.update_selection_buttons()
            
            log_manager.add_log(f"{len(selected_tasks)}개 추출 기록 삭제 완료", "info")
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.success(self, "삭제 완료", f"{len(selected_tasks)}개의 추출 기록이 삭제되었습니다.")
    
    def export_selected_history(self):
        """선택된 기록들을 엑셀로 내보내기"""
        selected_tasks = []
        selected_data = []
        
        # 선택된 항목 찾기
        for row in range(self.history_table.rowCount()):
            checkbox = self.history_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                task_id_item = self.history_table.item(row, 1)
                if task_id_item:
                    task_id = task_id_item.text()
                    selected_tasks.append(task_id)
                    
                    # 해당 기록의 사용자 데이터 가져오기 - Foundation DB에서 조회
                    task_users = self._get_users_by_task_id(task_id)
                    for user in task_users:
                        user_data = [
                            str(len(selected_data) + 1),  # 번호
                            user.user_id,                # 사용자 ID
                            user.nickname,               # 닉네임
                            user.last_seen.strftime("%Y-%m-%d %H:%M:%S") if user.last_seen else ""  # 추출 시간
                        ]
                        selected_data.append(user_data)
        
        if not selected_tasks:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "선택 없음", "내보낼 기록을 선택해주세요.")
            return
        
        if not selected_data:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            ModernInfoDialog.warning(self, "데이터 없음", "선택된 기록에 내보낼 사용자 데이터가 없습니다.")
            return
        
        # service 경유로 엑셀로 내보내기 (CLAUDE.md: UI 오케스트레이션은 service)
        success = self.service.export_to_excel_with_dialog(selected_data, self)
        
        if success:
            log_manager.add_log(f"선택된 {len(selected_tasks)}개 기록의 사용자 데이터 엑셀 내보내기 완료 (총 {len(selected_data)}명)", "success")
    
    
    def setup_header_checkbox(self):
        """QTableWidget 헤더에 체크박스 추가 (기존 방식)"""
        try:
            # 헤더용 체크박스 생성 (기존 스타일과 동일)
            self.header_checkbox = QCheckBox()
            self.header_checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                    padding: 0px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #007bff;
                    border-color: #007bff;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iMTQiIHZpZXdCb3g9IjAgMCAxNCAxNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTExLjUgMy41TDUuNSA5LjVMMi41IDYuNSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
                }
                QCheckBox::indicator:hover {
                    border-color: #999999;
                    background-color: #f8f9fa;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #0056b3;
                    border-color: #0056b3;
                }
            """)
            self.header_checkbox.stateChanged.connect(self.on_header_checkbox_changed)
            
            # 헤더 위젯 컨테이너 생성
            self.header_widget = QWidget()
            header_layout = QHBoxLayout(self.header_widget)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(self.header_checkbox)
            
            # 헤더 설정
            header = self.history_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Fixed)
            header.resizeSection(0, 80)
            
            # 첫 번째 컬럼 헤더를 빈 문자열로 설정
            header_item = self.history_table.horizontalHeaderItem(0)
            if not header_item:
                header_item = QTableWidgetItem("")
                self.history_table.setHorizontalHeaderItem(0, header_item)
            header_item.setText("")
            
            # 헤더에 위젯 배치
            self.position_header_checkbox()
            
        except Exception as e:
            logger.error(f"헤더 체크박스 설정 실패: {e}")
    
    def position_header_checkbox(self):
        """헤더 체크박스를 헤더에 배치 (헤더와 함께 스크롤)"""
        try:
            if not hasattr(self, 'header_widget') or not self.header_widget:
                return
                
            # QTableWidget의 헤더 영역 위치 계산
            header = self.history_table.horizontalHeader()
            
            # 안전한 위치 계산
            if header.sectionSize(0) <= 0:
                return
            
            # 헤더 위젯을 헤더의 자식으로 설정 (헤더와 함께 움직임)
            if self.header_widget.parent() != header:
                self.header_widget.setParent(header)
            
            # 첫 번째 섹션 위치 계산
            section_pos = header.sectionPosition(0)
            section_width = header.sectionSize(0)
            header_height = header.height()
            
            # 헤더 섹션에 정확히 맞춤
            self.header_widget.setFixedSize(section_width, header_height)
            self.header_widget.move(section_pos, 0)  # 첫 번째 섹션 위치
            self.header_widget.show()
            self.header_widget.raise_()
            
            # 투명한 배경 (헤더 배경이 보이도록)
            self.header_widget.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                }
            """)
            
        except Exception as e:
            logger.error(f"헤더 체크박스 위치 설정 실패: {e}")
    
    def on_header_checkbox_changed(self, state):
        """헤더 체크박스 상태 변경 시 전체 선택/해제"""
        checked = (state == 2)  # Qt.Checked = 2
        
        # 모든 행의 체크박스 상태 변경
        for row in range(self.history_table.rowCount()):
            checkbox_widget = self.history_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.blockSignals(True)  # 시그널 차단으로 무한루프 방지
                    checkbox.setChecked(checked)
                    checkbox.blockSignals(False)
        
        # 버튼 텍스트 업데이트
        self.update_selection_buttons()
    
    # ==================== 시그널 핸들러 메서드 ====================
    
    def on_user_extracted(self, user: ExtractedUser):
        """실시간 사용자 추출 시 테이블에 추가"""
        self.add_user_to_table(user)
    
    def on_extraction_completed(self, result: dict):
        """추출 완료 시 기록 테이블 새로고침"""
        try:
            # 기록 테이블 새로고침 (새로 저장된 기록을 포함하여)
            self.refresh_history_table()
            logger.info("추출 완료 후 기록 테이블 새로고침 완료")
        except Exception as e:
            logger.error(f"추출 완료 후 기록 테이블 새로고침 실패: {e}")
    
