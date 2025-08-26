"""
모던한 스타일의 커스텀 다이얼로그들 - 단순화 버전
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QApplication, QLineEdit, QTextEdit)
from PySide6.QtCore import Qt, QPoint
from .modern_style import ModernStyle
from . import tokens

class ModernConfirmDialog(QDialog):
    """모던한 확인 다이얼로그 - 단순화"""
    
    def __init__(self, parent=None, title="확인", message="", 
                 confirm_text="확인", cancel_text="취소", icon="❓", position_near_widget=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.icon = icon
        self.result_value = False
        self.position_near_widget = position_near_widget
        
        self.setup_ui()
        if self.position_near_widget:
            self.position_near_widget_func()
        else:
            self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)  # 모달 다이얼로그로 설정
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # 헤더 (아이콘 + 제목)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # 아이콘
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                color: {ModernStyle.COLORS['text_secondary']};
                min-width: 20px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # 메시지
        message_label = QLabel(self.message)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.5;
                margin: 10px 20px;
                padding: 15px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: 8px;
                border: 1px solid {ModernStyle.COLORS['border']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 텍스트 선택 가능
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        # 취소 버튼 (cancel_text가 None이 아닐 때만 표시)
        if self.cancel_text is not None:
            self.cancel_button = QPushButton(self.cancel_text)
            self.cancel_button.clicked.connect(self.reject)
            self.cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['bg_input']};
                    color: {ModernStyle.COLORS['text_primary']};
                    border: 1px solid {ModernStyle.COLORS['border']};
                    padding: 10px 18px;
                    border-radius: 6px;
                    font-size: 13px;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['border']};
                }}
            """)
            button_layout.addWidget(self.cancel_button)
        else:
            self.cancel_button = None
        
        # 확인 버튼
        self.confirm_button = QPushButton(self.confirm_text)
        self.confirm_button.clicked.connect(self.accept)
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary']}dd;
            }}
        """)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 동적 크기 계산을 위한 임시 조정
        self.adjustSize()
        
        # 메시지 내용에 따른 동적 크기 설정
        message_lines = self.message.count('\n') + 1
        message_length = len(self.message)
        
        # 기본 크기 설정
        base_width = 400
        base_height = 180
        
        # 텍스트 길이에 따른 너비 조정 (최대 600px)
        if message_length > 100:
            additional_width = min(200, (message_length - 100) * 2)
            base_width += additional_width
        
        # 줄 수에 따른 높이 조정
        if message_lines > 3:
            additional_height = (message_lines - 3) * 25
            base_height += additional_height
        
        # 최소/최대 크기 설정
        final_width = max(350, min(600, base_width))
        final_height = max(180, min(400, base_height))
        
        self.setMinimumWidth(final_width)
        self.setMaximumWidth(final_width + 50)  # 약간의 여유 공간
        self.resize(final_width, final_height)
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    def position_near_widget_func(self):
        """특정 위젯 근처에 위치"""
        if self.position_near_widget:
            # 위젯의 글로벌 위치 가져오기
            widget_pos = self.position_near_widget.mapToGlobal(self.position_near_widget.rect().topLeft())
            widget_rect = self.position_near_widget.geometry()
            
            # 다이얼로그를 버튼 아래쪽에 위치
            dialog_x = widget_pos.x() + widget_rect.width() // 2 - self.width() // 2
            dialog_y = widget_pos.y() + widget_rect.height() + 10  # 버튼 아래 10px 간격
            
            # 화면 경계 체크
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # 화면 오른쪽 경계 체크
            if dialog_x + self.width() > screen_rect.right():
                dialog_x = screen_rect.right() - self.width() - 10
            
            # 화면 왼쪽 경계 체크
            if dialog_x < screen_rect.left():
                dialog_x = screen_rect.left() + 10
            
            # 화면 아래쪽 경계 체크 (버튼 위쪽으로 이동)
            if dialog_y + self.height() > screen_rect.bottom():
                dialog_y = widget_pos.y() - self.height() - 10  # 버튼 위쪽으로
            
            self.move(dialog_x, dialog_y)
        else:
            self.center_on_parent()
    
    def accept(self):
        """확인 버튼 클릭"""
        self.result_value = True
        super().accept()
    
    def reject(self):
        """취소 버튼 클릭"""
        self.result_value = False
        super().reject()
    
    @classmethod
    def question(cls, parent, title, message, confirm_text="확인", cancel_text="취소"):
        """질문 다이얼로그 표시"""
        dialog = cls(parent, title, message, confirm_text, cancel_text, "❓")
        dialog.center_on_parent()
        dialog.exec()
        return dialog.result_value
    
    @classmethod
    def warning(cls, parent, title, message, confirm_text="삭제", cancel_text="취소"):
        """경고 다이얼로그 표시"""
        dialog = cls(parent, title, message, confirm_text, cancel_text, "⚠️")
        dialog.center_on_parent()
        dialog.exec()
        return dialog.result_value

class ModernInfoDialog(QDialog):
    """모던한 정보 다이얼로그 - 단순화"""
    
    def __init__(self, parent=None, title="알림", message="", icon="ℹ️"):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.icon = icon
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성 - 개선된 커스텀 디자인"""
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.title)
        self.setModal(True)
        
        # 아이콘별 색상 정의
        if self.icon == "✅":
            icon_color = "#10b981"  # 성공
            bg_color = "#f0fdf4"
            border_color = "#bbf7d0"
        elif self.icon == "❌":
            icon_color = "#ef4444"  # 에러
            bg_color = "#fef2f2"
            border_color = "#fecaca"
        elif self.icon == "⚠️":
            icon_color = "#f59e0b"  # 경고
            bg_color = "#fffbeb"
            border_color = "#fed7aa"
        else:
            icon_color = "#3b82f6"  # 기본 정보
            bg_color = "#f8fafc"
            border_color = "#e2e8f0"
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)
        
        # 헤더 (아이콘 + 제목)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # 아이콘
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {icon_color};
                min-width: 24px;
                max-width: 24px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 600;
                color: {icon_color};
                margin: 0;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 메시지
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: #4a5568;
                line-height: 1.6;
                padding: 14px 16px;
                background-color: {bg_color};
                border-radius: 6px;
                border: 1px solid {border_color};
                margin: 0;
            }}
        """)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # 버튼
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.addStretch()
        
        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {icon_color};
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {icon_color}dd;
            }}
            QPushButton:pressed {{
                background-color: {icon_color}bb;
            }}
        """)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # 크기를 내용에 맞게 동적 조정
        self.adjustSize()
        
        # 최소/최대 크기 설정
        min_width = 350
        max_width = 500
        min_height = 150
        max_height = 400
        
        # 메시지 길이에 따른 크기 조정
        message_lines = self.message.count('\n') + 1
        message_length = len(self.message)
        
        # 너비 계산
        if message_length > 80:
            width = min(max_width, min_width + (message_length - 80) * 1.5)
        else:
            width = min_width
            
        # 높이 계산
        base_height = 180
        if message_lines > 2:
            height = min(max_height, base_height + (message_lines - 2) * 20)
        else:
            height = base_height
            
        self.resize(int(width), int(height))
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    @classmethod
    def success(cls, parent, title, message):
        """성공 다이얼로그 표시"""
        dialog = cls(parent, title, message, "✅")
        dialog.center_on_parent()
        dialog.exec()
        return True
    
    @classmethod
    def warning(cls, parent, title, message, relative_widget=None):
        """경고 다이얼로그 표시 - 특정 위젯 근처에 표시 가능"""
        dialog = cls(parent, title, message, "⚠️")
        
        if relative_widget:
            dialog.position_near_widget(relative_widget)
        else:
            dialog.center_on_parent()
        
        dialog.exec()
        return True
    
    @classmethod
    def error(cls, parent, title, message):
        """에러 다이얼로그 표시"""
        dialog = cls(parent, title, message, "❌")
        dialog.center_on_parent()
        dialog.exec()
        return True
    
    def position_near_widget(self, widget):
        """특정 위젯 근처에 다이얼로그 위치"""
        if not widget:
            self.center_on_parent()
            return
            
        try:
            # 위젯의 전역 좌표 계산
            widget_pos = widget.mapToGlobal(widget.rect().topLeft())
            widget_bottom = widget_pos.y() + widget.height()
            widget_center_x = widget_pos.x() + widget.width() // 2
            
            # 다이얼로그를 위젯 바로 아래 중앙에 위치
            dialog_x = widget_center_x - self.width() // 2
            dialog_y = widget_bottom + 10  # 위젯 아래 10px 간격
            
            # 화면 경계 체크
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # x 좌표 조정 (화면 밖으로 나가지 않도록)
            if dialog_x < screen_rect.x():
                dialog_x = screen_rect.x() + 10
            elif dialog_x + self.width() > screen_rect.right():
                dialog_x = screen_rect.right() - self.width() - 10
                
            # y 좌표 조정 (화면 아래로 나가면 위젯 위로)
            if dialog_y + self.height() > screen_rect.bottom():
                dialog_y = widget_pos.y() - self.height() - 10
                
            self.move(dialog_x, dialog_y)
            
        except Exception as e:
            print(f"위젯 근처 위치 설정 실패: {e}")
            self.center_on_parent()


