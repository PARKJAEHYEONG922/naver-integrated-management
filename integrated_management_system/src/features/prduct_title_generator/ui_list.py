"""
네이버 상품명 생성기 UI - 입력 및 컨트롤 위젯
입력 섹션만 관리
"""
from typing import TypedDict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QGroupBox, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernCancelButton
from src.desktop.common_log import log_manager


class InputData(TypedDict):
    """입력 데이터 타입 정의"""
    brand: str
    keyword: str
    spec: str
    material: str
    size: str


class ProductTitleInputWidget(QWidget):
    """상품명 생성기 입력 위젯"""
    
    # 시그널 정의
    analyze_requested = Signal(dict)  # 분석 요청 시그널 (InputData 전달)
    stop_requested = Signal()  # 분석 중단 요청
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # 입력 섹션만 포함
        self.input_group = self.create_input_section()
        layout.addWidget(self.input_group)
        
        self.setLayout(layout)
        
    def create_input_section(self):
        """입력 섹션 - 5개 필드를 2x3 그리드로 배치"""
        group = QGroupBox("📝 기본 정보 입력")
        
        # 폰트 기반 최소 높이 계산
        fm = QFontMetrics(self.font())
        line_h = max(32, fm.height() + 14)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 20, 15, 15)
        main_layout.setSpacing(15)
        
        # 입력 필드 그리드 레이아웃 (2열 x 3행)
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(12)
        
        # 왼쪽 열
        # 브랜드명 (0,0)
        brand_label = QLabel("브랜드명 (선택):")
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("예: 슈퍼츄")
        self.brand_input.setMinimumHeight(line_h)
        self.brand_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(brand_label, 0, 0)
        grid_layout.addWidget(self.brand_input, 0, 1)
        
        # 핵심제품명 (1,0)
        keyword_label = QLabel("핵심제품명 (필수):")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("강아지사료,오븐베이크사료,터키츄 (여러개 입력시 , 쉼표로 구분)")
        self.keyword_input.setMinimumHeight(line_h)
        self.keyword_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(keyword_label, 1, 0)
        grid_layout.addWidget(self.keyword_input, 1, 1)
        
        # 카테고리 (2,0)
        category_label = QLabel("카테고리:")
        self.keyword_category_display = QLineEdit("")
        self.keyword_category_display.setPlaceholderText("분석 후 자동 표시")
        self.keyword_category_display.setReadOnly(True)
        self.keyword_category_display.setMinimumHeight(line_h)
        self.keyword_category_display.setTextMargins(8, 4, 8, 4)
        self.keyword_category_display.setObjectName("category_display")
        grid_layout.addWidget(category_label, 2, 0)
        grid_layout.addWidget(self.keyword_category_display, 2, 1)
        
        # 오른쪽 열
        # 재질/원재료 (0,2)
        material_label = QLabel("재질/원재료 (선택):")
        self.material_input = QLineEdit()
        self.material_input.setPlaceholderText("예: 칠면조힘줄, 소고기, 양")
        self.material_input.setMinimumHeight(line_h)
        self.material_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(material_label, 0, 2)
        grid_layout.addWidget(self.material_input, 0, 3)
        
        # 사이즈 (1,2)
        size_label = QLabel("사이즈 (선택):")
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("예: S, M, L")
        self.size_input.setMinimumHeight(line_h)
        self.size_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(size_label, 1, 2)
        grid_layout.addWidget(self.size_input, 1, 3)
        
        # 수량/구성 (2,2)
        quantity_label = QLabel("수량/구성 (선택):")
        self.spec_input = QLineEdit()
        self.spec_input.setPlaceholderText("예: 20개, 300g, 20g 10개")
        self.spec_input.setMinimumHeight(line_h)
        self.spec_input.setTextMargins(8, 4, 8, 4)
        grid_layout.addWidget(quantity_label, 2, 2)
        grid_layout.addWidget(self.spec_input, 2, 3)
        
        main_layout.addLayout(grid_layout)
        
        # 버튼 영역 (오른쪽 정렬)
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 왼쪽 공간 채우기
        
        # 상품 분석 시작 버튼 (공용 컴포넌트)
        self.analyze_button = ModernPrimaryButton("🔍 상품분석시작")
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setMinimumWidth(130)
        button_layout.addWidget(self.analyze_button)
        
        # 분석 정지 버튼 (공용 컴포넌트)
        self.stop_button = ModernCancelButton("⏹️ 정지")
        self.stop_button.setEnabled(False)  # 처음엔 비활성화
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setMinimumWidth(130)
        button_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(button_layout)
        
        group.setLayout(main_layout)
        
        # SizePolicy 설정
        group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        group.setObjectName("input_group")
        
        # 스타일 적용
        self.apply_input_styles()
        
        return group
        
    def setup_connections(self):
        """시그널 연결"""
        self.analyze_button.clicked.connect(self.on_analyze_clicked)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        
    def on_analyze_clicked(self):
        """분석 버튼 클릭 처리"""
        # 입력값 수집
        input_data = {
            'brand': self.brand_input.text().strip(),
            'keyword': self.keyword_input.text().strip(),
            'spec': self.spec_input.text().strip(),
            'material': self.material_input.text().strip(),
            'size': self.size_input.text().strip()
        }
        
        # 필수 필드 검증 (핵심제품명만 필수)
        if not input_data['keyword']:
            log_manager.add_log("❌ 핵심제품명을 입력해주세요. (여러개 입력시 쉼표로 구분)", "error")
            return
            
        # 분석 요청 시그널 발생
        self.analyze_requested.emit(input_data)
        
    def set_analysis_mode(self, analyzing: bool):
        """분석 모드 설정"""
        self.analyze_button.setEnabled(not analyzing)
        self.stop_button.setEnabled(analyzing)
        
        if analyzing:
            self.keyword_category_display.setText("분석 중...")
        
    def set_compact_mode(self, compact: bool):
        """컴팩트 모드 설정"""
        if compact:
            # 더 작게 만들기
            for w in (self.brand_input, self.keyword_input, self.spec_input, 
                     self.material_input, self.size_input):
                w.setMinimumHeight(24)
        else:
            # 원래 크기로 복원
            fm = QFontMetrics(self.font())
            line_h = max(28, fm.height() + 8)
            for w in (self.brand_input, self.keyword_input, self.spec_input,
                     self.material_input, self.size_input):
                w.setMinimumHeight(line_h)
                
    def update_category_display(self, category: str):
        """카테고리 표시 업데이트"""
        if category and category.strip() and category != "미분류(0%)":
            self.keyword_category_display.setText(category)
        else:
            self.keyword_category_display.setText("분석 중...")
        
    def get_input_data(self) -> InputData:
        """현재 입력 데이터 반환"""
        return InputData(
            brand=self.brand_input.text().strip(),
            keyword=self.keyword_input.text().strip(),
            spec=self.spec_input.text().strip(),
            material=self.material_input.text().strip(),
            size=self.size_input.text().strip()
        )
        
    def apply_input_styles(self):
        """입력 섹션 스타일 적용"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 10px;
                margin: 15px 0;
                padding-top: 18px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                top: 0px;
            }}
            QLineEdit {{
                padding: 6px 10px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: {ModernStyle.COLORS['bg_input']};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QLineEdit#category_display {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_muted']};
                border: 2px solid {ModernStyle.COLORS['border']};
            }}
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_primary']};
                font-weight: 500;
            }}
            QGroupBox#input_group {{
                padding-top: 16px;
                margin: 6px 0;
            }}
            QGroupBox#input_group QLineEdit {{
                min-height: 18px;
                padding: 4px 8px;
            }}
        """)