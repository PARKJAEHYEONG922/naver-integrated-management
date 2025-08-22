"""
순위 추적 관련 다이얼로그들
기존 통합관리프로그램의 다이얼로그들을 새 구조에 맞게 구현
"""
from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.toolbox.ui_kit import ModernStyle
from src.foundation.logging import get_logger

logger = get_logger("features.rank_tracking.keyword_dialogs")


class AddKeywordsDialog(QDialog):
    """키워드 추가 다이얼로그 (원본과 완전 동일)"""
    
    def __init__(self, project=None, parent=None):
        super().__init__(parent)
        self.project = project
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("키워드 추가")
        self.setModal(True)
        self.setMinimumSize(560, 520)
        self.resize(560, 520)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 25, 30, 30)
        main_layout.setSpacing(20)
        
        # 헤더
        header_label = QLabel("📝 키워드 추가")
        header_label.setStyleSheet("""
            QLabel {
                color: #2563eb;
                font-size: 20px;
                font-weight: bold;
                padding: 0 0 5px 0;
                margin: 0;
            }
        """)
        main_layout.addWidget(header_label)
        
        # 설명
        self.description_label = QLabel("추적할 키워드를 입력하세요")
        self.description_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 14px;
                margin: 0 0 10px 0;
            }
        """)
        main_layout.addWidget(self.description_label)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                color: #e2e8f0;
                background-color: #e2e8f0;
                border: none;
                height: 1px;
            }
        """)
        main_layout.addWidget(separator)
        
        # 입력 라벨
        input_label = QLabel("키워드 목록")
        input_label.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 13px;
                font-weight: 600;
                margin: 5px 0;
            }
        """)
        main_layout.addWidget(input_label)
        
        # 키워드 입력 필드
        self.keywords_input = QTextEdit()
        self.keywords_input.setPlaceholderText("예:\n강아지 사료\n고양이 간식\n반려동물 장난감\n\n또는 쉼표로 구분: 강아지 사료, 고양이 간식, 반려동물 장난감")
        self.keywords_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                background-color: #ffffff;
                color: #1e293b;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #2563eb;
                outline: none;
            }
        """)
        self.keywords_input.setMinimumHeight(160)
        self.keywords_input.setMaximumHeight(160)
        main_layout.addWidget(self.keywords_input)
        
        # 안내 텍스트
        help_label = QLabel("ℹ️ 각 줄에 하나씩 입력하거나 쉼표(,)로 구분해서 입력하세요")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 12px;
                line-height: 1.4;
                padding: 8px 12px;
                background-color: #f1f5f9;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
                margin: 5px 0 10px 0;
            }
        """)
        main_layout.addWidget(help_label)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("추가")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 포커스 설정
        self.keywords_input.setFocus()
    
    def get_keywords(self) -> List[str]:
        """입력된 키워드들을 파싱해서 리스트로 반환"""
        text = self.keywords_input.toPlainText().strip()
        if not text:
            return []
        
        keywords = []
        
        # 쉼표로 구분된 경우와 줄 바꿈으로 구분된 경우 모두 처리
        if ',' in text:
            # 쉼표로 구분된 경우
            for keyword in text.split(','):
                keyword = keyword.strip()
                if keyword:
                    keywords.append(keyword)
        else:
            # 줄 바꿈으로 구분된 경우
            for line in text.split('\n'):
                keyword = line.strip()
                if keyword:
                    keywords.append(keyword)
        
        # 중복 제거하면서 순서 유지 + 영어 대문자 변환
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            # 영어는 대문자로 변환, 한글은 그대로 유지
            processed_keyword = ""
            for char in keyword:
                if char.isalpha() and char.isascii():  # 영문자만 대문자 변환
                    processed_keyword += char.upper()
                else:
                    processed_keyword += char
            
            normalized = processed_keyword.upper().replace(' ', '')
            if normalized not in seen:
                seen.add(normalized)
                unique_keywords.append(processed_keyword)  # 처리된 키워드 저장
        
        return unique_keywords