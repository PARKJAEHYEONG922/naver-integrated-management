"""
파워링크 광고비 분석기 컨트롤 위젯 (좌측 패널)
진행상황, 키워드입력, 분석 제어 버튼들을 포함
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal

from src.toolbox.ui_kit import ModernStyle, tokens
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog, ModernInfoDialog
from src.toolbox.ui_kit.components import ModernCard, ModernPrimaryButton, ModernDangerButton
from src.desktop.common_log import log_manager
from src.foundation.logging import get_logger
from src.toolbox.progress import throttle_ms
from .service import powerlink_service
from .worker import PowerLinkAnalysisWorker
from src.toolbox.text_utils import parse_keywords_from_text, process_keywords, TextProcessor

logger = get_logger("features.powerlink_analyzer.control_widget")






class PowerLinkControlWidget(QWidget):
    """파워링크 분석 컨트롤 위젯 (좌측 패널)"""
    
    # 시그널 정의
    analysis_completed = Signal(dict)  # 분석 완료 시 결과 전달
    analysis_error = Signal(str)       # 분석 오류 시 에러 메시지 전달
    keywords_data_cleared = Signal()   # 키워드 데이터 클리어 시
    keyword_added_immediately = Signal(str)  # 키워드 즉시 추가 시그널  
    all_rankings_updated = Signal()   # 모든 순위 계산 완료 시그널
    analysis_started = Signal()       # 분석 시작 시그널
    analysis_finished = Signal()      # 분석 완료/오류 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keywords_data = {}  # 키워드 데이터 저장
        self.analysis_worker = None  # 분석 워커 스레드
        self.current_analysis_total = 0  # 현재 분석 중인 총 키워드 개수
        self.analysis_in_progress = False  # 분석 진행 중 여부 플래그
        self.results_widget = None  # 결과 위젯 참조 (테이블 키워드 확인용)
        
        # 브라우저는 worker에서 관리
        
        # 실시간 UI 업데이트를 위한 타이머 (throttle 적용)
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_keyword_count_display)
        self.ui_update_timer.setInterval(500)  # 500ms 간격
        self.last_update_time = 0  # throttle용 마지막 업데이트 시간
        
        self.setup_ui()
        self.setup_connections()
        
    def closeEvent(self, event):
        """위젯 종료 시 리소스 정리"""
        # 분석 워커 정리 (워커에서 브라우저 정리 담당)
        if getattr(self, 'analysis_worker', None):
            try:
                self.analysis_worker.stop()
                if self.analysis_worker.isRunning():
                    self.analysis_worker.wait()  # 워커 종료 대기
            except Exception:
                pass

        # 🔧 UI 타이머 정리
        if hasattr(self, 'ui_update_timer') and self.ui_update_timer.isActive():
            self.ui_update_timer.stop()

        log_manager.add_log("🧹 PowerLink 리소스 정리 완료", "info")
        super().closeEvent(event)
    
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(tokens.GAP_15)
        
        # 1. 진행 상황 카드
        progress_card = self.create_progress_card()
        layout.addWidget(progress_card)
        
        # 2. 키워드 입력 카드
        keyword_card = self.create_keyword_input_card()
        layout.addWidget(keyword_card)
        
        # 3. 제어 버튼들
        control_buttons = self.create_control_buttons()
        layout.addWidget(control_buttons)
        
        # 4. 여유 공간
        layout.addStretch()
        
    def create_progress_card(self) -> ModernCard:
        """진행 상황 카드"""
        card = ModernCard("📊 진행 상황")
        layout = QVBoxLayout(card)
        layout.setSpacing(tokens.GAP_10)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        progress_height = tokens.GAP_24
        border_radius = tokens.GAP_8
        chunk_radius = tokens.GAP_6
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {border_radius}px;
                text-align: center;
                background-color: {ModernStyle.COLORS['bg_input']};
                font-weight: bold;
                height: {progress_height}px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: {chunk_radius}px;
            }}
        """)
        self.progress_bar.setVisible(False)  # 처음엔 숨김
        
        # 상태 메시지
        self.status_label = QLabel("분석 대기 중...")
        status_font_size = tokens.get_font_size('normal')
        status_padding = tokens.GAP_5
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {status_font_size}px;
                font-weight: 500;
                padding: {status_padding}px;
            }}
        """)
        
        # 키워드 개수 표시 레이블
        self.keyword_count_label = QLabel("등록된 키워드: 0개")
        count_font_size = tokens.get_font_size('normal')
        count_padding_v = tokens.GAP_3
        count_padding_h = tokens.GAP_8
        count_radius = tokens.GAP_6
        count_margin = tokens.GAP_5
        self.keyword_count_label.setStyleSheet(f"""
            QLabel {{
                color: #10b981;
                font-size: {count_font_size}px;
                font-weight: 600;
                padding: {count_padding_v}px {count_padding_h}px;
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: {count_radius}px;
                margin-top: {count_margin}px;
            }}
        """)
        self.keyword_count_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.keyword_count_label)
        
        return card
        
    def create_keyword_input_card(self) -> ModernCard:
        """키워드 입력 카드"""
        card = ModernCard("📝 키워드 입력")
        
        # 컴팩트한 스타일
        card_font_size = tokens.get_font_size('normal')
        card_radius = tokens.GAP_12
        card_margin = tokens.GAP_5
        card_padding = tokens.GAP_5
        card_left = tokens.GAP_15
        card_title_padding = tokens.GAP_8
        card.setStyleSheet(f"""
            QGroupBox {{
                font-size: {card_font_size}px;
                font-weight: 600;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {card_radius}px;
                margin: {card_margin}px 0;
                padding-top: {card_padding}px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {card_left}px;
                padding: 0 {card_title_padding}px;
                color: {ModernStyle.COLORS['text_primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(tokens.GAP_3)
        layout.setContentsMargins(
            tokens.GAP_12, tokens.GAP_3, 
            tokens.GAP_12, tokens.GAP_8
        )
        
        # 키워드 입력 텍스트박스
        self.keyword_input = QTextEdit()
        self.keyword_input.setPlaceholderText("키워드를 입력하세요 (엔터 또는 , 로 구분)")
        
        # 자동 줄바꿈 설정
        self.keyword_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.keyword_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.keyword_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        input_radius = tokens.GAP_8
        input_padding = tokens.GAP_16
        input_font_size = tokens.get_font_size('normal')
        input_height = 200
        self.keyword_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: {input_radius}px;
                padding: {input_padding}px;
                font-size: {input_font_size}px;
                color: {ModernStyle.COLORS['text_primary']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """)
        self.keyword_input.setFixedHeight(input_height)
        
        # 텍스트 변경 시 처리
        self.keyword_input.textChanged.connect(self.on_text_changed)
        
        layout.addWidget(self.keyword_input)
        
        return card
    
    def create_control_buttons(self) -> QWidget:
        """분석 제어 버튼들"""
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(tokens.GAP_12)
        button_layout.setContentsMargins(0, tokens.GAP_8, 0, 0)  # 좌우 여백 제거
        
        # 분석 시작 버튼
        button_height = tokens.GAP_48
        button_width = tokens.GAP_150
        self.analyze_button = ModernPrimaryButton("🚀 분석 시작")
        self.analyze_button.setFixedHeight(button_height)
        self.analyze_button.setFixedWidth(button_width)  # 너비 조정 (300 → 150)
        
        # 정지 버튼
        self.stop_button = ModernDangerButton("⏹ 정지")
        self.stop_button.setFixedHeight(button_height)
        self.stop_button.setFixedWidth(button_width)  # 시작 버튼과 동일한 너비
        self.stop_button.setEnabled(False)
        
        # 완전 중앙 정렬
        button_layout.addStretch(1)
        button_layout.addWidget(self.analyze_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch(1)
        
        return button_container
        
    def setup_connections(self):
        """시그널 연결"""
        self.analyze_button.clicked.connect(self.start_analysis)
        self.stop_button.clicked.connect(self.stop_analysis)
    
    def on_text_changed(self):
        """키워드 입력 텍스트 변경 처리"""
        if not self.ui_update_timer.isActive():
            self.ui_update_timer.start()
    
    def _restore_ui_state(self, mode="completed", message="", result_count=0):
        """
        UI 상태 복원 헬퍼 함수 (중복 로직 통합)
        Args:
            mode: "completed", "stopped", "error", "cleared"
            message: 커스텀 상태 메시지 (빈 문자열이면 기본 메시지)
            result_count: 결과 개수 (completed 모드에서 사용)
        """
        # 공통 UI 복원
        self.analyze_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # 모드별 상태 메시지
        if message:
            status_text = message
        else:
            if mode == "completed":
                status_text = f"분석 완료! {result_count}개 키워드 성공"
            elif mode == "stopped":
                status_text = "분석 중단됨"
            elif mode == "error":
                status_text = "분석 오류 발생"
            elif mode == "cleared":
                status_text = "분석 대기 중..."
                self.progress_bar.setValue(0)
                self.keyword_count_label.setText("등록된 키워드: 0개")
            else:
                status_text = "분석 대기 중..."
        
        self.status_label.setText(status_text)
        
        # 시그널 발송
        self.analysis_finished.emit()
        
        # 키워드 카운트 갱신
        if mode != "cleared":  # cleared에서는 별도로 설정
            self.update_keyword_count_display()
    
    def update_keyword_count_display(self):
        """
        키워드 개수/진행 상태 레이블 업데이트 (throttle 적용)
        - 분석 중: 무조건 진행상황 기준 '완료된 키워드: X/Y개'
        - 대기/완료: 입력창 기준 '등록된 키워드: N개'
        """
        try:
            # throttle 적용: 최소 간격 제한
            import time
            current_time = int(time.time() * 1000)  # ms 단위
            if not throttle_ms(current_time, self.last_update_time, 300):  # 300ms 최소 간격
                return
            self.last_update_time = current_time
            
            # 분석 진행 상태 체크
            is_analysis_running = (hasattr(self, 'analysis_worker') and 
                                 self.analysis_worker and 
                                 self.analysis_worker.isRunning())
            
            if is_analysis_running:
                # 분석 중: 무조건 진행상황만 표시 (입력창 텍스트 무시)
                completed_count = len(self.keywords_data)
                total_count = getattr(self, 'current_analysis_total', completed_count)
                self.keyword_count_label.setText(f"완료된 키워드: {completed_count}/{total_count}개")
            else:
                # 대기/완료 상태: 입력창 기준
                text = self.keyword_input.toPlainText().strip()
                if text:
                    keywords = parse_keywords_from_text(text)
                    processed = process_keywords(keywords)
                    count = len(processed)
                else:
                    count = 0
                self.keyword_count_label.setText(f"등록된 키워드: {count}개")
        except Exception as e:
            logger.warning(f"키워드 개수 표시 업데이트 실패: {e}")
            
    
    def start_analysis(self):
        """분석 시작"""
        # 이중 클릭 방어 가드
        if self.analysis_worker and self.analysis_worker.isRunning():
            return
            
        keywords_text = self.keyword_input.toPlainText().strip()
        if not keywords_text:
            dialog = ModernInfoDialog(
                self,
                "키워드 입력 필요",
                "분석할 키워드를 입력해주세요.",
                icon="⚠️"
            )
            dialog.exec()
            return
        
        # 키워드 파싱
        keywords = parse_keywords_from_text(keywords_text)
        
        # 테이블 위젯에 표시된 키워드들과 중복 체크 (정규화된 형태)
        existing_keywords = self.get_table_keywords()
        
        logger.debug(f"테이블 키워드 {len(existing_keywords)}개, 정규화된 키워드: {existing_keywords}")
        
        # 중복 키워드 감지 및 로깅
        original_count = len(keywords)
        logger.debug(f"입력된 키워드 {original_count}개: {keywords}")
        processed_keywords = process_keywords(keywords, existing_keywords)
        processed_count = len(processed_keywords)
        logger.debug(f"중복 제거 후 키워드 {processed_count}개: {processed_keywords}")
        
        # 중복 키워드 로깅 (단순화)
        if original_count != processed_count:
            removed_count = original_count - processed_count
            log_manager.add_log(f"🔄 중복 키워드 {removed_count}개 제거됨 (테이블 기준)", "info")
            log_manager.add_log(f"   분석 대상: {processed_count}개 키워드", "info")
        else:
            log_manager.add_log(f"✅ 중복 키워드 없음: {processed_count}개 키워드 분석 시작", "info")
        
        if not processed_keywords:
            dialog = ModernInfoDialog(
                self,
                "키워드 없음",
                "유효한 키워드가 없거나 모두 중복된 키워드입니다.",
                icon="⚠️"
            )
            dialog.exec()
            return
        
        # 키워드 즉시 추가 제거 - 분석 완료 후에만 테이블에 표시
        logger.info(f"분석 대상 키워드 {len(processed_keywords)}개 준비 완료: {processed_keywords}")
        # 즉시 추가하지 않고 분석 완료 후 set_keywords_data에서 일괄 표시
        
        # 키워드 입력창 자동 클리어
        self.keyword_input.clear()
        
        # 분석 상태 설정
        self.analysis_in_progress = True
        self.current_analysis_total = len(processed_keywords)
        
        # 분석 워커 시작 (브라우저는 worker에서 자체 관리)
        self.analysis_worker = PowerLinkAnalysisWorker(processed_keywords)
        self.analysis_worker.progress_updated.connect(self.on_progress_updated)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.keyword_result_ready.connect(self.on_keyword_result_ready)
        
        # UI 상태 변경
        self.analyze_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"분석 시작 중... ({len(processed_keywords)}개 키워드)")
        
        # 분석 시작 시그널 발송
        self.analysis_started.emit()
        
        # 워커 시작
        self.analysis_worker.start()
        log_manager.add_log(f"PowerLink 분석 시작: {len(processed_keywords)}개 키워드", "info")
    
    def stop_analysis(self):
        """분석 정지"""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.analysis_in_progress = False  # 분석 상태 리셋
            self.status_label.setText("분석을 중단하는 중...")
            
            # Worker가 완료될 때까지 기다리지 않고 즉시 UI 복원
            QTimer.singleShot(500, self._finalize_stop_analysis)  # 0.5초 후 UI 복원
            
            log_manager.add_log("PowerLink 분석 중단 요청", "warning")
    
    def _finalize_stop_analysis(self):
        """정지 후 UI 복원 및 정리"""
        try:
            # 서비스를 통해 불완전한 키워드 제거
            result_stats = powerlink_service.remove_incomplete_keywords()
            completed_count = result_stats.get('completed', 0)
            removed_count = result_stats.get('removed', 0)
            
            if completed_count > 0:
                if removed_count > 0:
                    self.status_label.setText(f"분석 중단됨 - {completed_count}개 완료, {removed_count}개 제거")
                    log_manager.add_log(f"분석 중단 - {completed_count}개 키워드 유지, {removed_count}개 미완성 키워드 제거", "warning")
                else:
                    self.status_label.setText(f"분석 중단됨 - {completed_count}개 키워드 완료")
                    log_manager.add_log(f"분석 중단 - {completed_count}개 키워드 데이터 유지", "warning")
                
                # 순위 업데이트 시그널 발송
                self.all_rankings_updated.emit()
            else:
                # 완료된 키워드가 없으면 모든 데이터 클리어 (서비스 통해)
                powerlink_service.clear_all_keywords()
                self.status_label.setText("분석 중단됨 - 완료된 키워드 없음 (전체 클리어)")
                log_manager.add_log("분석 중단 - 미완성 키워드 전체 클리어", "warning")
                
                # 테이블 클리어 시그널 발송
                self.keywords_data_cleared.emit()
            
            # UI 상태 복원 (헬퍼 사용)
            if completed_count > 0:
                msg = (f"분석 중단됨 - {completed_count}개 완료, {removed_count}개 제거"
                       if removed_count > 0 else
                       f"분석 중단됨 - {completed_count}개 키워드 완료")
                self._restore_ui_state("stopped", msg)
            else:
                self._restore_ui_state("stopped", "분석 중단됨 - 완료된 키워드 없음 (전체 클리어)")
            
        except Exception as e:
            logger.error(f"정지 후 정리 중 오류: {e}")
            # 오류 발생 시에도 UI 복원 (헬퍼 사용)
            self._restore_ui_state("stopped")
    
    def on_progress_updated(self, progress):
        """진행상황 업데이트"""
        try:
            self.progress_bar.setValue(int(getattr(progress, 'percentage', 0)))
            # 안전한 상태 문구 조립 (detailed_status가 없을 때 대비)
            status = getattr(progress, 'status', '')
            detail = getattr(progress, 'step_detail', '')
            if status and detail:
                text = f"{status} - {detail}"
            else:
                text = status or detail or "진행 중..."
            self.status_label.setText(text)
        except Exception as e:
            logger.warning(f"진행상황 표시 업데이트 실패: {e}")
    
    def on_analysis_completed(self, results):
        """분석 완료 처리"""
        log_manager.add_log(f"PowerLink 분석 완료: {len(results)}개 결과", "info")
        
        # 결과를 메모리에 저장 (서비스 통해)
        for keyword, result in results.items():
            self.keywords_data[keyword] = result
        # 서비스를 통해 키워드 데이터 추가
        powerlink_service.add_keywords_data(results)
            
        # 디버그: 분석 완료 후 키워드 데이터베이스 상태 (서비스 통해)
        keyword_info = powerlink_service.get_keyword_count_info()
        total_in_db = keyword_info.get('count', 0)
        keywords_list = keyword_info.get('keywords', [])
        log_manager.add_log(f"🔍 분석 완료 후 keyword_database에 {total_in_db}개 키워드 저장됨", "info")
        log_manager.add_log(f"🔍 저장된 키워드 목록: {keywords_list}", "info")
        
        # 분석 완료 후 순위 재계산 (서비스 통해 엔진 위임)
        self.analysis_in_progress = False
        powerlink_service.recalculate_rankings()
        
        # 모든 순위 계산 완료 시그널 발송
        self.all_rankings_updated.emit()
        
        # UI 상태 복원 (헬퍼 사용)
        self._restore_ui_state("completed", result_count=len(results))
        
        # 상위 위젯에 결과 전달
        self.analysis_completed.emit(results)
        
        # 분석 완료 (다이얼로그 제거)
    
    def on_analysis_error(self, error_msg):
        """분석 오류 처리"""
        log_manager.add_log(f"PowerLink 분석 오류: {error_msg}", "error")
        
        # 분석 상태 리셋
        self.analysis_in_progress = False
        
        # 분석 완료 시그널 발송 (오류로 인한 완료)
        self.analysis_finished.emit()
        
        # UI 상태 복원 (헬퍼 사용)
        self._restore_ui_state("error")
        
        # 상위 위젯에 오류 전달
        self.analysis_error.emit(error_msg)
        
        # 모던 디자인 오류 다이얼로그 표시 (확인 버튼만)
        dialog = ModernConfirmDialog(
            self, 
            "분석 오류", 
            f"분석 중 오류가 발생했습니다.\n\n{error_msg}", 
            confirm_text="확인", 
            cancel_text=None,  # 취소 버튼 제거
            icon="❌"
        )
        dialog.exec()
    
    def on_keyword_result_ready(self, keyword: str, result):
        """개별 키워드 결과 준비 시 실시간 업데이트"""
        if result:
            # 메모리에 저장 (서비스 통해)
            self.keywords_data[keyword] = result
            powerlink_service.add_keyword_result(result)
            
            # 분석 진행 중에는 순위 계산하지 않음 (전체 완료 후 일괄 계산)
            
            # 키워드 개수 업데이트
            self.update_keyword_count_display()
    
    def get_keywords_data(self):
        """키워드 데이터 반환"""
        return self.keywords_data
        
    def clear_keywords_data(self):
        """키워드 데이터 초기화"""
        # 진행 중인 분석이 있으면 먼저 중단
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.stop()
            self.analysis_in_progress = False
        
        # 데이터 클리어 (서비스 통해)
        self.keywords_data.clear()
        powerlink_service.clear_all_keywords()
        
        # UI 상태 완전 초기화 (헬퍼 사용)
        self._restore_ui_state("cleared")
        
        # 키워드 입력창도 클리어 (선택사항)
        # self.keyword_input.clear()
        
        # 클리어 시그널 발송
        self.keywords_data_cleared.emit()
        log_manager.add_log("PowerLink 데이터 전체 클리어 완료", "info")
    
    def get_table_keywords(self) -> set:
        """테이블 위젯에 현재 표시된 키워드들을 정규화된 형태로 반환"""
        table_keywords = set()
        try:
            # NPE 가드 강화
            if not self.results_widget or not hasattr(self.results_widget, 'mobile_table'):
                return set()
                
            if self.results_widget:
                # 모바일 테이블에서 키워드 수집 (모바일과 PC는 동일한 키워드 세트)
                mobile_table = self.results_widget.mobile_table
                for row in range(mobile_table.rowCount()):
                    keyword_item = mobile_table.item(row, 1)  # 키워드는 1번 컬럼
                    if keyword_item:
                        keyword = keyword_item.text().strip()
                        if keyword:
                            normalized = TextProcessor.normalize_keyword(keyword)
                            table_keywords.add(normalized)
                
                logger.debug(f"테이블에서 {len(table_keywords)}개 키워드 수집: {table_keywords}")
            else:
                logger.warning("results_widget 참조가 없어 테이블 키워드를 확인할 수 없음")
        except Exception as e:
            logger.error(f"테이블 키워드 수집 실패: {e}")
        
        return table_keywords

    
    
    
