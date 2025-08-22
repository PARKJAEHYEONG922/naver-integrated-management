"""
순위 추적 기능 전용 다이얼로그들
프로젝트 생성, 키워드 추가 등 - 기존 시스템과 동일한 UI/UX
"""
from typing import List, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QApplication, QTextEdit, QFrame, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from src.toolbox.ui_kit import ModernStyle


class NewProjectDialog(QDialog):
    """새 프로젝트 생성 다이얼로그 - 기존 ModernProjectUrlDialog와 동일"""
    
    def __init__(self, parent=None, button_pos=None):
        super().__init__(parent)
        self.result_url = ""
        self.result_product_name = ""
        self.result_ok = False
        self.button_pos = button_pos  # 버튼 위치 (QPoint)
        
        self.setup_ui()
        self.position_dialog()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle("새 프로젝트 생성")
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 25, 30, 30)  # 하단 여백 증가
        main_layout.setSpacing(18)  # 요소 간 간격 약간 감소
        
        # 헤더
        header_label = QLabel("🚀 새 프로젝트 생성")
        header_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
        """)
        main_layout.addWidget(header_label)
        
        # 설명
        desc_label = QLabel("네이버 쇼핑 상품 URL을 입력하여 새 프로젝트를 생성하세요.")
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 5px;
            }}
        """)
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # URL 입력 라벨
        url_label = QLabel("상품 URL:")
        url_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 5px;
            }}
        """)
        main_layout.addWidget(url_label)
        
        # URL 입력 필드
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://shopping.naver.com/catalog/...")
        self.url_input.textChanged.connect(self._clear_validation_error)  # 입력시 오류 메시지 제거
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 15px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {ModernStyle.COLORS['primary']}88;
            }}
        """)
        main_layout.addWidget(self.url_input)
        
        # 상품명 입력 라벨
        product_name_label = QLabel("상품명:")
        product_name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 500;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 5px;
                margin-top: 15px;
            }}
        """)
        main_layout.addWidget(product_name_label)
        
        # 상품명 입력 필드
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("검색될 수 있는 키워드 또는 상품명을 입력해주세요")
        self.product_name_input.textChanged.connect(self._clear_validation_error)  # 입력시 오류 메시지 제거
        self.product_name_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 15px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: {ModernStyle.COLORS['primary']}88;
            }}
        """)
        main_layout.addWidget(self.product_name_input)
        
        # 도움말
        help_label = QLabel("💡 팁: 네이버 쇼핑에서 상품 페이지 URL을 복사해서 붙여넣으세요.\n상품명은 키워드 생성을 위해 사용됩니다.")
        help_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {ModernStyle.COLORS['text_muted']};
                padding: 12px 15px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border-radius: 6px;
                margin: 8px 0px 15px 0px;
            }}
        """)
        help_label.setWordWrap(True)
        main_layout.addWidget(help_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                min-width: 90px;
                margin-right: 12px;
            }}
            QPushButton:hover {{
                background-color: #f1f5f9;
                color: {ModernStyle.COLORS['text_primary']};
                border-color: #cbd5e1;
            }}
        """)
        button_layout.addWidget(self.cancel_button)
        
        # 생성 버튼
        self.create_button = QPushButton("프로젝트 생성")
        self.create_button.clicked.connect(self.accept)
        self.create_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
                color: white;
            }}
        """)
        self.create_button.setDefault(True)
        button_layout.addWidget(self.create_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 크기 설정 - 내용에 맞게 자동 조정
        self.adjustSize()
        self.setMinimumWidth(580)
        self.setMaximumWidth(700)
        self.setMinimumHeight(480)  # 최소 높이를 충분히 늘려서 모든 내용이 보이도록
        
        # 실제 필요한 높이 계산하여 설정
        required_height = main_layout.sizeHint().height() + 100  # 여유 공간 충분히 추가
        if required_height > 480:
            self.resize(580, required_height)
        else:
            self.resize(580, 480)
    
    def position_dialog(self):
        """버튼 위치 근처에 다이얼로그 표시"""
        if self.button_pos and self.parent():
            # 버튼의 전역 좌표 계산
            button_global_pos = self.parent().mapToGlobal(self.button_pos)
            
            # 화면 크기 가져오기
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # 다이얼로그 크기
            dialog_width = self.width() if self.width() > 0 else 400
            dialog_height = self.height() if self.height() > 0 else 300
            
            # 버튼 위쪽에 다이얼로그 배치 (100px 간격)
            x = button_global_pos.x() - dialog_width // 2
            y = button_global_pos.y() - dialog_height - 100
            
            # 화면 경계 체크 및 조정
            if x < screen_rect.left():
                x = screen_rect.left() + 10
            elif x + dialog_width > screen_rect.right():
                x = screen_rect.right() - dialog_width - 10
                
            if y < screen_rect.top():
                y = screen_rect.top() + 10
            
            self.move(x, y)
        else:
            # 기본 중앙 정렬
            self.center_on_parent()
    
    def center_on_parent(self):
        """부모 윈도우 중앙에 위치"""
        if self.parent():
            parent_geo = self.parent().geometry()
            parent_pos = self.parent().mapToGlobal(parent_geo.topLeft())
            
            center_x = parent_pos.x() + parent_geo.width() // 2 - self.width() // 2
            center_y = parent_pos.y() + parent_geo.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
            center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
    
    def accept(self):
        """생성 버튼 클릭"""
        url = self.url_input.text().strip()
        product_name = self.product_name_input.text().strip()
        
        # URL 비어있음 검사
        if not url:
            self._show_validation_error("URL을 입력해주세요.")
            return
        
        # 상품명 비어있음 검사
        if not product_name:
            self._show_validation_error("상품명을 입력해주세요.")
            return
        
        # URL 형식 검사
        if not self._validate_url_format(url):
            self._show_validation_error("올바른 네이버 쇼핑 URL을 입력해주세요.\n예: https://shopping.naver.com/catalog/...")
            return
        
        self.result_url = url
        self.result_product_name = product_name
        self.result_ok = True
        super().accept()
    
    def _validate_url_format(self, url: str) -> bool:
        """네이버 쇼핑 URL 형식 검증"""
        import re
        
        # 네이버 쇼핑 URL 패턴들
        patterns = [
            r'https?://shopping\.naver\.com/catalog/\d+',  # catalog 패턴
            r'https?://smartstore\.naver\.com/[^/]+/products/\d+',  # 스마트스토어 패턴
            r'https?://brand\.naver\.com/[^/]+/products/\d+',  # 브랜드스토어 패턴
        ]
        
        for pattern in patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def _show_validation_error(self, message: str):
        """검증 오류 메시지 표시"""
        # 기존 오류 메시지가 있으면 제거
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
        
        # 오류 라벨 생성
        self.error_label = QLabel(message)
        self.error_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['danger']};
                font-size: 12px;
                padding: 8px 15px;
                background-color: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                margin: 5px 0px;
            }}
        """)
        self.error_label.setWordWrap(True)
        
        # URL 입력 필드 아래에 삽입
        layout = self.layout()
        url_input_index = -1
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget == self.url_input:
                url_input_index = i
                break
        
        if url_input_index >= 0:
            layout.insertWidget(url_input_index + 1, self.error_label)
    
    def _clear_validation_error(self):
        """검증 오류 메시지 제거"""
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
    
    def reject(self):
        """취소 버튼 클릭"""
        self.result_url = ""
        self.result_product_name = ""
        self.result_ok = False
        super().reject()
    
    @classmethod
    def getProjectData(cls, parent, button_widget=None):
        """프로젝트 데이터 입력 다이얼로그 표시"""
        button_pos = None
        if button_widget:
            # 버튼의 중앙 위치 계산
            button_rect = button_widget.geometry()
            button_pos = button_rect.center()
        
        dialog = cls(parent, button_pos)
        dialog.exec()
        return dialog.result_url, dialog.result_product_name, dialog.result_ok
