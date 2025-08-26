"""
네이버 카페 DB 추출기 결과 위젯 (우측 패널)
추출된 사용자, 추출 기록 탭으로 구성된 테이블 위젯
"""
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QTableWidgetItem, 
    QHeaderView, QApplication, QDialog, QPushButton,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from src.toolbox.ui_kit import ModernStyle, ModernTableWidget, tokens
from src.toolbox.ui_kit.components import ModernButton
from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
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
        layout.setSpacing(tokens.GAP_16)
        
        # 탭 위젯
        self.tabs = QTabWidget()
        tab_radius = tokens.RADIUS_SM
        tab_padding = tokens.GAP_10
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {tab_radius}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                padding: {tab_padding}px;
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                padding: {tokens.GAP_12}px {tokens.GAP_20}px;
                margin-right: {tokens.GAP_2}px;
                border-top-left-radius: {tab_radius}px;
                border-top-right-radius: {tab_radius}px;
                font-weight: 600;
                font-size: {tokens.get_font_size('normal')}px;
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
        layout.setSpacing(tokens.GAP_16)
        
        # 사용자 테이블 (ModernTableWidget 사용 - 체크박스 없음)
        self.users_table = ModernTableWidget(
            columns=["번호", "사용자 ID", "닉네임", "추출 시간"],
            has_checkboxes=False,  # 사용자 테이블은 체크박스 없음
            has_header_checkbox=False
        )
        
        # 컬럼 너비 설정 (체크박스가 없으므로 자유롭게 설정 가능)
        header = self.users_table.horizontalHeader()
        header.resizeSection(0, tokens.GAP_50)   # 번호 
        header.resizeSection(1, 150)  # 사용자 ID
        header.resizeSection(2, 150)  # 닉네임
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
        layout.setSpacing(tokens.GAP_16)
        
        # 상단 정보
        top_layout = QHBoxLayout()
        
        self.history_count_label = QLabel("총 기록: 0개")
        history_font_size = tokens.get_font_size('normal')
        self.history_count_label.setStyleSheet(f"""
            QLabel {{
                font-size: {history_font_size}px;
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
        
        # 기록 테이블 (ModernTableWidget 사용)
        self.history_table = ModernTableWidget(
            columns=["", "날짜", "카페명", "게시판명", "추출수", "페이지"],
            has_checkboxes=True,  # 히스토리 테이블은 체크박스 있음
            has_header_checkbox=True
        )
        
        # 컬럼 너비 설정 (체크박스 컬럼 제외하고 나머지만 설정)
        history_header = self.history_table.horizontalHeader()
        # history_header.resizeSection(0, 80)   # 선택 체크박스 - ModernTableWidget에서 자동 처리
        history_header.resizeSection(1, 110)  # 날짜 + 시간
        history_header.resizeSection(2, 140)  # 카페명
        history_header.resizeSection(3, 130)  # 게시판명 
        history_header.resizeSection(4, 80)   # 추출수
        history_header.resizeSection(5, 100)  # 페이지
        
        # 행 높이는 ModernTableWidget 기본값(35px) 사용
        
        # 선택 상태 변경 시그널 연결
        self.history_table.selection_changed.connect(self.update_selection_buttons)
        
        layout.addWidget(self.history_table)
        
        # 버튼 연결
        self.download_selected_button.clicked.connect(self.download_selected_history)
        self.delete_selected_button.clicked.connect(self.delete_selected_history)
        
        # ModernTableWidget에서 헤더 체크박스 자동 처리됨
        
        return tab
    
    def update_selection_buttons(self):
        """선택된 항목 수에 따라 버튼 텍스트 업데이트 (ModernTableWidget API 사용)"""
        # 선택된 항목 수 계산
        selected_count = self.history_table.get_selected_count()
        
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
            self.history_table.clear_table()
            
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
        """기록 테이블에 추가 (ModernTableWidget API 사용)"""
        # 날짜 (생성 시간)
        date_str = task.created_at.strftime("%Y-%m-%d %H:%M") if task.created_at else ""
        
        # 페이지 (시작페이지-종료페이지 형식)
        page_range = f"{task.start_page}-{task.end_page}"
        
        # 데이터 추가 (체크박스 포함)
        row = self.history_table.add_row_with_data([
            date_str,  # 날짜
            task.cafe_info.name,  # 카페명
            task.board_info.name,  # 게시판명
            str(task.total_extracted),  # 추출수
            page_range  # 페이지
        ], checkable=True)
        
        # task_id를 날짜 셀에 숨김 데이터로 저장
        date_item = self.history_table.item(row, 0)  # 날짜 셀 (첫 번째 컬럼)
        if date_item:
            date_item.setData(Qt.UserRole, task.task_id)
        
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
        
        # UI 레이어에서 다이얼로그 처리 후 service 호출 (CLAUDE.md: UI 분리)
        format_type = self.show_save_format_dialog(len(users_data))
        if format_type:
            self.export_users_data_internal(users_data, format_type, self)
    
    def show_save_format_dialog(self, users_count: int) -> str:
        """저장 포맷 선택 다이얼로그 표시 - UI 레이어 책임"""
        try:
            # 원본과 동일한 저장 방식 선택 다이얼로그
            dialog = QDialog(self)
            dialog.setWindowTitle("저장 방식 선택")
            dialog.setFixedSize(600, 300)
            dialog.setModal(True)
            
            # 레이아웃
            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            layout.setContentsMargins(30, 30, 30, 30)
            
            # 제목
            title_label = QLabel("선택된 기록의 저장 방식을 선택해주세요")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3748;")
            layout.addWidget(title_label)
            
            # 설명
            desc_label = QLabel(f"• Excel: 사용자ID, 닉네임 등 전체 정보\n• Meta CSV: 이메일 형태로 Meta 광고 활용 가능\n• 사용자: {users_count}명")
            desc_label.setStyleSheet("font-size: 12px; color: #4a5568; line-height: 1.4;")
            layout.addWidget(desc_label)
            
            # 버튼 레이아웃
            button_layout = QHBoxLayout()
            button_layout.setSpacing(20)
            button_layout.setContentsMargins(20, 0, 20, 0)
            
            excel_button = QPushButton("📊 Excel 파일")
            excel_button.setStyleSheet("""
                QPushButton {
                    background-color: #3182ce;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #2c5aa0;
                }
            """)
            
            meta_button = QPushButton("📧 Meta CSV")
            meta_button.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #c53030;
                }
            """)
            
            cancel_button = QPushButton("취소")
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #718096;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #4a5568;
                }
            """)
            
            button_layout.addWidget(excel_button)
            button_layout.addWidget(meta_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # 결과 변수
            result = None
            
            def on_excel():
                nonlocal result
                result = "excel"
                dialog.accept()
            
            def on_meta():
                nonlocal result
                result = "meta_csv"
                dialog.accept()
            
            def on_cancel():
                nonlocal result
                result = None
                dialog.reject()
            
            excel_button.clicked.connect(on_excel)
            meta_button.clicked.connect(on_meta)
            cancel_button.clicked.connect(on_cancel)
            
            # 다이얼로그 화면 중앙 위치 설정
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            center_x = screen_rect.x() + screen_rect.width() // 2 - dialog.width() // 2
            center_y = screen_rect.y() + screen_rect.height() // 2 - dialog.height() // 2
            dialog.move(center_x, center_y)
            
            dialog.exec()
            
            return result
                
        except Exception as e:
            logger.error(f"저장 포맷 선택 다이얼로그 오류: {e}")
            return None
    
    def export_users_data_internal(self, users_data: list, format_type: str, parent_widget=None) -> bool:
        """사용자 데이터 내보내기 - UI 레이어에서 처리"""
        try:
            # 선택된 형식으로 내보내기
            if format_type == "excel":
                return self.export_to_excel_with_dialog(users_data, parent_widget)
            elif format_type == "meta_csv":
                return self.export_to_meta_csv_with_dialog(users_data, parent_widget)
            else:
                logger.warning(f"지원하지 않는 내보내기 형식: {format_type}")
                return False
                
        except Exception as e:
            logger.error(f"사용자 데이터 내보내기 오류: {e}")
            return False
            
    def download_selected_history(self):
        """선택된 기록 다운로드 - Excel/Meta CSV 선택 다이얼로그"""
        selected_tasks = []
        selected_data = []
        
        # 임시: DB에 있는 모든 task_id 확인
        try:
            from src.foundation.db import get_db
            db = get_db()
            all_tasks = db.list_cafe_extraction_tasks()
            logger.info(f"[DEBUG] DB에 있는 모든 task들: {[(t.get('task_id'), type(t.get('task_id'))) for t in all_tasks]}")
        except Exception as e:
            logger.warning(f"[DEBUG] 모든 task 조회 실패: {e}")
        
        # 선택된 항목 찾기 (ModernTableWidget API 사용)
        for row in self.history_table.get_checked_rows():
            date_item = self.history_table.item(row, 0)  # 첫 번째 컬럼 (날짜)
            if date_item:
                # 숨김 데이터에서 task_id 가져오기
                task_id = date_item.data(Qt.UserRole)
                logger.info(f"[UI] row={row}, task_id={repr(task_id)}, type={type(task_id).__name__}")
                if task_id is not None:
                    selected_tasks.append(task_id)
                    
                    # 해당 기록의 사용자 데이터 가져오기 - service 경유 (CLAUDE.md: UI는 service 경유)
                    task_users = self.service.get_users_by_task_id(task_id)
                    logger.info(f"[UI] task_users 조회 결과: {len(task_users)}개")
                    if not task_users:
                        logger.warning(f"[UI] task_id={task_id}에 대한 사용자 데이터가 없습니다. DB 쿼리 확인 필요.")
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
            ModernInfoDialog.warning(self, "데이터 없음", "선택된 기록에 사용자 데이터가 없습니다.")
            return
        
        # UI 레이어에서 다이얼로그 처리 (CLAUDE.md: UI 분리)
        format_type = self.show_save_format_dialog(len(selected_data))
        if format_type:
            success = self.export_users_data_internal(selected_data, format_type, self)
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
        """선택된 기록 삭제 (ModernTableWidget API 사용)"""
        selected_tasks = []
        selected_rows = []
        
        # 선택된 항목 찾기
        for row in self.history_table.get_checked_rows():
            date_item = self.history_table.item(row, 0)  # 첫 번째 컬럼 (날짜)
            if date_item:
                # 숨김 데이터에서 task_id 가져오기
                task_id = date_item.data(Qt.UserRole)
                if task_id is not None:
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
        
        # 선택된 항목 찾기 (ModernTableWidget API 사용)
        for row in self.history_table.get_checked_rows():
            task_id_item = self.history_table.item(row, 0)  # 첫 번째 컬럼 (날짜)
            if task_id_item:
                task_id = task_id_item.data(Qt.UserRole)  # 숨김 데이터에서 task_id 가져오기
                if task_id is not None:
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
        
        # UI 다이얼로그로 엑셀 내보내기 (CLAUDE.md: UI 다이얼로그는 UI 레이어)
        success = self.export_to_excel_with_dialog(selected_data, self)
        
        if success:
            log_manager.add_log(f"선택된 {len(selected_tasks)}개 기록의 사용자 데이터 엑셀 내보내기 완료 (총 {len(selected_data)}명)", "success")
    
    
    # Legacy header checkbox method removed - ModernTableWidget handles automatically
    def export_to_excel_with_dialog(self, users_data: list, parent_widget=None) -> bool:
        """엑셀로 내보내기 - 파일 선택 다이얼로그 포함"""
        try:
            # 1. 파일 저장 다이얼로그
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget or self,
                "엑셀 파일로 저장",
                "네이버카페_사용자_목록.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if not file_path:
                return False
            
            # 2. 사용자 데이터를 ExtractedUser 객체로 변환
            users = []
            for row_data in users_data:
                if len(row_data) >= 4:
                    user = ExtractedUser(
                        user_id=row_data[1],
                        nickname=row_data[2],
                        last_seen=datetime.strptime(row_data[3], "%Y-%m-%d %H:%M:%S") if row_data[3] else datetime.now(),
                        article_count=1
                    )
                    users.append(user)
            
            # 3. service 경유로 실제 파일 저장
            success = self.service.export_to_excel(file_path, users)
            
            if success:
                # 4. 성공 다이얼로그 표시
                filename = Path(file_path).name
                user_count = len([row_data for row_data in users_data if len(row_data) >= 2])
                self._show_save_completion_dialog(
                    "엑셀 파일 저장 완료",
                    f"엑셀 파일이 성공적으로 저장되었습니다.\n\n파일명: {filename}\n사용자 수: {user_count}명",
                    file_path
                )
                logger.info(f"엑셀 파일 저장 완료: {filename} (사용자 {user_count}명)")
            else:
                QMessageBox.critical(parent_widget or self, "오류", "엑셀 저장 중 오류가 발생했습니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"엑셀 내보내기 (대화상자 포함) 실패: {e}")
            QMessageBox.critical(parent_widget or self, "오류", f"엑셀 저장 중 오류가 발생했습니다.\n{str(e)}")
            return False

    def export_to_meta_csv_with_dialog(self, users_data: list, parent_widget=None) -> bool:
        """Meta CSV로 내보내기 - 파일 선택 다이얼로그 포함"""
        try:
            # 1. 파일 저장 다이얼로그
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget or self,
                "Meta CSV 파일로 저장",
                "네이버카페_Meta광고용.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return False
            
            # 2. 사용자 데이터를 ExtractedUser 객체로 변환
            users = []
            for row_data in users_data:
                if len(row_data) >= 4:
                    user = ExtractedUser(
                        user_id=row_data[1],
                        nickname=row_data[2],
                        last_seen=datetime.strptime(row_data[3], "%Y-%m-%d %H:%M:%S") if row_data[3] else datetime.now(),
                        article_count=1
                    )
                    users.append(user)
            
            # 3. service 경유로 실제 파일 저장
            success = self.service.export_to_meta_csv(file_path, users)
            
            if success:
                # 4. 성공 다이얼로그 표시 (도메인 정보 동적 가져오기)
                filename = Path(file_path).name
                user_count = len([row_data for row_data in users_data if len(row_data) >= 2])
                
                # service에서 도메인 정보 가져오기 (하드코딩 방지)
                domain_count = self.service.get_meta_csv_domain_count()
                domains = self.service.get_meta_csv_domains()
                domain_list = ", ".join(domains)
                
                self._show_save_completion_dialog(
                    "Meta CSV 저장 완료",
                    f"Meta 광고용 CSV 파일이 성공적으로 저장되었습니다.\n\n파일명: {filename}\n사용자 ID: {user_count}개\n생성된 이메일: {user_count*domain_count}개\n({domain_list})",
                    file_path
                )
                logger.info(f"Meta CSV 파일 저장 완료: {filename} (사용자 {user_count}명)")
            else:
                QMessageBox.critical(parent_widget or self, "오류", "CSV 저장 중 오류가 발생했습니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"Meta CSV 내보내기 (대화상자 포함) 실패: {e}")
            QMessageBox.critical(parent_widget or self, "오류", f"CSV 저장 중 오류가 발생했습니다.\n{str(e)}")
            return False

    def _show_save_completion_dialog(self, title: str, message: str, file_path: str):
        """저장 완료 다이얼로그 표시"""
        try:
            # toolbox 공용 다이얼로그 사용
            ModernSaveCompletionDialog.show_save_completion(
                self, 
                title, 
                message, 
                file_path
            )
        except Exception as e:
            logger.warning(f"저장 완료 다이얼로그 표시 실패: {e}")
            # 폴백: 일반 메시지박스
            QMessageBox.information(self, title, message)
    
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
