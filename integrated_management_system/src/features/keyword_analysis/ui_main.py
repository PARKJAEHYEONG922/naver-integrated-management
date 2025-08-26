"""
키워드 분석 기능 UI
원본 통합관리프로그램의 키워드 검색기 UI 완전 복원
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QProgressBar, QMessageBox, QFileDialog,
    QFrame, QSizePolicy, QHeaderView
)
from PySide6.QtCore import Qt, QMetaObject, Q_ARG, Slot, Signal

from src.toolbox.ui_kit import (
    ModernStyle,
    ModernPrimaryButton, ModernSuccessButton, ModernDangerButton, 
    ModernCancelButton, ModernHelpButton
)
from src.toolbox.ui_kit.modern_table import ModernTableWidget
from src.toolbox.ui_kit import tokens
from src.desktop.common_log import log_manager
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog, ModernInfoDialog, ModernSaveCompletionDialog
from .worker import BackgroundWorker
from .service import analysis_manager
from .models import KeywordData
from src.toolbox import formatters
from src.toolbox.text_utils import parse_keywords, filter_unique_keywords_with_skipped
from src.foundation.logging import get_logger

logger = get_logger("features.keyword_analysis.ui")






class KeywordAnalysisWidget(QWidget):
    """키워드 분석 메인 위젯 - 원본 키워드 검색기 UI 완전 복원"""
    
    # 실시간 결과 추가를 위한 시그널
    keyword_result_ready = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.worker: BackgroundWorker = None
        self.search_results = []  # 검색 결과 저장 (원본과 동일)
        self.is_search_canceled = False  # 취소 상태 추적
        
        
        self.setup_ui()
        self.load_api_config()
        
        # 실시간 결과 추가 시그널 연결
        self.keyword_result_ready.connect(self._safe_add_keyword_result)
    
    def setup_ui(self):
        """원본 키워드 검색기 UI 레이아웃 - 반응형 적용"""
        main_layout = QVBoxLayout()
        # 토큰 기반 마진과 간격
        margin = tokens.GAP_16
        spacing = tokens.GAP_10
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 헤더 (제목 + 사용법 버튼)
        self.setup_header(main_layout)
        
        # 키워드 입력 + 검색/정지 버튼
        self.setup_input_section(main_layout)
        
        # 진행 상태
        self.setup_progress_section(main_layout)
        
        # 결과 테이블
        self.setup_results_section(main_layout)
        
        # 하단 버튼들 (Clear, Excel 저장 등)
        self.setup_bottom_buttons(main_layout)
        
        self.setLayout(main_layout)
    
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법 툴팁)"""
        header_layout = QHBoxLayout()
        
        # 제목 - 토큰 기반 폰트
        title_label = QLabel("🔍 키워드 검색기")
        title_font_size = tokens.get_font_size('title')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 다이얼로그 버튼
        self.help_button = ModernHelpButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()  # 오른쪽 여백
        
        layout.addLayout(header_layout)
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = (
            "📋 키워드 입력:\n"
            "• 분석하고 싶은 키워드를 입력해 주세요\n"
            "• 엔터 또는 쉼표(,)로 구분 가능합니다\n"
            "• 키워드 공백은 자동으로 제거되어 검색됩니다\n"
            "• 영문은 자동으로 대문자로 변환됩니다\n"
            "• 중복 키워드는 자동으로 제거됩니다\n\n"
            "📈 검색 결과:\n"
            "• 월검색량: 해당 키워드의 월 평균 검색량\n"
            "• 전체상품수: 네이버쇼핑 내 관련 상품 개수\n"
            "• 경쟁강도: 전체상품수 ÷ 월검색량 (낮을수록 좋음, 경쟁 적음)\n\n"
            "💾 기능:\n"
            "• 검색 결과를 Excel 파일로 내보내기 가능\n"
            "• 컬럼별 정렬 기능 지원 (클릭으로 오름차순/내림차순)\n"
            "• 실시간 진행률 표시\n\n"
            "🔧 사용 팁:\n"
            "• 여러 키워드를 한 번에 분석하여 효율성 향상\n"
            "• 경쟁강도가 낮은 키워드를 우선적으로 선택\n"
            "• 월검색량과 상품수를 함께 고려하여 시장 분석"
        )
        
        try:
            from src.toolbox.ui_kit.modern_dialog import ModernHelpDialog
            ModernHelpDialog.show_help(self, "키워드 검색기 사용법", help_text, self.help_button)
        except:
            QMessageBox.information(self, "키워드 검색기 사용법", help_text)
    
    def setup_input_section(self, layout):
        """키워드 입력 + 검색/정지 버튼 섹션 - 반응형"""
        input_frame = QFrame()
        # 고정 높이
        frame_height = 160
        input_frame.setFixedHeight(frame_height)
        
        # 토큰 기반 패딩과 테두리
        frame_padding = tokens.GAP_6
        border_radius = tokens.RADIUS_MD
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: {border_radius}px;
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: {frame_padding}px;
            }}
        """)
        
        input_layout = QVBoxLayout()
        
        # 키워드 입력 + 버튼 가로 배치
        input_row = QHBoxLayout()
        input_row_widget = QWidget()
        # 고정 내부 높이
        inner_height = frame_height - (frame_padding * 2) - 10  # 여유 공간
        input_row_widget.setFixedHeight(inner_height)
        
        # 텍스트 입력 - 반응형
        self.keyword_input = QTextEdit()
        self.keyword_input.setPlaceholderText("예: 아이폰 케이스, 갤럭시 충전기, 블루투스 이어폰")
        
        # 토큰 기반 텍스트 입력창 높이 및 스타일
        text_height = 80
        text_padding = tokens.GAP_6
        text_border_radius = tokens.RADIUS_SM
        text_font_size = tokens.get_font_size('normal')
        
        self.keyword_input.setMaximumHeight(text_height)
        self.keyword_input.setStyleSheet(f"""
            QTextEdit {{
                font-size: {text_font_size}px;
                padding: {text_padding}px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {text_border_radius}px;
                background-color: {ModernStyle.COLORS['bg_primary']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """)
        input_row.addWidget(self.keyword_input, 3)  # 비율 3 (더 넓게)
        
        # 버튼 컨테이너 - 토큰 기반
        button_container = QVBoxLayout()
        button_spacing = tokens.GAP_4
        button_container.setSpacing(button_spacing)
        
        # 검색 시작 버튼
        self.search_button = ModernPrimaryButton("🔍 검색")
        self.search_button.clicked.connect(self.start_search)
        button_container.addWidget(self.search_button)
        
        # 정지 버튼
        self.cancel_button = ModernCancelButton("⏹ 정지")
        self.cancel_button.clicked.connect(self.cancel_search)
        self.cancel_button.setEnabled(False)
        button_container.addWidget(self.cancel_button)
        
        input_row.addLayout(button_container)
        input_row_widget.setLayout(input_row)
        input_layout.addWidget(input_row_widget)
        
        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)
    
    def setup_progress_section(self, layout):
        """진행 상태 섹션 - 반응형"""
        progress_layout = QHBoxLayout()
        
        # 선택삭제 버튼
        self.delete_selected_button = ModernDangerButton("🗑 선택삭제")
        self.delete_selected_button.clicked.connect(self.delete_selected_results)
        self.delete_selected_button.setEnabled(False)  # 초기에는 비활성화
        progress_layout.addWidget(self.delete_selected_button)
        
        progress_layout.addStretch()  # 공간 확보
        
        # 진행률 바 - 토큰 기반
        self.progress_bar = QProgressBar()
        progress_height = 24
        progress_border_radius = tokens.RADIUS_SM
        progress_font_size = tokens.get_font_size('small')
        progress_max_width = 200
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {progress_border_radius}px;
                text-align: center;
                font-weight: 500;
                font-size: {progress_font_size}px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: {progress_border_radius - 2}px;
            }}
        """)
        self.progress_bar.setMaximumWidth(progress_max_width)
        self.progress_bar.setMinimumHeight(progress_height)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
    
    def setup_results_section(self, layout):
        """결과 테이블 섹션 - 반응형"""
        results_container = QVBoxLayout()
        
        
        # 테이블
        self.results_table = ModernTableWidget(
            columns=["", "키워드", "카테고리", "월검색량", "전체상품수", "경쟁강도"],
            has_checkboxes=True,
            has_header_checkbox=True
        )
        
        # 정렬 기능은 ModernTableWidget에서 기본 제공됨
        
        # 컬럼 너비 설정 (체크박스 포함 6개 컬럼)
        self.results_table.setColumnWidth(0, 50)   # 체크박스 (빈 헤더)
        self.results_table.setColumnWidth(1, 200)  # 키워드
        self.results_table.setColumnWidth(2, 450)  # 카테고리 
        self.results_table.setColumnWidth(3, 150)  # 월검색량
        self.results_table.setColumnWidth(4, 150)  # 전체상품수
        
        # 마지막 컬럼(경쟁강도)이 남은 공간을 채우도록 설정
        self.results_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        
        # 선택 상태 변경 시그널 연결
        self.results_table.selection_changed.connect(self.on_selection_changed)
        
        # 행 높이 자동 조정 (내용에 맞게)
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 텍스트 줄바꿈 활성화
        self.results_table.setWordWrap(True)
        
        results_container.addWidget(self.results_table)
        
        layout.addLayout(results_container)
    
    def on_selection_changed(self):
        """테이블 선택 상태 변경 시 호출"""
        # 선택된 행이 있으면 버튼들 활성화
        selected_count = len(self.results_table.get_checked_rows())
        total_count = self.results_table.rowCount()
        
        # 버튼 활성화 상태 업데이트
        self.clear_button.setEnabled(total_count > 0)
        self.delete_selected_button.setEnabled(selected_count > 0)
        self.save_all_button.setEnabled(total_count > 0)
        
        # 선택삭제 버튼 텍스트 업데이트 (선택된 개수 표시)
        if selected_count > 0:
            self.delete_selected_button.setText(f"🗑 선택삭제 ({selected_count})")
        else:
            self.delete_selected_button.setText("🗑 선택삭제")
    
    def setup_bottom_buttons(self, layout):
        """하단 버튼 섹션 (Clear, Excel 저장 등)"""
        button_layout = QHBoxLayout()
        
        # 클리어 버튼
        self.clear_button = ModernDangerButton("🗑 전체 클리어")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # Excel 저장 버튼
        self.save_all_button = ModernSuccessButton("💾 저장")
        self.save_all_button.clicked.connect(self.save_all_results)
        self.save_all_button.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.save_all_button)
        
        layout.addLayout(button_layout)
    
    def delete_selected_results(self):
        """선택된 결과 삭제"""
        checked_row_indices = self.results_table.get_checked_rows()
        if not checked_row_indices:
            try:
                ModernInfoDialog.warning(self, "항목 선택 필요", "삭제할 검색 결과를 먼저 선택해주세요.")
            except:
                QMessageBox.information(self, "항목 선택 필요", "삭제할 검색 결과를 먼저 선택해주세요.")
            return
        
        # 확인 다이얼로그
        try:
            confirmed = ModernConfirmDialog.warning(
                self,
                "선택된 결과 삭제",
                f"선택된 {len(checked_row_indices)}개의 검색 결과를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                "삭제",
                "취소"
            )
        except:
            reply = QMessageBox.question(
                self, "선택된 결과 삭제",
                f"선택된 {len(checked_row_indices)}개의 검색 결과를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                QMessageBox.Yes | QMessageBox.No
            )
            confirmed = reply == QMessageBox.Yes
        
        if not confirmed:
            return
        
        # 선택된 키워드들 수집 (행 삭제 전에 미리 수집)
        keywords_to_delete = []
        for row_index in checked_row_indices:
            if row_index < self.results_table.rowCount():
                keyword_item = self.results_table.item(row_index, 1)  # 키워드는 1번 컬럼
                if keyword_item:
                    keywords_to_delete.append(keyword_item.text())
        
        # 역순으로 행 삭제 (인덱스 변경 방지)
        for row_index in sorted(checked_row_indices, reverse=True):
            if row_index < self.results_table.rowCount():
                self.results_table.removeRow(row_index)
        
        # search_results에서도 해당 키워드들 제거
        self.search_results = [
            data for data in self.search_results 
            if data.keyword not in keywords_to_delete
        ]
        
        # 상태 업데이트
        self.on_selection_changed()
        
        # 로그 메시지
        self.add_log(f"🗑 선택된 {len(keywords_to_delete)}개 결과가 삭제되었습니다.", "info")
    
    def cancel_search(self):
        """검색 취소"""
        # 취소 상태 설정 (진행률 업데이트 차단)
        self.is_search_canceled = True
        
        try:
            if self.service:
                self.service.stop_analysis()  # 협조적 취소

            if self.worker and self.worker.isRunning():
                try:
                    self.worker.cancel()  # 올바른 취소
                except AttributeError:
                    self.worker.requestInterruption()
                    self.worker.quit()
        except Exception as e:
            print(f"워커 종료 중 오류: {e}")
        finally:
            self.on_search_finished(canceled=True)
            self.add_log("⏹ 검색이 취소되었습니다.", "warning")
    
    def save_all_results(self):
        """모든 결과 저장"""
        if not self.search_results:
            try:
                ModernInfoDialog.warning(self, "저장 불가", "저장할 검색 결과가 없습니다.")
            except:
                QMessageBox.information(self, "저장 불가", "저장할 검색 결과가 없습니다.")
            return
        
        # 현재 날짜와 시간을 파일명에 포함
        current_time = datetime.now().strftime("%Y%m%d_%H%M")
        default_filename = f"키워드_검색결과_{current_time}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "저장할 파일명을 입력하세요",
            default_filename,
            "Excel files (*.xlsx)"
        )
        
        if file_path:
            # Excel 내보내기 로직 (service 경유 - CLAUDE.md 구조 준수)
            try:
                # service를 통해 adapters 호출
                success = self.service.export_keywords_to_excel(self.search_results, file_path)
                if success:
                    self.add_log(f"📊 전체 결과 저장 완료: {len(self.search_results)}개 키워드", "success")
                    
                    # 저장 완료 다이얼로그 사용
                    try:
                        ModernSaveCompletionDialog.show_save_completion(
                            self, 
                            "저장 완료", 
                            f"키워드 검색 결과가 성공적으로 저장되었습니다.\n\n총 {len(self.search_results)}개 키워드가 Excel 파일로 저장되었습니다.", 
                            file_path
                        )
                    except:
                        QMessageBox.information(self, "저장 완료", f"Excel 파일로 저장되었습니다.\n파일 경로: {file_path}")
                else:
                    self.add_log("❌ 파일 저장에 실패했습니다.", "error")
                    QMessageBox.warning(self, "저장 실패", "Excel 파일 저장에 실패했습니다.")
            except Exception as e:
                logger.error(f"Excel 내보내기 실패: {e}")
                self.add_log("❌ 파일 저장에 실패했습니다.", "error")
                QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{e}")
    
    def save_selected_results(self):
        """선택된 결과 저장"""
        # ModernTableWidget에서 체크된 행 인덱스들 가져오기
        checked_row_indices = self.results_table.get_checked_rows()
        if not checked_row_indices:
            try:
                ModernInfoDialog.warning(self, "항목 선택 필요", "저장할 검색 결과를 먼저 선택해주세요.")
            except:
                QMessageBox.information(self, "항목 선택 필요", "저장할 검색 결과를 먼저 선택해주세요.")
            return
        
        # 선택된 결과 필터링 - 행 인덱스로 키워드 찾기
        selected_data = []
        for row_index in checked_row_indices:
            if row_index < self.results_table.rowCount():
                keyword_item = self.results_table.item(row_index, 1)  # 키워드는 1번 컬럼
                if keyword_item:
                    keyword = keyword_item.text()
                    for data in self.search_results:
                        if data.keyword == keyword:
                            selected_data.append(data)
                            break
        
        if not selected_data:
            try:
                ModernInfoDialog.error(self, "데이터 오류", "선택된 항목에 해당하는 데이터를 찾을 수 없습니다.")
            except:
                QMessageBox.information(self, "데이터 오류", "선택된 항목에 해당하는 데이터를 찾을 수 없습니다.")
            return
        
        # 현재 날짜와 시간을 파일명에 포함
        current_time = datetime.now().strftime("%Y%m%d_%H%M")
        default_filename = f"키워드_선택결과_{current_time}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "저장할 파일명을 입력하세요",
            default_filename, 
            "Excel files (*.xlsx)"
        )
        
        if file_path:
            # Excel 내보내기 로직 (service 경유 - CLAUDE.md 구조 준수)
            try:
                # service를 통해 adapters 호출
                success = self.service.export_keywords_to_excel(selected_data, file_path)
                if success:
                    self.add_log(f"📋 선택된 결과 저장 완료: {len(selected_data)}개 키워드", "success")
                    
                    # 저장 완료 다이얼로그 사용
                    try:
                        ModernSaveCompletionDialog.show_save_completion(
                            self, 
                            "저장 완료", 
                            f"선택된 키워드 검색 결과가 성공적으로 저장되었습니다.\n\n총 {len(selected_data)}개 키워드가 Excel 파일로 저장되었습니다.", 
                            file_path
                        )
                    except:
                        QMessageBox.information(self, "저장 완료", f"Excel 파일로 저장되었습니다.\n파일 경로: {file_path}")
                else:
                    self.add_log("❌ 파일 저장에 실패했습니다.", "error")
                    QMessageBox.warning(self, "저장 실패", "Excel 파일 저장에 실패했습니다.")
            except Exception as e:
                logger.error(f"Excel 내보내기 실패: {e}")
                self.add_log("❌ 파일 저장에 실패했습니다.", "error")
                QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{e}")
    
    def clear_results(self):
        """결과 지우기"""
        if not self.search_results:
            # 검색 결과가 없으면 버튼을 비활성화하고 조용히 리턴
            self.clear_button.setEnabled(False)
            return
        
        # 모던 확인 다이얼로그 사용
        try:
            confirmed = ModernConfirmDialog.warning(
                self, 
                "검색 결과 삭제", 
                f"총 {len(self.search_results)}개의 검색 결과를 모두 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                "삭제", 
                "취소"
            )
        except:
            reply = QMessageBox.question(
                self, "검색 결과 삭제",
                f"총 {len(self.search_results)}개의 검색 결과를 모두 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
                QMessageBox.Yes | QMessageBox.No
            )
            confirmed = reply == QMessageBox.Yes
        
        if confirmed:
            # UI 및 데이터 클리어
            self.results_table.clearContents()
            self.results_table.setRowCount(0)
            self.search_results.clear()
            self.progress_bar.setValue(0)
            
            # 검색 결과가 없으므로 버튼들 비활성화
            self.clear_button.setEnabled(False)
            self.save_all_button.setEnabled(False)
            self.delete_selected_button.setEnabled(False)
            self.delete_selected_button.setText("🗑 선택삭제")
            
            self.add_log("🗑 모든 검색 결과가 삭제되었습니다.", "info")
    
    def add_log(self, message: str, level: str = "info"):
        """로그 메시지 추가 (공통 로그 매니저 사용)"""
        try:
            log_manager.add_log(message, level)
        except:
            print(f"[{level.upper()}] {message}")
    
    def start_search(self):
        """검색 시작 (로깅 추가)"""
        text = self.keyword_input.toPlainText().strip()
        if not text:
            self.add_log("❌ 키워드를 입력해주세요.", "error")
            try:
                ModernInfoDialog.warning(self, "키워드 입력 필요", "검색할 키워드를 입력해주세요.")
            except:
                QMessageBox.information(self, "키워드 입력 필요", "검색할 키워드를 입력해주세요.")
            return
        
        if not self.service:
            self.add_log("❌ API 설정이 필요합니다.", "error")
            try:
                ModernInfoDialog.warning(self, "API 설정 필요", "API 설정을 먼저 완료해주세요.")
            except:
                QMessageBox.information(self, "API 설정 필요", "API 설정을 먼저 완료해주세요.")
            return
        
        # 키워드 파싱 (validators 사용)
        keywords = parse_keywords(text)
        if not keywords:
            self.add_log("❌ 유효한 키워드가 없습니다.", "error")
            try:
                ModernInfoDialog.warning(self, "키워드 오류", "입력한 텍스트에서 유효한 키워드를 찾을 수 없습니다.")
            except:
                QMessageBox.information(self, "키워드 오류", "입력한 텍스트에서 유효한 키워드를 찾을 수 없습니다.")
            return
        
        # 기존 키워드 확인 (ModernTableWidget에서)
        existing_keywords = set()
        for row in range(self.results_table.rowCount()):
            keyword_item = self.results_table.item(row, 1)  # 키워드는 1번 컬럼
            if keyword_item:
                existing_keywords.add(keyword_item.text())
        
        # 중복 제거 및 건너뛴 키워드 추적
        unique_keywords, skipped_keywords = filter_unique_keywords_with_skipped(keywords, existing_keywords)
        
        # 키워드 처리 결과 로깅
        if skipped_keywords:
            self.add_log(f"⚠️ 중복 제거: {len(skipped_keywords)}개 키워드 건너뜀 ({', '.join(skipped_keywords[:3])}{'...' if len(skipped_keywords) > 3 else ''})", "warning")
        
        # 검색할 키워드가 없는 경우 처리
        if not unique_keywords:
            self.add_log("❌ 모든 키워드가 중복되어 검색할 키워드가 없습니다.", "error")
            # 입력창 비우기
            self.keyword_input.clear()
            try:
                ModernInfoDialog.warning(self, "중복 키워드", "입력된 모든 키워드가 이미 검색되었거나 중복입니다.")
            except:
                QMessageBox.information(self, "중복 키워드", "입력된 모든 키워드가 이미 검색되었거나 중복입니다.")
            return
        
        # UI 상태 변경
        self.is_search_canceled = False  # 새 검색 시작 시 취소 상태 초기화
        self.search_button.setEnabled(False)
        self.search_button.setText("🔍 검색 중...")
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(unique_keywords))
        
        # 백그라운드 워커로 키워드 분석 실행
        self.worker = BackgroundWorker(self)
        
        # 워커 시그널 연결
        self.worker.progress_updated.connect(self._on_worker_progress)
        self.worker.processing_finished.connect(self._on_worker_finished)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.canceled.connect(self._on_worker_canceled)
        
        # 병렬 분석 함수 실행 (실시간 결과 표시)
        self.worker.execute_function(
            self._analyze_keywords_task,
            list(unique_keywords),
            progress_callback=self._create_progress_callback(),
            result_callback=self._create_result_callback()
        )
        
        # 상세한 검색 시작 로그
        if len(keywords) == len(unique_keywords):
            self.add_log(f"🔍 키워드 검색 시작: {len(unique_keywords)}개", "info")
        else:
            self.add_log(f"🔍 키워드 검색 시작: {len(unique_keywords)}개 (입력: {len(keywords)}개, 중복 제거: {len(skipped_keywords)}개)", "info")
    
    def _analyze_keywords_task(self, keywords, progress_callback=None, result_callback=None, cancel_event=None):
        """워커에서 실행할 실제 작업: service의 병렬 분석 메소드 호출"""
        # 취소 확인 함수
        def stop_check():
            return cancel_event is not None and getattr(cancel_event, "is_set", lambda: False)()
        
        # service의 병렬 분석 메소드 호출 (CLAUDE.md 구조 준수)
        return self.service.analyze_keywords_parallel(
            keywords=list(keywords),
            progress_callback=progress_callback,
            result_callback=result_callback,
            stop_check=stop_check
        )
    
    def _create_progress_callback(self):
        """진행률 콜백 함수 생성"""
        def callback(current, total, message):
            # 스레드 안전 방식으로 UI 업데이트
            QMetaObject.invokeMethod(self, "_update_progress", Qt.QueuedConnection,
                                   Q_ARG(int, current), Q_ARG(int, total), Q_ARG(str, message))
        return callback
    
    def _create_result_callback(self):
        """실시간 결과 추가 콜백 함수 생성"""
        def callback(keyword_data):
            # Qt 시그널을 통해 실시간으로 UI에 결과 추가
            self.keyword_result_ready.emit(keyword_data)
        return callback
    
    @Slot(int, int, str)
    def _update_progress(self, current: int, total: int, message: str):
        """메인 스레드에서 진행률 업데이트"""
        # 취소 중이면 진행률 업데이트 무시
        if self.is_search_canceled:
            return
            
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
    
    def _on_worker_progress(self, current: int, total: int, message: str):
        """워커 진행률 업데이트"""
        # 취소 중이면 진행률 업데이트 무시
        if self.is_search_canceled:
            return
            
        self._update_progress(current, total, message)
    
    def _on_worker_finished(self, result):
        """워커 완료 처리 (병렬 처리용)"""
        # 병렬 처리에서는 개별 키워드가 이미 실시간으로 추가되었으므로
        # 워커 완료시에는 UI 상태만 업데이트
        if result and hasattr(result, 'keywords'):
            # 혹시 실시간 시그널이 누락된 키워드가 있다면 추가
            existing_keywords = {kw.keyword for kw in self.search_results}
            for keyword_data in result.keywords:
                if keyword_data.keyword not in existing_keywords:
                    self._safe_add_keyword_result(keyword_data)
        
        self.on_search_finished()
        # 성공 로그는 _on_service_finished에서 이미 출력되므로 중복 방지
        if not (result and hasattr(result, 'keywords')):
            self.add_log(f"✅ 키워드 분석 완료", "success")
    
    def _on_worker_error(self, error_msg: str):
        """워커 오류 처리"""
        self.on_search_finished(canceled=False)  # 에러는 취소가 아님
        self.add_log(f"❌ 키워드 분석 오류: {error_msg}", "error")
        try:
            ModernInfoDialog.error(self, "분석 오류", f"키워드 분석 중 오류가 발생했습니다:\n{error_msg}")
        except:
            QMessageBox.critical(self, "분석 오류", f"키워드 분석 중 오류가 발생했습니다:\n{error_msg}")
    
    def _on_worker_canceled(self):
        """워커 취소 처리"""
        self.on_search_finished(canceled=True)
        # 로그는 cancel_search()에서 이미 출력했으므로 중복 방지
    
    def _safe_add_keyword_result(self, keyword_data: KeywordData):
        """메인 스레드에서 실행되는 안전한 키워드 결과 추가"""
        # ModernTableWidget에 행 추가 (체크박스는 자동 처리되므로 실제 데이터만 전달)
        # 카테고리를 줄바꿈으로 처리 (기존 방식과 동일)
        category_text = keyword_data.category or "-"
        if keyword_data.category and "," in keyword_data.category:
            # 콤마로 구분된 카테고리들을 줄바꿈으로 변경
            categories = [cat.strip() for cat in keyword_data.category.split(",")]
            category_text = "\n".join(categories)
        
        # 안전한 데이터 처리
        keyword_text = keyword_data.keyword or ""
        search_volume_text = formatters.format_int(keyword_data.search_volume) if keyword_data.search_volume is not None else "0"
        total_products_text = formatters.format_int(keyword_data.total_products) if keyword_data.total_products is not None else "0"
        competition_text = formatters.format_competition(keyword_data.competition_strength) if keyword_data.competition_strength is not None else "-"
        
        row_data = [
            keyword_text,
            category_text,
            search_volume_text,
            total_products_text,
            competition_text,
        ]
        
        # 테이블에 행 추가 (체크박스는 자동으로 추가됨)
        self.results_table.add_row_with_data(row_data)
        self.search_results.append(keyword_data)

        # 첫 번째 결과가 추가되면 버튼들 활성화
        if len(self.search_results) == 1:
            self.clear_button.setEnabled(True)
            self.save_all_button.setEnabled(True)
    
    def on_search_finished(self, canceled=False):
        """검색 완료 또는 취소"""
        self.search_button.setEnabled(True)
        self.search_button.setText("🔍 검색")
        self.cancel_button.setEnabled(False)
        
        # 진행률바 초기화
        self.progress_bar.setValue(0)
        
        
        self.keyword_input.clear()
    
    def show_error(self, message: str):
        """오류 메시지 표시 (로깅 추가)"""
        self.add_log(f"❌ 오류: {message}", "error")
        try:
            ModernInfoDialog.error(self, "오류 발생", f"다음 오류가 발생했습니다:\n\n{message}")
        except:
            QMessageBox.critical(self, "오류 발생", f"다음 오류가 발생했습니다:\n\n{message}")
    
    def load_api_config(self):
        """API 설정 로드 - Foundation Config 사용"""
        try:
            from src.foundation.config import config_manager
            config = config_manager.load_api_config()
            
            if config.is_complete():
                # Foundation config를 통해 서비스 생성
                self.service = analysis_manager.create_service()
                logger.debug("서비스 준비 완료 (Foundation Config 사용).")
                self.add_log("🔧 API 설정 로드 완료", "info")
            else:
                self.service = None
                logger.debug("API 미설정으로 서비스 생성하지 않음.")
                missing_apis = []
                if not config.is_searchad_valid():
                    missing_apis.append("검색광고")
                if not config.is_shopping_valid():
                    missing_apis.append("쇼핑")
                self.add_log(f"⚠️ API 설정 필요: {', '.join(missing_apis)}", "warning")
                
        except Exception as e:
            self.add_log(f"❌ API 설정 로드 실패: {str(e)}", "error")
            logger.error(f"API 설정 로드 오류: {e}")
            self.service = None
    
    def open_api_settings(self):
        """API 설정 창 열기"""
        try:
            from src.desktop.api_dialog import APISettingsDialog
            dialog = APISettingsDialog(self)
            
            # API 설정 변경 시그널 연결
            if hasattr(dialog, 'api_settings_changed'):
                dialog.api_settings_changed.connect(self.on_api_settings_changed)
            
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self, "정보", 
                "API 설정 기능은 구현 예정입니다.\n"
                "현재는 설정 파일을 직접 수정해주세요."
            )
    
    def on_api_settings_changed(self):
        """API 설정이 변경되었을 때 호출"""
        # API 설정 다시 로드 (시그널 연결 포함)
        self.load_api_config()
        self.add_log("🔄 API 설정이 업데이트되었습니다.", "info")