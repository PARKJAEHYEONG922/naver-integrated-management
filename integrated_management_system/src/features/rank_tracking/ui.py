"""
순위 추적 UI 메인 컴포넌트
분리된 위젯들을 조합하여 완성된 UI 구성
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.modern_dialog import ModernHelpDialog
from src.foundation.logging import get_logger

# 분리된 위젯들 임포트
from .project_list_widget import ProjectListWidget
from .ranking_table_widget import RankingTableWidget

logger = get_logger("features.rank_tracking.ui")


class RankTrackingWidget(QWidget):
    """순위 추적 메인 위젯 - 기존과 완전 동일"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """UI 설정 - 기존과 동일"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 헤더 (제목 + 사용법 툴팁)
        self.setup_header(main_layout)
        
        # 메인 콘텐츠 영역
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Horizontal)
        
        # 좌측: 프로젝트 목록 (300px 고정)
        self.project_list = ProjectListWidget()
        self.project_list.setMinimumWidth(300)
        self.project_list.setMaximumWidth(300)
        self.project_list.project_selected.connect(self.on_project_selected)
        self.project_list.project_deleted.connect(self.on_project_deleted)
        splitter.addWidget(self.project_list)
        
        # 우측: 순위 테이블
        self.ranking_table = RankingTableWidget()
        # 신호 연결: 프로젝트 정보 업데이트 시 목록 새로고침
        self.ranking_table.project_updated.connect(self.project_list.load_projects)
        splitter.addWidget(self.ranking_table)
        
        # 스플리터 비율 설정
        splitter.setStretchFactor(0, 0)  # 좌측 고정
        splitter.setStretchFactor(1, 1)  # 우측 확장
        
        content_layout.addWidget(splitter)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)
    
    def setup_header(self, layout):
        """헤더 섹션 - 기존과 동일한 제목"""
        header_layout = QHBoxLayout()
        
        # 제목 - 기존과 정확히 동일
        title_label = QLabel("📈 상품 순위추적")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 다이얼로그 버튼
        self.help_button = QPushButton("❓ 사용법")
        self.help_button.clicked.connect(self.show_help_dialog)
        self.help_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
                margin-left: 10px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        
        header_layout.addWidget(self.help_button)
        header_layout.addStretch()  # 오른쪽 여백
        
        layout.addLayout(header_layout)
    
    def show_help_dialog(self):
        """사용법 다이얼로그 표시"""
        help_text = """
📝 첫 사용하기 (3단계):

1️⃣ 상품 등록하기
• '➕ 새 프로젝트' 버튼 클릭
• 네이버 쇼핑 상품 URL 붙여넣기
• 상품 정보가 자동으로 추출됩니다

2️⃣ 키워드 추가하기  
• 상품을 선택한 후 '🔤 키워드 추가' 클릭
• 순위를 확인할 키워드를 입력

3️⃣ 순위 확인하기
• '🔍 순위 확인' 클릭하여 현재 순위 조회
• 1-10위: 녹색, 11-50위: 노란색으로 표시

💡 추가 기능:
• 키워드 더블클릭으로 삭제 가능
• 📤 엑셀 내보내기로 데이터 저장
• 실시간 월검색량 및 카테고리 자동 조회
        """
        
        ModernHelpDialog.show_help(
            parent=self,
            title="📈 상품 순위추적 사용법",
            message=help_text.strip(),
            button_widget=self.help_button
        )
    
    def on_project_selected(self, project_id):
        """프로젝트 선택 처리"""
        try:
            from .service import rank_tracking_service
            project = rank_tracking_service.get_project_by_id(project_id)
            if project:
                self.ranking_table.set_project(project)
        except Exception as e:
            logger.error(f"프로젝트 선택 오류: {e}")
    
    def on_project_deleted(self, project_id):
        """프로젝트 삭제 처리"""
        self.project_list.load_projects()
        self.ranking_table.clear_project()  # 새로운 초기화 메서드 사용