class ModernHelpDialog(QDialog):
    """사용법 전용 다이얼로그 - 동적 크기 조정 및 위치 지정 가능"""
    
    def __init__(self, parent=None, title="사용법", message="", button_pos=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.button_pos = button_pos
        
        self.setup_ui()
        self.position_dialog()
    
    def setup_ui(self):
        """UI 구성 - 깔끔하고 단순한 디자인"""
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 헤더
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # 아이콘
        icon_label = QLabel("📖")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['primary']}15;
                border-radius: 8px;
                padding: 8px;
                min-width: 24px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 17px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-left: 4px;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 메시지 (한 번만 추가)
        message_label = QLabel()
        message_label.setText(self.message)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.6;
                margin-left: 4px;
                margin-right: 4px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: 8px;
                padding: 18px;
                border: 1px solid {ModernStyle.COLORS['border']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # 확인 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.accept)
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary']}dd;
            }}
            QPushButton:pressed {{
                background-color: {ModernStyle.COLORS['primary']}bb;
            }}
        """)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 크기를 내용에 맞게 조정
        self.adjustSize()
        self.setMinimumWidth(500)
        self.setMaximumWidth(600)
        self.setMaximumHeight(700)
    
    def position_dialog(self):
        """버튼 위치 근처에 다이얼로그 표시"""
        if self.button_pos and self.parent():
            # 버튼 위치를 전역 좌표로 변환
            global_pos = self.parent().mapToGlobal(self.button_pos)
            
            # 화면 크기 가져오기
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # 다이얼로그가 화면을 벗어나지 않도록 조정
            x = global_pos.x() + 30  # 버튼 오른쪽에 표시
            y = global_pos.y() - 20  # 버튼 위쪽에 약간 겹치게
            
            # 화면 경계 검사
            if x + self.width() > screen_rect.right():
                x = global_pos.x() - self.width() - 10  # 버튼 왼쪽에 표시
            if y + self.height() > screen_rect.bottom():
                y = screen_rect.bottom() - self.height() - 10
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
    
    @classmethod
    def show_help(cls, parent, title, message, button_widget=None):
        """도움말 다이얼로그 표시"""
        button_pos = None
        if button_widget:
            # 버튼의 중앙 위치 계산
            button_rect = button_widget.geometry()
            button_pos = button_rect.center()
        
        dialog = cls(parent, title, message, button_pos)
        dialog.exec()
        return True


class ModernTextInputDialog(QDialog):
    """모던한 텍스트 입력 다이얼로그"""
    
    def __init__(self, parent=None, title="입력", message="", default_text="", 
                 placeholder="", multiline=False):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.default_text = default_text
        self.placeholder = placeholder
        self.multiline = multiline
        self.result_text = ""
        self.result_ok = False
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)
        
        # 제목
        if self.message:
            title_label = QLabel(self.message)
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    color: {ModernStyle.COLORS['text_primary']};
                    font-weight: 500;
                    margin-bottom: 5px;
                }}
            """)
            title_label.setWordWrap(True)
            main_layout.addWidget(title_label)
        
        # 입력 필드
        if self.multiline:
            self.text_input = QTextEdit()
            self.text_input.setPlainText(self.default_text)
            self.text_input.setMinimumHeight(120)
            if self.placeholder:
                self.text_input.setPlaceholderText(self.placeholder)
        else:
            self.text_input = QLineEdit()
            self.text_input.setText(self.default_text)
            if self.placeholder:
                self.text_input.setPlaceholderText(self.placeholder)
            self.text_input.selectAll()
        
        # 입력 필드 스타일
        input_style = f"""
            QLineEdit, QTextEdit {{
                padding: 10px 12px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                font-size: 13px;
                background-color: white;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                outline: none;
            }}
        """
        self.text_input.setStyleSheet(input_style)
        main_layout.addWidget(self.text_input)
        
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
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                min-width: 80px;
                margin-right: 10px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['border']};
            }}
        """)
        button_layout.addWidget(self.cancel_button)
        
        # 확인 버튼
        self.confirm_button = QPushButton("확인")
        self.confirm_button.clicked.connect(self.accept)
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary']}dd;
            }}
        """)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 크기 설정
        self.setMinimumWidth(400)
        self.setMaximumWidth(600)
        if self.multiline:
            self.setMinimumHeight(220)
        else:
            self.adjustSize()
    
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
        """확인 버튼 클릭"""
        if self.multiline:
            self.result_text = self.text_input.toPlainText()
        else:
            self.result_text = self.text_input.text()
        self.result_ok = True
        super().accept()
    
    def reject(self):
        """취소 버튼 클릭"""
        self.result_text = ""
        self.result_ok = False
        super().reject()
    
    @classmethod
    def getText(cls, parent, title, message, default_text="", placeholder=""):
        """텍스트 입력 다이얼로그 표시"""
        dialog = cls(parent, title, message, default_text, placeholder, False)
        dialog.exec()
        return dialog.result_text, dialog.result_ok
    
    @classmethod
    def getMultilineText(cls, parent, title, message, default_text="", placeholder=""):
        """여러 줄 텍스트 입력 다이얼로그 표시"""
        dialog = cls(parent, title, message, default_text, placeholder, True)
        dialog.exec()
        return dialog.result_text, dialog.result_ok


