"""
파워링크 광고비 분석기 컨트롤 위젯 (좌측 패널)
진행상황, 키워드입력, 분석 제어 버튼들을 포함
"""
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal

from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.components import ModernCard, ModernPrimaryButton, ModernDangerButton
from src.desktop.common_log import log_manager
from src.foundation.logging import get_logger
from .models import AnalysisProgress
from .service import keyword_database
from .worker import PowerLinkAnalysisWorker
from src.toolbox.text_utils import parse_keywords_from_text, process_keywords

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
        
        # 브라우저는 worker에서 관리
        
        # 실시간 UI 업데이트를 위한 타이머
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_keyword_count_display)
        self.ui_update_timer.setInterval(100)  # 100ms마다 업데이트
        
        self.setup_ui()
        self.setup_connections()
        
    def closeEvent(self, event):
        """위젯 종료 시 리소스 정리"""
        # 분석 워커 정리 (워커에서 브라우저 정리 담당)
        if hasattr(self, 'analysis_worker') and self.analysis_worker:
            self.analysis_worker.stop()
            self.analysis_worker.wait()  # 워커 종료 대기
        
        log_manager.add_log("🧹 PowerLink 리소스 정리 완료", "info")
        super().closeEvent(event)
    
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
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
        layout.setSpacing(10)
        
        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                text-align: center;
                background-color: {ModernStyle.COLORS['bg_input']};
                font-weight: bold;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: 6px;
            }}
        """)
        self.progress_bar.setVisible(False)  # 처음엔 숨김
        
        # 상태 메시지
        self.status_label = QLabel("분석 대기 중...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 13px;
                font-weight: 500;
                padding: 5px;
            }}
        """)
        
        # 키워드 개수 표시 레이블
        self.keyword_count_label = QLabel("등록된 키워드: 0개")
        self.keyword_count_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-size: 12px;
                font-weight: 600;
                padding: 3px 8px;
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 6px;
                margin-top: 5px;
            }
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
        card.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: 600;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 12px;
                margin: 5px 0;
                padding-top: 5px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: {ModernStyle.COLORS['text_primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(3)
        layout.setContentsMargins(12, 3, 12, 8)
        
        # 키워드 입력 텍스트박스
        self.keyword_input = QTextEdit()
        self.keyword_input.setPlaceholderText("키워드를 입력하세요 (엔터 또는 , 로 구분)")
        
        # 자동 줄바꿈 설정
        self.keyword_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.keyword_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.keyword_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.keyword_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
                color: {ModernStyle.COLORS['text_primary']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
        """)
        self.keyword_input.setFixedHeight(300)
        
        # 텍스트 변경 시 처리
        self.keyword_input.textChanged.connect(self.on_text_changed)
        
        layout.addWidget(self.keyword_input)
        
        return card
    
    def create_control_buttons(self) -> QWidget:
        """분석 제어 버튼들"""
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 8, 0, 0)  # 좌우 여백 제거
        
        # 분석 시작 버튼
        self.analyze_button = ModernPrimaryButton("🚀 분석 시작")
        self.analyze_button.setFixedHeight(45)
        self.analyze_button.setFixedWidth(150)  # 너비 조정 (300 → 150)
        
        # 정지 버튼
        self.stop_button = ModernDangerButton("⏹ 정지")
        self.stop_button.setFixedHeight(45)
        self.stop_button.setFixedWidth(150)  # 시작 버튼과 동일한 너비
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
    
    def update_keyword_count_display(self):
        """키워드 개수 표시 업데이트 (타이머용)"""
        text = self.keyword_input.toPlainText().strip()
        if text:
            keywords = parse_keywords_from_text(text)
            processed = process_keywords(keywords)
            count = len(processed)
        else:
            count = 0
            
        self.keyword_count_label.setText(f"등록된 키워드: {count}개")
            
    
    def start_analysis(self):
        """분석 시작"""
        keywords_text = self.keyword_input.toPlainText().strip()
        if not keywords_text:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
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
        existing_keywords = set(self.keywords_data.keys())
        
        # 중복 키워드 감지 및 로깅
        original_count = len(keywords)
        processed_keywords = process_keywords(keywords, existing_keywords)
        processed_count = len(processed_keywords)
        
        # 중복 키워드 로깅
        if original_count != processed_count:
            removed_count = original_count - processed_count
            # 제거된 키워드들 찾기
            processed_set = set(keyword.strip().replace(' ', '').upper() for keyword in processed_keywords)
            removed_keywords = []
            seen = set()
            for original in keywords:
                normalized = original.strip().replace(' ', '').upper()
                if normalized not in processed_set or normalized in seen:
                    if normalized not in seen:  # 중복으로 제거된 것만 기록
                        removed_keywords.append(original)
                    seen.add(normalized)
            
            # 기존 키워드와 중복인 것들도 찾기
            existing_duplicates = []
            for original in keywords:
                normalized = original.strip().replace(' ', '').upper()
                if normalized in existing_keywords:
                    existing_duplicates.append(original)
            
            if removed_keywords or existing_duplicates:
                total_removed = len(removed_keywords) + len(existing_duplicates)
                duplicate_list = removed_keywords + existing_duplicates
                duplicate_text = ", ".join(f"'{dup}'" for dup in duplicate_list)
                log_manager.add_log(f"🔄 중복 키워드 감지: {total_removed}개 자동 제거됨", "info")
                log_manager.add_log(f"   제거된 중복 키워드: {duplicate_text}", "info")
                log_manager.add_log(f"   분석 대상: {processed_count}개 키워드 (중복 제거 후)", "info")
            else:
                log_manager.add_log(f"✅ 중복 키워드 없음: {processed_count}개 키워드 분석 시작", "info")
        else:
            log_manager.add_log(f"✅ 중복 키워드 없음: {processed_count}개 키워드 분석 시작", "info")
        
        if not processed_keywords:
            from src.toolbox.ui_kit.modern_dialog import ModernInfoDialog
            dialog = ModernInfoDialog(
                self,
                "키워드 없음",
                "유효한 키워드가 없거나 모두 중복된 키워드입니다.",
                icon="⚠️"
            )
            dialog.exec()
            return
        
        # 키워드들을 즉시 테이블에 추가 (데이터 로딩 전 상태로)
        for keyword in processed_keywords:
            self.keyword_added_immediately.emit(keyword)
        
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
            # 실제 분석 데이터가 있는 키워드 개수 확인
            completed_keywords = []
            for keyword, result in keyword_database.keywords.items():
                # 실제 분석 데이터가 있는지 확인 (PC+Mobile 검색량이 0 이상이면 분석 완료, -1은 미분석)
                if (hasattr(result, 'pc_search_volume') and hasattr(result, 'mobile_search_volume') and 
                    result.pc_search_volume >= 0 and result.mobile_search_volume >= 0):
                    completed_keywords.append(keyword)
            
            if completed_keywords:
                # 완료된 키워드들만 유지하고 나머지는 제거
                incomplete_keywords = []
                for keyword in list(keyword_database.keywords.keys()):
                    if keyword not in completed_keywords:
                        incomplete_keywords.append(keyword)
                        keyword_database.remove_keyword(keyword)
                
                # 순위 재계산
                keyword_database.recalculate_all_rankings()
                completed_count = len(completed_keywords)
                removed_count = len(incomplete_keywords)
                
                if removed_count > 0:
                    self.status_label.setText(f"분석 중단됨 - {completed_count}개 완료, {removed_count}개 제거")
                    log_manager.add_log(f"분석 중단 - {completed_count}개 키워드 유지, {removed_count}개 미완성 키워드 제거", "warning")
                else:
                    self.status_label.setText(f"분석 중단됨 - {completed_count}개 키워드 완료")
                    log_manager.add_log(f"분석 중단 - {completed_count}개 키워드 데이터 유지", "warning")
                
                # 순위 업데이트 시그널 발송
                self.all_rankings_updated.emit()
            else:
                # 완료된 키워드가 없으면 모든 데이터 클리어
                keyword_database.clear()
                self.status_label.setText("분석 중단됨 - 완료된 키워드 없음 (전체 클리어)")
                log_manager.add_log("분석 중단 - 미완성 키워드 전체 클리어", "warning")
                
                # 테이블 클리어 시그널 발송
                self.keywords_data_cleared.emit()
            
            # UI 상태 복원
            self.analyze_button.setEnabled(True)
            self.stop_button.setEnabled(False) 
            self.progress_bar.setVisible(False)
            
            # 분석 완료 시그널 발송 (저장 버튼 활성화용)
            self.analysis_finished.emit()
            
        except Exception as e:
            logger.error(f"정지 후 정리 중 오류: {e}")
            # 오류 발생 시에도 UI 복원
            self.analyze_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.status_label.setText("분석 중단됨")
            self.analysis_finished.emit()
    
    def on_progress_updated(self, progress):
        """진행상황 업데이트"""
        self.progress_bar.setValue(progress.percentage)
        # 상세한 상태 메시지 표시
        self.status_label.setText(progress.detailed_status)
    
    def on_analysis_completed(self, results):
        """분석 완료 처리"""
        log_manager.add_log(f"PowerLink 분석 완료: {len(results)}개 결과", "info")
        
        # 결과를 메모리에 저장
        for keyword, result in results.items():
            self.keywords_data[keyword] = result
            keyword_database.add_keyword(result)
        
        # 분석 완료 후 순위 재계산 (모든 데이터가 완료된 후에만 실행)
        self.analysis_in_progress = False
        keyword_database.recalculate_all_rankings()
        
        # 모든 순위 계산 완료 시그널 발송
        self.all_rankings_updated.emit()
        
        # UI 상태 복원
        self.analyze_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"분석 완료! {len(results)}개 키워드 성공")
        
        # 분석 완료 시그널 발송
        self.analysis_finished.emit()
        
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
        
        # UI 상태 복원
        self.analyze_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("분석 오류 발생")
        
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
            # 메모리에 저장
            self.keywords_data[keyword] = result
            keyword_database.add_keyword(result)
            
            # 분석 진행 중에는 순위 계산하지 않음 (전체 완료 후 일괄 계산)
            
            # 키워드 결과 저장 완료
            
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
        
        # 데이터 클리어
        self.keywords_data.clear()
        keyword_database.clear()
        
        # UI 상태 완전 초기화
        self.status_label.setText("분석 대기 중...")
        self.keyword_count_label.setText("등록된 키워드: 0개")
        self.analyze_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        
        # 키워드 입력창도 클리어 (선택사항)
        # self.keyword_input.clear()
        
        # 클리어 시그널 발송
        self.keywords_data_cleared.emit()
        log_manager.add_log("PowerLink 데이터 전체 클리어 완료", "info")
    
    def update_keyword_count_display(self):
        """키워드 개수 실시간 업데이트 (타이머용, 원본과 동일)"""
        completed_count = len(self.keywords_data)
        total_count = getattr(self, 'current_analysis_total', completed_count)
        
        if hasattr(self, 'analysis_worker') and self.analysis_worker and self.analysis_worker.isRunning():
            # 분석 진행 중일 때
            self.keyword_count_label.setText(f"완료된 키워드: {completed_count}/{total_count}개")
        else:
            # 분석 완료 또는 대기 중일 때
            self.keyword_count_label.setText(f"등록된 키워드: {completed_count}개")
    
    
    
