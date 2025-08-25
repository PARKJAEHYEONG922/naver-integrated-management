"""
네이버 PowerLink 광고비 분석기 메인 UI 
컨트롤 위젯과 결과 위젯을 조합하는 컨테이너 역할
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)

from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit.components import ModernHelpButton
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.responsive import ResponsiveUI
from .ui_list import PowerLinkControlWidget
from .ui_table import PowerLinkResultsWidget


class PowerLinkAnalyzerWidget(QWidget):
    """PowerLink 광고비 분석기 메인 UI 컨테이너"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
    def closeEvent(self, event):
        """위젯 종료 시 리소스 정리"""
        # 컨트롤 위젯의 리소스 정리
        if getattr(self, 'control_widget', None):
            try:
                self.control_widget.close()  # Qt가 자동으로 closeEvent 전파하므로 close()만 호출
            except Exception:
                pass
        super().closeEvent(event)
        
    def setup_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            ResponsiveUI.scale(20), ResponsiveUI.scale(20), 
            ResponsiveUI.scale(20), ResponsiveUI.scale(20)
        )
        main_layout.setSpacing(ResponsiveUI.scale(20))
        
        # 헤더 섹션 (제목 + 사용법)
        self.setup_header(main_layout)
        
        # 컨텐츠 레이아웃 (좌측 패널 + 우측 패널)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(ResponsiveUI.scale(20))
        
        # 좌측 패널 (컨트롤 위젯)
        self.control_widget = PowerLinkControlWidget()
        # 200px 기준으로 반응형 조정하되 최소 150px 보장
        control_width = max(150, ResponsiveUI.scale(200))
        self.control_widget.setFixedWidth(control_width)
        
        # 우측 패널 (결과 위젯)
        self.results_widget = PowerLinkResultsWidget()
        
        # control_widget에 results_widget 참조 설정 (테이블 키워드 확인용)
        self.control_widget.results_widget = self.results_widget
        
        content_layout.addWidget(self.control_widget)
        content_layout.addWidget(self.results_widget, 1)
        
        main_layout.addLayout(content_layout)
        
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법)"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("💰 파워링크 광고비")
        title_font_size = ResponsiveUI.get_font_size_pt('title')
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}pt;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 버튼 (공용 컴포넌트 사용)
        self.help_button = ModernHelpButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = (
            "📋 키워드 입력:\n"
            "• 분석할 키워드를 입력해주세요 (엔터로 구분)\n"
            "• 같은 업종/카테고리 키워드를 함께 분석하면 정확한 순위 비교 가능\n\n"
            "📊 분석 결과 설명:\n"
            "• 월검색량: 네이버에서 월 평균 검색되는 횟수\n"
            "• 월평균클릭수: 파워링크 1~15위 광고들의 월 평균 클릭수\n"
            "• 클릭률: 파워링크 1~15위 광고들의 월 평균 클릭률 (%)\n"
            "• 1p노출위치: 실제 1페이지에 노출되는 광고 개수 (위까지)\n"
            "• 1등광고비: 1위 노출을 위한 예상 입찰가 (원)\n"
            "• 최소노출가격: 1페이지 노출을 위한 최소 입찰가 (원)\n"
            "• 추천순위: 비용 대비 효율성 기준 상대적 순위\n\n"
            "🏆 추천순위 계산 공식 (하이브리드 방식):\n\n"
            "📊 두 가지 관점으로 효율성 측정:\n"
            "• 현실성 점수 = 월평균클릭수 ÷ 최소노출가격\n"
            "  → 네이버 데이터 기반 실제 예상 성과 (원당 클릭수)\n\n"
            "• 잠재력 점수 = (월검색량 × 클릭률 ÷ 100) ÷ 최소노출가격\n"
            "  → 순수 수요와 반응성 기반 이론적 잠재력\n\n"
            "🎯 최종 점수 = 현실성 70% + 잠재력 30%\n"
            "• 실제 성과 가능성과 전략적 잠재력을 균형있게 반영\n"
            "• 점수가 높을수록 비용 대비 효율이 좋은 키워드\n"
            "• 동점시: 월검색량↑ → 최소노출가격↓ → 키워드명 순\n\n"
            "💡 사용 팁:\n"
            "• PC/모바일 탭을 구분해서 플랫폼별 분석\n"
            "• 추천순위 상위 키워드 우선 검토 (투자 효율 높음)\n"
            "• 월검색량 높고 최소노출가격 낮은 키워드가 유리\n"
            "• 체크박스로 불필요한 키워드 삭제 가능\n"
            "• 클리어 버튼으로 새로운 키워드 그룹 분석\n"
            "• 상세 버튼으로 1~15위별 입찰가 확인 가능"
        )
        
        dialog = ModernConfirmDialog(
            self, "파워링크 광고비 사용법", help_text, 
            confirm_text="확인", cancel_text=None, icon="💡"
        )
        dialog.exec()
    
    def setup_connections(self):
        """시그널 연결"""
        # 컨트롤 위젯의 시그널을 결과 위젯으로 연결
        self.control_widget.analysis_completed.connect(self.on_analysis_completed)
        self.control_widget.analysis_error.connect(self.on_analysis_error)
        self.control_widget.keywords_data_cleared.connect(self.on_keywords_data_cleared)
        
        # 키워드 즉시 추가 시그널 연결 (제거 - 분석 완료 후에만 표시)
        # self.control_widget.keyword_added_immediately.connect(self.results_widget.add_keyword_immediately)
        
        # 모든 순위 계산 완료 시그널 연결 (방어적 가드)
        if hasattr(self.results_widget, 'update_all_tables'):
            self.control_widget.all_rankings_updated.connect(self.results_widget.update_all_tables)
        
        # 분석 상태 시그널 연결 (저장 버튼 제어용)
        if hasattr(self.results_widget, 'on_analysis_started'):
            self.control_widget.analysis_started.connect(self.results_widget.on_analysis_started)
        if hasattr(self.results_widget, 'on_analysis_finished'):
            self.control_widget.analysis_finished.connect(self.results_widget.on_analysis_finished)
    
    def on_analysis_completed(self, results):
        """분석 완료 시 결과 위젯 업데이트"""
        # 결과 위젯에 키워드 데이터 추가 (누적 방식)
        self.results_widget.add_keywords_data(results)
    
    def on_analysis_error(self, error_msg):
        """분석 오류 처리"""
        ModernConfirmDialog(self, "분석 오류", error_msg, confirm_text="확인", cancel_text=None, icon="❌").exec()
    
    def on_keywords_data_cleared(self):
        """키워드 데이터 클리어 시 결과 위젯 테이블 클리어"""
        # Use the available method or create a direct clear
        if hasattr(self.results_widget, 'clear_all_tables'):
            self.results_widget.clear_all_tables()
        else:
            # Fallback: clear tables directly
            self.results_widget.mobile_table.setRowCount(0)
            self.results_widget.pc_table.setRowCount(0)
            # 버튼 상태도 갱신(권장)
            if hasattr(self.results_widget, 'update_save_button_state'):
                self.results_widget.update_save_button_state()
            if hasattr(self.results_widget, 'update_delete_button_state'):
                self.results_widget.update_delete_button_state()