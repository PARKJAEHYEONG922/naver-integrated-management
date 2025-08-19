"""
키워드 분석 기능 UI
원본 통합관리프로그램의 키워드 검색기 UI 완전 복원
"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QTreeWidget, QProgressBar, QMessageBox, QFileDialog,
    QFrame, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QMetaObject, Q_ARG, Slot

from src.toolbox.ui_kit import (
    ModernStyle, SortableTreeWidgetItem,
    ModernPrimaryButton, ModernSuccessButton, ModernDangerButton, 
    ModernCancelButton, ModernHelpButton
)
from src.desktop.common_log import log_manager
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog, ModernInfoDialog, ModernSaveCompletionDialog
from .worker import BackgroundWorker
from .service import analysis_manager
from .models import KeywordData, AnalysisPolicy, AnalysisProgress
from src.toolbox.text_utils import parse_keywords_from_text, filter_unique_keywords, clean_keywords, filter_unique_keywords_with_skipped
from src.foundation.logging import get_logger

logger = get_logger("features.keyword_analysis.ui")






class KeywordAnalysisWidget(QWidget):
    """키워드 분석 메인 위젯 - 원본 키워드 검색기 UI 완전 복원"""
    
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.worker: BackgroundWorker = None
        self.search_results = []  # 검색 결과 저장 (원본과 동일)
        
        
        self.setup_ui()
        self.load_api_config()
    
    def setup_ui(self):
        """원본 키워드 검색기 UI 레이아웃 완전 복원"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
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
        
        # 제목
        title_label = QLabel("🔍 키워드 검색기")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
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
        """키워드 입력 + 검색/정지 버튼 섹션"""
        input_frame = QFrame()
        input_frame.setFixedHeight(160)  # UI 블록 고정 높이
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: 12px;
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: 8px;
            }}
        """)
        
        input_layout = QVBoxLayout()
        
        # 키워드 입력 + 버튼 가로 배치
        input_row = QHBoxLayout()
        input_row_widget = QWidget()
        input_row_widget.setFixedHeight(140)  # 내부 검색 영역 고정 높이
        
        # 텍스트 입력
        self.keyword_input = QTextEdit()
        self.keyword_input.setPlaceholderText("예: 아이폰 케이스, 갤럭시 충전기, 블루투스 이어폰")
        self.keyword_input.setMaximumHeight(80)
        self.keyword_input.setStyleSheet(f"""
            QTextEdit {{
                font-size: 14px;
                padding: 8px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_primary']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """)
        input_row.addWidget(self.keyword_input, 3)  # 비율 3 (더 넓게)
        
        # 버튼 컨테이너
        button_container = QVBoxLayout()
        button_container.setSpacing(5)
        
        # 검색 시작 버튼
        self.search_button = ModernPrimaryButton("🔍 검색")
        self.search_button.clicked.connect(self.start_search)
        self.search_button.setMinimumWidth(80)
        button_container.addWidget(self.search_button)
        
        # 정지 버튼
        self.cancel_button = ModernCancelButton("⏹ 정지")
        self.cancel_button.clicked.connect(self.cancel_search)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setMinimumWidth(80)
        button_container.addWidget(self.cancel_button)
        
        input_row.addLayout(button_container)
        input_row_widget.setLayout(input_row)
        input_layout.addWidget(input_row_widget)
        
        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)
    
    def setup_progress_section(self, layout):
        """진행 상태 섹션"""
        progress_layout = QHBoxLayout()
        
        self.progress_label = QLabel("대기 중...")
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
            }}
        """)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                text-align: center;
                font-weight: 500;
                background-color: {ModernStyle.COLORS['bg_card']};
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: 6px;
            }}
        """)
        self.progress_bar.setMaximumWidth(300)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
    
    def setup_results_section(self, layout):
        """결과 테이블 섹션"""
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels([
            "키워드", "카테고리", "월검색량", "전체상품수", "경쟁강도"
        ])
        
        # 정렬 기능 활성화
        self.results_tree.setSortingEnabled(True)
        
        # 다중 선택 모드 활성화
        self.results_tree.setSelectionMode(QAbstractItemView.MultiSelection)
        
        # 컬럼 너비 설정
        self.results_tree.setColumnWidth(0, 220)  # 키워드
        self.results_tree.setColumnWidth(1, 525)  # 카테고리 (1.5배)
        self.results_tree.setColumnWidth(2, 100)  # 월검색량
        self.results_tree.setColumnWidth(3, 100)  # 전체상품수
        self.results_tree.setColumnWidth(4, 80)   # 경쟁강도
        
        # 테이블이 사용 가능한 공간을 모두 차지하도록 설정
        self.results_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.results_tree.setStyleSheet(f"""
            QTreeWidget {{
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_card']};
                alternate-background-color: {ModernStyle.COLORS['bg_primary']};
                font-size: 13px;
                gridline-color: {ModernStyle.COLORS['border']};
            }}
            QTreeWidget::item {{
                padding: 8px 4px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
            QTreeWidget::item:selected {{
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
        
        layout.addWidget(self.results_tree)
    
    def setup_bottom_buttons(self, layout):
        """하단 버튼 섹션 (Clear, Excel 저장 등)"""
        button_layout = QHBoxLayout()
        
        # 클리어 버튼
        self.clear_button = ModernDangerButton("🗑 전체 클리어")
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # Excel 저장 버튼들
        self.save_all_button = ModernSuccessButton("📊 모두 저장")
        self.save_all_button.clicked.connect(self.save_all_results)
        button_layout.addWidget(self.save_all_button)
        
        self.save_selected_button = ModernSuccessButton("📋 선택 저장")
        self.save_selected_button.clicked.connect(self.save_selected_results)
        button_layout.addWidget(self.save_selected_button)
        
        layout.addLayout(button_layout)
    
    
    def setup_service_connections(self):
        """서비스 시그널 연결 (기존 방식 - 호환성 유지)"""
        if self.service:
            self.service.set_progress_callback(self.update_progress)
            self.service.set_keyword_callback(self.add_keyword_result)
    
    def setup_service_signals(self):
        """병렬 처리를 위한 Qt 시그널 연결"""
        if self.service:
            try:
                # 개별 키워드 완료시 실시간 결과 표시
                self.service.keyword_processed.connect(self._safe_add_keyword_result)
                
                # 진행률 업데이트
                self.service.progress_updated.connect(self._on_service_progress)
                
                # 전체 작업 완료
                self.service.processing_finished.connect(self._on_service_finished)
                
                # 오류 발생
                self.service.error_occurred.connect(self._on_service_error)
                
                logger.debug("서비스 시그널 연결 완료")
            except Exception as e:
                logger.error(f"서비스 시그널 연결 실패: {e}")
    
    def _on_service_progress(self, current: int, total: int, message: str):
        """서비스 진행률 업데이트 (실시간)"""
        self._update_progress(current, total, message)
    
    def _on_service_finished(self, results):
        """서비스 전체 작업 완료"""
        # 병렬 처리에서는 개별 키워드가 이미 실시간으로 추가되었으므로
        # 여기서는 UI 상태만 업데이트
        self.on_search_finished()
        self.add_log(f"✅ 병렬 키워드 분석 완료: {len(results)}개", "success")
    
    def _on_service_error(self, error_msg: str):
        """서비스 오류 처리"""
        self.show_error(error_msg)
    
    def cancel_search(self):
        """검색 취소"""
        try:
            # 서비스 취소
            if self.service:
                self.service.stop_analysis()
            
            # 워커 안전 종료 (예외 처리)
            if self.worker and self.worker.isRunning():
                self.worker.stop()  # 워커의 자체 stop 메서드 호출
                self.worker.quit()  # 이벤트 루프 종료
                # wait() 호출하지 않아서 UI 블록킹 방지
            
        except Exception as e:
            print(f"워커 종료 중 오류: {e}")
        finally:
            # UI 상태 복원 (항상 실행)
            self.on_search_finished()
            self.add_log("⏹ 검색이 취소되었습니다.", "warning")
    
    def disconnect_service_signals(self):
        """서비스 시그널 연결 해제 (중복 연결 방지)"""
        if self.service and self.signals_connected:
            # 각 시그널을 개별적으로 해제하여 경고 방지
            try:
                self.service.set_progress_callback(None)
                self.service.set_keyword_callback(None)
            except:
                pass
            self.signals_connected = False
    
    def update_progress(self, progress: AnalysisProgress):
        """진행 상태 업데이트 - 스레드 안전"""
        self.progress_update_signal.emit(progress)
    
    def _safe_update_progress(self, progress: AnalysisProgress):
        """메인 스레드에서 실행되는 안전한 프로그레스 업데이트"""
        completed = progress.completed_keywords + progress.failed_keywords
        self.progress_bar.setValue(completed)
        self.progress_bar.setMaximum(progress.total_keywords)
        
        status = f"검색 중... ({completed}/{progress.total_keywords})"
        if progress.current_keyword:
            status += f" - 현재: {progress.current_keyword}"
        
        self.progress_label.setText(status)
    
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
        selected_items = self.results_tree.selectedItems()
        if not selected_items:
            try:
                ModernInfoDialog.warning(self, "항목 선택 필요", "저장할 검색 결과를 먼저 선택해주세요.")
            except:
                QMessageBox.information(self, "항목 선택 필요", "저장할 검색 결과를 먼저 선택해주세요.")
            return
        
        # 선택된 결과 필터링
        selected_data = []
        for item in selected_items:
            keyword = item.text(0)
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
            self.results_tree.clear()
            self.search_results.clear()
            self.progress_bar.setValue(0)
            self.progress_label.setText("대기 중...")
            
            # 검색 결과가 없으므로 전체 클리어 버튼 비활성화
            self.clear_button.setEnabled(False)
            
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
        
        # 키워드 파싱
        keywords = parse_keywords_from_text(text)
        if not keywords:
            self.add_log("❌ 유효한 키워드가 없습니다.", "error")
            try:
                ModernInfoDialog.warning(self, "키워드 오류", "입력한 텍스트에서 유효한 키워드를 찾을 수 없습니다.")
            except:
                QMessageBox.information(self, "키워드 오류", "입력한 텍스트에서 유효한 키워드를 찾을 수 없습니다.")
            return
        
        # 기존 키워드 확인
        existing_keywords = {
            self.results_tree.topLevelItem(i).text(0) 
            for i in range(self.results_tree.topLevelItemCount())
        }
        
        # 중복 제거 및 건너뛴 키워드 추적
        unique_keywords, skipped_keywords = filter_unique_keywords_with_skipped(keywords, existing_keywords)
        
        # 건너뛴 키워드가 있으면 로그에 표시
        if skipped_keywords:
            skipped_list = ", ".join(skipped_keywords)
            self.add_log(f"⚠️ 이미 검색된 키워드 건너뜀: {skipped_list}", "warning")
        
        # 검색할 키워드가 없으면 입력창 지우고 종료
        if not unique_keywords:
            self.keyword_input.clear()
            return
        
        # UI 상태 변경
        self.search_button.setEnabled(False)
        self.search_button.setText("🔍 검색 중...")
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(unique_keywords))
        self.progress_label.setText(f"검색 준비 중... (0/{len(unique_keywords)})")
        
        # 백그라운드 워커로 키워드 분석 실행
        self.worker = BackgroundWorker(self)
        
        # 워커 시그널 연결
        self.worker.progress_updated.connect(self._on_worker_progress)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.canceled.connect(self._on_worker_canceled)
        
        # 병렬 분석 함수 실행 (실시간 결과 표시)
        self.worker.execute_function(
            self.service.analyze_keywords_parallel,  # 병렬 처리로 변경
            unique_keywords,
            progress_callback=self._create_progress_callback()
        )
        
        self.add_log(f"🔍 키워드 검색 시작: {len(unique_keywords)}개", "info")
    
    def _create_progress_callback(self):
        """진행률 콜백 함수 생성"""
        def callback(current, total, message):
            # 스레드 안전 방식으로 UI 업데이트
            QMetaObject.invokeMethod(self, "_update_progress", Qt.QueuedConnection,
                                   Q_ARG(int, current), Q_ARG(int, total), Q_ARG(str, message))
        return callback
    
    @Slot(int, int, str)
    def _update_progress(self, current: int, total: int, message: str):
        """메인 스레드에서 진행률 업데이트"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{message} ({current}/{total})")
    
    def _on_worker_progress(self, current: int, total: int, message: str):
        """워커 진행률 업데이트"""
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
        self.on_search_finished()
        self.add_log(f"❌ 키워드 분석 오류: {error_msg}", "error")
        try:
            ModernInfoDialog.error(self, "분석 오류", f"키워드 분석 중 오류가 발생했습니다:\n{error_msg}")
        except:
            QMessageBox.critical(self, "분석 오류", f"키워드 분석 중 오류가 발생했습니다:\n{error_msg}")
    
    def _on_worker_canceled(self):
        """워커 취소 처리"""
        self.on_search_finished()
        self.add_log("⏹ 키워드 분석이 취소되었습니다.", "warning")
    
    def _safe_add_keyword_result(self, keyword_data: KeywordData):
        """메인 스레드에서 실행되는 안전한 키워드 결과 추가"""
        item = SortableTreeWidgetItem([
            keyword_data.keyword,
            keyword_data.category,
            keyword_data.formatted_volume,
            keyword_data.formatted_products,
            keyword_data.formatted_strength
        ])
        
        # 정렬을 위해 숫자 값을 사용자 데이터로 저장
        # 월검색량: None은 0으로 처리
        search_vol = 0 if keyword_data.search_volume is None else keyword_data.search_volume
        item.setData(2, Qt.UserRole, search_vol)
        
        # 전체상품수: None은 0으로 처리  
        total_prod = 0 if keyword_data.total_products is None else keyword_data.total_products
        item.setData(3, Qt.UserRole, total_prod)
        
        # 경쟁강도: None이나 inf는 그대로 저장 (정렬 로직에서 처리)
        comp_strength = keyword_data.competition_strength
        item.setData(4, Qt.UserRole, comp_strength)
        
        self.results_tree.addTopLevelItem(item)
        self.search_results.append(keyword_data)
        
        # 첫 번째 검색 결과가 추가되면 전체 클리어 버튼 활성화
        if len(self.search_results) == 1:
            self.clear_button.setEnabled(True)
    
    def on_search_finished(self):
        """검색 완료"""
        self.search_button.setEnabled(True)
        self.search_button.setText("🔍 검색")
        self.cancel_button.setEnabled(False)
        self.progress_label.setText(f"완료! 총 {len(self.search_results)}개 키워드")
        self.keyword_input.clear()
    
    def show_error(self, message: str):
        """오류 메시지 표시 (로깅 추가)"""
        self.add_log(f"❌ 오류: {message}", "error")
        try:
            ModernInfoDialog.error(self, "오류 발생", f"다음 오류가 발생했습니다:\n\n{message}")
        except:
            QMessageBox.critical(self, "오류 발생", f"다음 오류가 발생했습니다:\n\n{message}")
    
    def load_api_config(self):
        """API 설정 로드"""
        try:
            # API 설정이 있는지 확인
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            if api_config and api_config.is_complete():
                # 서비스 생성
                self.service = analysis_manager.create_service()
                
                # 실시간 결과 표시를 위한 시그널 연결
                self.setup_service_signals()
                
                # API 설정 완료 시에만 성공 메시지 출력 (중복 방지)
                logger.debug("API 설정이 완료되어 키워드 분석 서비스가 준비되었습니다.")
            else:
                self.service = None
                # API 상태는 이미 API checker에서 출력하므로 여기서는 로그 생략
                logger.debug("API 설정이 불완전하여 키워드 분석 서비스를 생성하지 않습니다.")
                
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