# ModernProjectUrlDialog는 features/rank_tracking/dialogs.py로 이동됨


class ModernSaveCompletionDialog(QDialog):
    """저장 완료 다이얼로그 - 닫기 및 폴더 열기 버튼"""
    
    def __init__(self, parent=None, title="저장 완료", message="", file_path=""):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.file_path = file_path
        self.result_open_folder = False
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성"""
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)
        
        # 헤더 (아이콘 + 제목)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # 성공 아이콘
        icon_label = QLabel("✅")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                min-width: 30px;
                max-width: 30px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # 메시지
        message_label = QLabel(self.message)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.6;
                margin: 10px 20px 10px 42px;
                padding: 15px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: 8px;
                border-left: 4px solid {ModernStyle.COLORS['success']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(message_label)
        
        # 파일 경로 표시 (있는 경우)
        if self.file_path:
            path_label = QLabel(f"📁 저장 위치: {self.file_path}")
            path_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {ModernStyle.COLORS['text_muted']};
                    margin: 5px 20px 10px 42px;
                    padding: 8px 10px;
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                    border-radius: 6px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }}
            """)
            path_label.setWordWrap(True)
            path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            main_layout.addWidget(path_label)
        
        main_layout.addStretch()
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 닫기 버튼
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.reject)
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_input']};
                color: {ModernStyle.COLORS['text_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['border']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        button_layout.addWidget(self.close_button)
        
        # 폴더 열기 버튼 (파일 경로가 있을 때만 표시)
        if self.file_path:
            self.open_folder_button = QPushButton("📁 폴더 열기")
            self.open_folder_button.clicked.connect(self.open_folder)
            self.open_folder_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['success']};
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                    color: white;
                }}
            """)
            self.open_folder_button.setDefault(True)
            button_layout.addWidget(self.open_folder_button)
        else:
            # 파일 경로가 없으면 닫기 버튼을 기본 버튼으로 설정
            self.close_button.setDefault(True)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 크기 설정
        self.adjustSize()
        self.setMinimumWidth(450)
        self.setMaximumWidth(600)
        self.setMinimumHeight(200)
        
        # 내용에 맞는 크기 계산
        required_height = main_layout.sizeHint().height() + 50
        required_width = max(450, min(600, main_layout.sizeHint().width() + 60))
        self.resize(required_width, max(200, required_height))
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    def position_near_widget(self, widget):
        """특정 위젯 근처에 다이얼로그 위치"""
        if not widget:
            self.center_on_parent()
            return
            
        try:
            # 위젯의 전역 좌표 계산
            widget_pos = widget.mapToGlobal(widget.rect().topLeft())
            widget_bottom = widget_pos.y() + widget.height()
            widget_center_x = widget_pos.x() + widget.width() // 2
            
            # 다이얼로그를 위젯 위쪽에 위치 (400px 더 위로)
            dialog_x = widget_center_x - self.width() // 2
            dialog_y = widget_pos.y() - self.height() - 400  # 위젯 위쪽 400px 간격
            
            # 화면 경계 체크
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # x 좌표 조정 (화면 밖으로 나가지 않도록)
            if dialog_x < screen_rect.x():
                dialog_x = screen_rect.x() + 10
            elif dialog_x + self.width() > screen_rect.right():
                dialog_x = screen_rect.right() - self.width() - 10
                
            # y 좌표 조정 (화면 위로 나가면 아래로 이동)
            if dialog_y < screen_rect.top():
                dialog_y = widget_bottom + 15  # 위젯 아래 15px로 이동
                
            self.move(dialog_x, dialog_y)
            
        except Exception as e:
            print(f"위젯 근처 위치 설정 실패: {e}")
            self.center_on_parent()
    
    def open_folder(self):
        """폴더 열기"""
        if self.file_path:
            import os
            import subprocess
            import platform
            
            try:
                # 파일 경로를 절대 경로로 변환
                abs_file_path = os.path.abspath(self.file_path)
                folder_path = os.path.dirname(abs_file_path)
                
                # Windows에서만 폴더 열기 (단순하게)
                if platform.system() == "Windows":
                    # 폴더만 간단하게 열기 (중복 방지)
                    os.startfile(folder_path)
                    
                elif platform.system() == "Darwin":  # macOS
                    if os.path.exists(abs_file_path):
                        subprocess.run(['open', '-R', abs_file_path])
                    else:
                        subprocess.run(['open', folder_path])
                        
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
                
                self.result_open_folder = True
                
            except Exception as e:
                print(f"폴더 열기 실패: {e}")
                # 최후의 수단: 기본 파일 관리자로 폴더 열기
                try:
                    folder_path = os.path.dirname(os.path.abspath(self.file_path))
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":
                        subprocess.run(['open', folder_path])
                    else:
                        subprocess.run(['xdg-open', folder_path])
                except Exception as e2:
                    print(f"최후 폴더 열기도 실패: {e2}")
        
        self.accept()
    
    def reject(self):
        """닫기 버튼 클릭"""
        self.result_open_folder = False
        super().reject()
    
    def accept(self):
        """폴더 열기 버튼 클릭"""
        super().accept()
    
    @classmethod
    def show_save_completion(cls, parent, title="저장 완료", message="", file_path=""):
        """저장 완료 다이얼로그 표시"""
        dialog = cls(parent, title, message, file_path)
        dialog.exec()
        return dialog.result_open_folder