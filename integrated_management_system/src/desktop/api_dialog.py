"""
API 설정 다이얼로그
사용자가 네이버 API 키들을 입력/관리할 수 있는 UI
"""
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QWidget, QGroupBox, QFormLayout, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from src.toolbox.ui_kit import ModernStyle

class APISettingsDialog(QDialog):
    """API 설정 다이얼로그"""
    
    # 시그널 정의
    api_settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 API 설정")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 제목
        title_label = QLabel("네이버 API 설정")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
        """)
        layout.addWidget(title_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.setup_naver_tab()  # 통합된 네이버 API 탭
        self.setup_ai_tab()     # AI API 탭
        self.setup_help_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 하단 버튼들
        self.setup_buttons(layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def setup_naver_tab(self):
        """통합된 네이버 API 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 전체 설명
        desc = QLabel("블로그, 뉴스, 데이터랩 검색을 위한 네이버 개발자 API와\n실제 월 검색량 조회를 위한 네이버 검색광고 API 키를 입력하세요.")
        desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 14px;
                margin-bottom: 15px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(desc)
        
        # 네이버 개발자 API 그룹
        developers_group = QGroupBox("네이버 개발자 API")
        developers_layout = QVBoxLayout()
        developers_layout.setSpacing(10)
        
        # 설명
        dev_desc = QLabel("블로그, 뉴스, 데이터랩 검색용")
        dev_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 12px;
                margin-bottom: 8px;
            }}
        """)
        developers_layout.addWidget(dev_desc)
        
        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.shopping_client_id = QLineEdit()
        self.shopping_client_id.setPlaceholderText("네이버 개발자 센터에서 발급받은 Client ID")
        client_id_layout.addWidget(self.shopping_client_id, 1)
        developers_layout.addLayout(client_id_layout)
        
        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_layout.addWidget(QLabel("Client Secret:"))
        self.shopping_client_secret = QLineEdit()
        self.shopping_client_secret.setPlaceholderText("네이버 개발자 센터에서 발급받은 Client Secret")
        self.shopping_client_secret.setEchoMode(QLineEdit.Password)
        client_secret_layout.addWidget(self.shopping_client_secret, 1)
        developers_layout.addLayout(client_secret_layout)
        
        # 개발자 API 버튼
        dev_btn_layout = QHBoxLayout()
        # 삭제 버튼 먼저
        self.shopping_delete_btn = QPushButton("삭제")
        self.shopping_delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['danger']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)
        self.shopping_delete_btn.clicked.connect(self.delete_shopping_api)
        dev_btn_layout.addWidget(self.shopping_delete_btn)
        
        # 적용 버튼 나중에
        self.shopping_apply_btn = QPushButton("적용")
        self.shopping_apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['success']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['secondary_hover']};
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)
        self.shopping_apply_btn.clicked.connect(self.apply_shopping_api)
        dev_btn_layout.addWidget(self.shopping_apply_btn)
        dev_btn_layout.addStretch()
        developers_layout.addLayout(dev_btn_layout)
        
        # 개발자 API 상태
        self.shopping_status = QLabel("")
        self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        developers_layout.addWidget(self.shopping_status)
        
        developers_group.setLayout(developers_layout)
        layout.addWidget(developers_group)
        
        # 네이버 검색광고 API 그룹
        searchad_group = QGroupBox("네이버 검색광고 API")
        searchad_layout = QVBoxLayout()
        searchad_layout.setSpacing(10)
        
        # 설명
        searchad_desc = QLabel("실제 월 검색량 조회용")
        searchad_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 12px;
                margin-bottom: 8px;
            }}
        """)
        searchad_layout.addWidget(searchad_desc)
        
        # 액세스 라이선스
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("액세스 라이선스:"))
        self.searchad_access_license = QLineEdit()
        self.searchad_access_license.setPlaceholderText("액세스 라이선스를 입력하세요")
        api_key_layout.addWidget(self.searchad_access_license, 1)
        searchad_layout.addLayout(api_key_layout)
        
        # 비밀키
        secret_key_layout = QHBoxLayout()
        secret_key_layout.addWidget(QLabel("비밀키:"))
        self.searchad_secret_key = QLineEdit()
        self.searchad_secret_key.setPlaceholderText("••••••••••••••••••••••••••••••••")
        self.searchad_secret_key.setEchoMode(QLineEdit.Password)
        secret_key_layout.addWidget(self.searchad_secret_key, 1)
        searchad_layout.addLayout(secret_key_layout)
        
        # Customer ID
        customer_id_layout = QHBoxLayout()
        customer_id_layout.addWidget(QLabel("Customer ID:"))
        self.searchad_customer_id = QLineEdit()
        self.searchad_customer_id.setPlaceholderText("Customer ID를 입력하세요")
        customer_id_layout.addWidget(self.searchad_customer_id, 1)
        searchad_layout.addLayout(customer_id_layout)
        
        # 검색광고 API 버튼
        searchad_btn_layout = QHBoxLayout()
        # 삭제 버튼 먼저
        self.searchad_delete_btn = QPushButton("삭제")
        self.searchad_delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['danger']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)
        self.searchad_delete_btn.clicked.connect(self.delete_searchad_api)
        searchad_btn_layout.addWidget(self.searchad_delete_btn)
        
        # 적용 버튼 나중에
        self.searchad_apply_btn = QPushButton("적용")
        self.searchad_apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['success']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['secondary_hover']};
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)
        self.searchad_apply_btn.clicked.connect(self.apply_searchad_api)
        searchad_btn_layout.addWidget(self.searchad_apply_btn)
        searchad_btn_layout.addStretch()
        searchad_layout.addLayout(searchad_btn_layout)
        
        # 검색광고 API 상태
        self.searchad_status = QLabel("")
        self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        searchad_layout.addWidget(self.searchad_status)
        
        searchad_group.setLayout(searchad_layout)
        layout.addWidget(searchad_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "네이버 API")
    
    def setup_ai_tab(self):
        """AI API 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 전체 설명
        desc = QLabel("상품명 생성을 위한 AI API를 선택하고 설정하세요.\n최소 하나의 AI API가 필요합니다.")
        desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 14px;
                margin-bottom: 15px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(desc)
        
        # AI 제공자 선택 드롭박스
        ai_selector_group = QGroupBox("AI 제공자 선택")
        ai_selector_layout = QVBoxLayout()
        ai_selector_layout.setSpacing(10)
        
        # AI 제공자 콤보박스
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("AI 제공자:"))
        
        from PySide6.QtWidgets import QComboBox
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems([
            "AI 제공자를 선택하세요",
            "GPT-4o Mini (무료)",
            "GPT-4o (유료)",
            "Gemini 1.5 Flash (무료)",
            "Claude Sonnet (유료)"
        ])
        self.ai_provider_combo.currentTextChanged.connect(self.on_ai_provider_changed)
        provider_layout.addWidget(self.ai_provider_combo, 1)
        ai_selector_layout.addLayout(provider_layout)
        
        ai_selector_group.setLayout(ai_selector_layout)
        layout.addWidget(ai_selector_group)
        
        # AI API 설정 그룹 (처음에는 숨김)
        self.ai_config_group = QGroupBox("API 설정")
        self.ai_config_group.setVisible(False)
        ai_config_layout = QVBoxLayout()
        ai_config_layout.setSpacing(10)
        
        # API 키 입력
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("API Key:"))
        self.ai_api_key = QLineEdit()
        self.ai_api_key.setPlaceholderText("API 키를 입력하세요")
        self.ai_api_key.setEchoMode(QLineEdit.Password)
        api_key_layout.addWidget(self.ai_api_key, 1)
        ai_config_layout.addLayout(api_key_layout)
        
        # 적용/삭제 버튼
        ai_btn_layout = QHBoxLayout()
        
        # 삭제 버튼
        self.ai_delete_btn = QPushButton("삭제")
        self.ai_delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['danger']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)
        self.ai_delete_btn.clicked.connect(self.delete_ai_api)
        ai_btn_layout.addWidget(self.ai_delete_btn)
        
        # 적용 버튼
        self.ai_apply_btn = QPushButton("적용")
        self.ai_apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['success']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['secondary_hover']};
            }}
            QPushButton:disabled {{
                background-color: #9CA3AF;
            }}
        """)
        self.ai_apply_btn.clicked.connect(self.apply_ai_api)
        ai_btn_layout.addWidget(self.ai_apply_btn)
        
        ai_btn_layout.addStretch()
        ai_config_layout.addLayout(ai_btn_layout)
        
        # AI API 상태
        self.ai_status = QLabel("")
        self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        ai_config_layout.addWidget(self.ai_status)
        
        self.ai_config_group.setLayout(ai_config_layout)
        layout.addWidget(self.ai_config_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "AI API")
    
    def on_ai_provider_changed(self, provider_text):
        """AI 제공자 변경시 호출"""
        if provider_text == "AI 제공자를 선택하세요":
            self.ai_config_group.setVisible(False)
            self.current_ai_provider = None
            self.ai_api_key.clear()
        else:
            self.ai_config_group.setVisible(True)
            
            # 이전 제공자 정보 저장 (변경 전에)
            old_provider = getattr(self, 'current_ai_provider', None)
            old_key = self.ai_api_key.text() if hasattr(self, 'ai_api_key') else ""
            
            # 새 제공자 설정
            if "GPT" in provider_text:
                self.ai_api_key.setPlaceholderText("sk-...")
                self.current_ai_provider = "openai"
            elif "Gemini" in provider_text:
                self.ai_api_key.setPlaceholderText("Google AI API 키")
                self.current_ai_provider = "gemini"
            elif "Claude" in provider_text:
                self.ai_api_key.setPlaceholderText("Anthropic API 키")
                self.current_ai_provider = "claude"
            
            # 이전 제공자의 키를 임시 저장 (메모리에만)
            if old_provider and old_key:
                if not hasattr(self, '_temp_ai_keys'):
                    self._temp_ai_keys = {}
                self._temp_ai_keys[old_provider] = old_key
            
            # 새 제공자의 설정 로드 (파일에서 또는 임시 저장소에서)
            self.load_ai_settings_with_temp()
    
    def apply_ai_api(self):
        """AI API 테스트 후 적용"""
        if not hasattr(self, 'current_ai_provider') or not self.current_ai_provider:
            return
            
        api_key = self.ai_api_key.text().strip()
        if not api_key:
            self.ai_status.setText("⚠️ API 키를 입력해주세요.")
            self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.ai_status.setText("테스트 및 적용 중...")
        self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.ai_apply_btn.setEnabled(False)
        
        try:
            # 제공자별 테스트 실행
            if self.current_ai_provider == "openai":
                result = self.test_openai_api_internal(api_key)
            elif self.current_ai_provider == "gemini":
                result = self.test_gemini_api_internal(api_key)
            elif self.current_ai_provider == "claude":
                result = self.test_claude_api_internal(api_key)
            else:
                result = (False, "지원되지 않는 AI 제공자입니다.")
            
            if result[0]:  # 테스트 성공시 자동 적용
                # 설정 저장
                self.save_ai_config(self.current_ai_provider, api_key)
                
                # 성공시 임시 저장된 키 제거 (정식 저장되었으므로)
                if hasattr(self, '_temp_ai_keys') and self.current_ai_provider in self._temp_ai_keys:
                    del self._temp_ai_keys[self.current_ai_provider]
                
                # 변경 로그 메시지 추가
                self.log_ai_provider_change()
                
                self.ai_status.setText(f"✅ {self.ai_provider_combo.currentText()} API가 적용되었습니다.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()
            else:
                self.ai_status.setText(f"❌ 연결 실패: {result[1]}")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.ai_status.setText(f"❌ 적용 오류: {str(e)}")
            self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.ai_apply_btn.setEnabled(True)
    
    def delete_ai_api(self):
        """AI API 삭제 (foundation config_manager 사용)"""
        if not hasattr(self, 'current_ai_provider') or not self.current_ai_provider:
            return
            
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "확인", 
            f"{self.ai_provider_combo.currentText()} API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                # 현재 설정 로드
                api_config = config_manager.load_api_config()
                
                # 해당 제공자의 API 키 삭제
                if self.current_ai_provider == "openai":
                    api_config.openai_api_key = ""
                elif self.current_ai_provider == "claude":
                    api_config.claude_api_key = ""
                elif self.current_ai_provider == "gemini":
                    api_config.gemini_api_key = ""
                
                # foundation config_manager로 저장
                config_manager.save_api_config(api_config)
                
                # UI 초기화
                self.ai_api_key.clear()
                self.ai_status.setText("🟡 API를 다시 설정해 주세요.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                self.api_settings_changed.emit()
                QMessageBox.information(self, "완료", "AI API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def save_ai_config(self, provider, api_key):
        """AI API 설정 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 모든 AI API 키 초기화 (한 번에 하나만 사용)
            api_config.openai_api_key = ""
            api_config.claude_api_key = ""
            api_config.gemini_api_key = ""
            
            # 선택된 제공자만 설정
            if provider == "openai":
                api_config.openai_api_key = api_key
            elif provider == "claude":
                api_config.claude_api_key = api_key
            elif provider == "gemini":
                api_config.gemini_api_key = api_key
            
            # foundation config_manager로 저장
            config_manager.save_api_config(api_config)
                
        except Exception as e:
            print(f"AI API 설정 저장 오류: {e}")
    
    def log_ai_provider_change(self):
        """AI 제공자 변경 시 로그 메시지 출력"""
        try:
            # 공통 로그 매니저가 있는지 확인
            try:
                from .common_log import log_manager
                
                # 제공자 이름 매핑
                provider_names = {
                    'openai': 'OpenAI GPT',
                    'gemini': 'Google Gemini',
                    'claude': 'Anthropic Claude'
                }
                
                current_text = self.ai_provider_combo.currentText()
                provider_display_name = provider_names.get(self.current_ai_provider, self.current_ai_provider.upper())
                
                log_manager.add_log(f"🔄 AI 제공자가 {provider_display_name}로 변경되었습니다. ({current_text})", "info")
                
            except ImportError:
                # 로그 매니저를 찾을 수 없는 경우 콘솔에 출력
                provider_names = {
                    'openai': 'OpenAI GPT',
                    'gemini': 'Google Gemini',
                    'claude': 'Anthropic Claude'
                }
                provider_display_name = provider_names.get(self.current_ai_provider, self.current_ai_provider.upper())
                print(f"🔄 AI 제공자가 {provider_display_name}로 변경되었습니다.")
                
        except Exception as e:
            print(f"AI 제공자 변경 로그 출력 오류: {e}")
    
    
    def load_ai_settings_with_temp(self):
        """AI API 설정 로드 (foundation config 사용)"""
        if not hasattr(self, 'current_ai_provider') or not self.current_ai_provider:
            return
            
        try:
            # 먼저 임시 저장된 키가 있는지 확인
            if hasattr(self, '_temp_ai_keys') and self.current_ai_provider in self._temp_ai_keys:
                # 임시 저장된 키 사용
                temp_key = self._temp_ai_keys[self.current_ai_provider]
                self.ai_api_key.setText(temp_key)
                self.ai_status.setText("🟡 API를 적용해 주세요.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                return
            
            # 임시 키가 없으면 foundation config에서 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 현재 제공자에 따라 키 로드
            if self.current_ai_provider == "openai" and api_config.openai_api_key:
                self.ai_api_key.setText(api_config.openai_api_key)
                self.ai_status.setText(f"✅ {self.ai_provider_combo.currentText()} API가 설정되었습니다.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            elif self.current_ai_provider == "claude" and api_config.claude_api_key:
                self.ai_api_key.setText(api_config.claude_api_key)
                self.ai_status.setText(f"✅ {self.ai_provider_combo.currentText()} API가 설정되었습니다.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            elif (self.current_ai_provider == "gemini" and 
                  hasattr(api_config, 'gemini_api_key') and api_config.gemini_api_key):
                self.ai_api_key.setText(api_config.gemini_api_key)
                self.ai_status.setText(f"✅ {self.ai_provider_combo.currentText()} API가 설정되었습니다.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            else:
                # 해당 제공자 설정이 없으면 빈 필드
                self.ai_api_key.clear()
                self.ai_status.setText("🟡 API를 설정해 주세요.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
        except Exception as e:
            print(f"AI API 설정 로드 오류: {e}")
            # 오류 시 빈 필드
            self.ai_api_key.clear()
            self.ai_status.setText("🟡 API를 설정해 주세요.")
            self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
    
    
    def test_openai_api_internal(self, api_key):
        """OpenAI API 내부 테스트 (UI 업데이트 없이)"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 최소한의 토큰으로 테스트 (약 10-20 토큰 정도)
            data = {
                "model": "gpt-3.5-turbo",  # 가장 저렴한 모델로 테스트
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5  # 최소 토큰으로 제한
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def test_gemini_api_internal(self, api_key):
        """Gemini API 내부 테스트 (UI 업데이트 없이)"""
        try:
            import requests
            
            # Gemini API 테스트 (최소 토큰으로)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": "Hi"  # 최소한의 텍스트로 테스트
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 5  # 최소 토큰으로 제한
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            elif response.status_code == 400:
                error_info = response.json()
                if 'error' in error_info:
                    return False, f"API 오류: {error_info['error'].get('message', '잘못된 요청')}"
                return False, "API 키가 유효하지 않거나 잘못된 요청입니다."
            elif response.status_code == 403:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def test_claude_api_internal(self, api_key):
        """Claude API 내부 테스트 (UI 업데이트 없이)"""
        try:
            import requests
            
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Claude API 테스트 (최소 토큰으로)
            data = {
                "model": "claude-3-haiku-20240307",  # 가장 저렴한 모델로 테스트
                "max_tokens": 5,  # 최소 토큰으로 제한
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'content' in result and len(result['content']) > 0:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            elif response.status_code == 400:
                error_info = response.json()
                if 'error' in error_info:
                    return False, f"API 오류: {error_info['error'].get('message', '잘못된 요청')}"
                return False, "잘못된 요청입니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def setup_help_tab(self):
        """도움말 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_content = """
API 키 발급 방법:

🔍 네이버 검색광고 API:
1. https://manage.searchad.naver.com 접속
2. 네이버 계정으로 로그인
3. '액세스 라이선스 발급' 버튼 클릭
4. 발급 후 액세스 라이선스, 비밀키, Customer ID 확인

🛒 네이버 쇼핑 API:
1. https://developers.naver.com/main/ 접속  
2. 'Application 등록' → '애플리케이션 정보 입력'
3. '사용 API' 에서 '검색' 체크
4. 등록 완료 후 Client ID, Client Secret 확인

⚠️ 주의사항:
- API 키는 개인정보이므로 타인과 공유하지 마세요
- 월 호출 한도를 확인하고 사용하세요
- 검색광고 API는 승인 절차가 있을 수 있습니다

💾 설정 저장:
- API 키는 로컬에 안전하게 암호화되어 저장됩니다
- 프로그램 재실행시 자동으로 로드됩니다
        """
        help_text.setPlainText(help_content)
        help_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        
        layout.addWidget(help_text)
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "❓ 도움말")
    
    def setup_buttons(self, layout):
        """버튼 영역 설정"""
        button_layout = QHBoxLayout()
        
        # 모든 API 삭제 버튼 (맨 왼쪽)
        delete_all_btn = QPushButton("모든 API 삭제")
        delete_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['danger']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: #DC2626;
            }}
        """)
        delete_all_btn.clicked.connect(self.delete_all_apis)
        button_layout.addWidget(delete_all_btn)
        
        # 가운데 공간
        button_layout.addStretch()
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 저장 버튼
        save_btn = QPushButton("저장")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['success']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['secondary_hover']};
            }}
        """)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernStyle.COLORS['bg_primary']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTabWidget::pane {{
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: 10px 20px;
                margin-right: 2px;
                border-bottom: none;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-bottom: 1px solid {ModernStyle.COLORS['bg_card']};
                font-weight: 600;
            }}
            QGroupBox {{
                font-size: 14px;
                font-weight: 600;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QLineEdit {{
                padding: 8px 12px;
                border: 2px solid {ModernStyle.COLORS['border']};
                border-radius: 6px;
                font-size: 14px;
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
        """)
    
    def load_settings(self):
        """foundation config_manager에서 API 키 로드"""
        try:
            from src.foundation.config import config_manager
            
            # foundation config에서 로드
            api_config = config_manager.load_api_config()
            
            # 네이버 검색광고 API
            self.searchad_access_license.setText(api_config.searchad_access_license)
            self.searchad_secret_key.setText(api_config.searchad_secret_key)
            self.searchad_customer_id.setText(api_config.searchad_customer_id)
            
            # 네이버 쇼핑 API
            self.shopping_client_id.setText(api_config.shopping_client_id)
            self.shopping_client_secret.setText(api_config.shopping_client_secret)
            
            # AI API 설정 로드 (별도 처리)
            self.load_ai_settings_from_foundation(api_config)
            
            # 로드 후 상태 체크
            self.check_api_status()
            
        except Exception as e:
            print(f"설정 로드 오류: {e}")
            self.check_api_status()
    
    def load_ai_settings_from_foundation(self, api_config):
        """foundation config에서 AI API 설정 로드"""
        try:
            # OpenAI가 설정되어 있으면
            if api_config.openai_api_key:
                # GPT 관련 옵션 찾기
                for i in range(self.ai_provider_combo.count()):
                    item_text = self.ai_provider_combo.itemText(i)
                    if "GPT" in item_text:
                        self.ai_provider_combo.setCurrentIndex(i)
                        self.on_ai_provider_changed(item_text)
                        self.ai_api_key.setText(api_config.openai_api_key)
                        self.ai_status.setText(f"✅ {item_text} API가 적용되었습니다.")
                        self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                        return
            
            # Claude가 설정되어 있으면
            elif api_config.claude_api_key:
                for i in range(self.ai_provider_combo.count()):
                    item_text = self.ai_provider_combo.itemText(i)
                    if "Claude" in item_text:
                        self.ai_provider_combo.setCurrentIndex(i)
                        self.on_ai_provider_changed(item_text)
                        self.ai_api_key.setText(api_config.claude_api_key)
                        self.ai_status.setText(f"✅ {item_text} API가 적용되었습니다.")
                        self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                        return
            
            # Gemini가 설정되어 있으면
            elif hasattr(api_config, 'gemini_api_key') and api_config.gemini_api_key:
                for i in range(self.ai_provider_combo.count()):
                    item_text = self.ai_provider_combo.itemText(i)
                    if "Gemini" in item_text:
                        self.ai_provider_combo.setCurrentIndex(i)
                        self.on_ai_provider_changed(item_text)
                        self.ai_api_key.setText(api_config.gemini_api_key)
                        self.ai_status.setText(f"✅ {item_text} API가 적용되었습니다.")
                        self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                        return
            
            # 아무것도 설정되지 않은 경우
            self.ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
            self.ai_config_group.setVisible(False)
                
        except Exception as e:
            print(f"AI 설정 로드 오류: {e}")
    
    
    def save_settings(self):
        """설정 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 네이버 API 설정 업데이트 (텍스트 필드 값으로)
            api_config.searchad_access_license = self.searchad_access_license.text().strip()
            api_config.searchad_secret_key = self.searchad_secret_key.text().strip()
            api_config.searchad_customer_id = self.searchad_customer_id.text().strip()
            
            api_config.shopping_client_id = self.shopping_client_id.text().strip()
            api_config.shopping_client_secret = self.shopping_client_secret.text().strip()
            
            # AI API는 현재 선택된 제공자와 입력된 키로 업데이트
            if (hasattr(self, 'current_ai_provider') and self.current_ai_provider and 
                hasattr(self, 'ai_api_key') and self.ai_api_key.text().strip()):
                
                # 모든 AI API 키 초기화
                api_config.openai_api_key = ""
                api_config.claude_api_key = ""
                api_config.gemini_api_key = ""
                
                # 현재 선택된 제공자만 설정
                ai_key = self.ai_api_key.text().strip()
                if self.current_ai_provider == "openai":
                    api_config.openai_api_key = ai_key
                elif self.current_ai_provider == "claude":
                    api_config.claude_api_key = ai_key
                elif self.current_ai_provider == "gemini":
                    api_config.gemini_api_key = ai_key
            
            # foundation config_manager로 저장
            success = config_manager.save_api_config(api_config)
            
            if success:
                QMessageBox.information(self, "완료", "API 설정이 저장되었습니다.")
                self.api_settings_changed.emit()  # 설정 변경 시그널 발송
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "API 설정 저장에 실패했습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패: {str(e)}")
    
    
    def apply_searchad_api(self):
        """검색광고 API 테스트 후 적용"""
        access_license = self.searchad_access_license.text().strip()
        secret_key = self.searchad_secret_key.text().strip()
        customer_id = self.searchad_customer_id.text().strip()
        
        if not all([access_license, secret_key, customer_id]):
            self.searchad_status.setText("⚠️ 모든 필드를 입력해주세요.")
            self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.searchad_status.setText("테스트 및 적용 중...")
        self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.searchad_apply_btn.setEnabled(False)
        
        try:
            # 테스트 먼저 실행
            result = self.test_searchad_api_internal(access_license, secret_key, customer_id)
            if result[0]:  # 테스트 성공시 자동 적용
                # 설정 저장
                self.save_searchad_config(access_license, secret_key, customer_id)
                self.searchad_status.setText("✅ 네이버 검색광고 API가 적용되었습니다.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()  # API 적용 시그널 발송
            else:
                self.searchad_status.setText(f"❌ 연결 실패: {result[1]}")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.searchad_status.setText(f"❌ 적용 오류: {str(e)}")
            self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.searchad_apply_btn.setEnabled(True)
    
    def test_searchad_api_internal(self, access_license, secret_key, customer_id):
        """검색광고 API 내부 테스트 (UI 업데이트 없이)"""
        import requests
        import hashlib
        import hmac
        import base64
        import time
        
        try:
            uri = '/keywordstool'
            timestamp = str(int(time.time() * 1000))
            message = f"{timestamp}.GET.{uri}"
            signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
            signature = base64.b64encode(signature).decode()
            
            headers = {
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Timestamp': timestamp,
                'X-API-KEY': access_license,
                'X-Customer': customer_id,
                'X-Signature': signature
            }
            
            params = {'hintKeywords': '테스트', 'showDetail': '1'}
            
            response = requests.get(
                'https://api.searchad.naver.com' + uri,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'keywordList' in data:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    
    def apply_shopping_api(self):
        """쇼핑 API 테스트 후 적용"""
        client_id = self.shopping_client_id.text().strip()
        client_secret = self.shopping_client_secret.text().strip()
        
        if not all([client_id, client_secret]):
            self.shopping_status.setText("⚠️ 모든 필드를 입력해주세요.")
            self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.shopping_status.setText("테스트 및 적용 중...")
        self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.shopping_apply_btn.setEnabled(False)
        
        try:
            # 테스트 먼저 실행
            result = self.test_shopping_api_internal(client_id, client_secret)
            if result[0]:  # 테스트 성공시 자동 적용
                # 설정 저장
                self.save_shopping_config(client_id, client_secret)
                self.shopping_status.setText("✅ 네이버 개발자 API가 적용되었습니다.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()  # API 적용 시그널 발송
            else:
                self.shopping_status.setText(f"❌ 연결 실패: {result[1]}")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.shopping_status.setText(f"❌ 적용 오류: {str(e)}")
            self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.shopping_apply_btn.setEnabled(True)
    
    def test_shopping_api_internal(self, client_id, client_secret):
        """쇼핑 API 내부 테스트 (UI 업데이트 없이)"""
        import requests
        
        try:
            headers = {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret
            }
            params = {'query': '테스트', 'display': 1}
            
            response = requests.get(
                "https://openapi.naver.com/v1/search/shop.json",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    
    def save_searchad_config(self, access_license, secret_key, customer_id):
        """검색광고 API 설정만 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 검색광고 API 설정 업데이트
            api_config.searchad_access_license = access_license
            api_config.searchad_secret_key = secret_key
            api_config.searchad_customer_id = customer_id
            
            # foundation config_manager로 저장
            config_manager.save_api_config(api_config)
                
        except Exception as e:
            print(f"검색광고 API 설정 저장 오류: {e}")
    
    def save_shopping_config(self, client_id, client_secret):
        """쇼핑 API 설정만 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 쇼핑 API 설정 업데이트
            api_config.shopping_client_id = client_id
            api_config.shopping_client_secret = client_secret
            
            # foundation config_manager로 저장
            config_manager.save_api_config(api_config)
                
        except Exception as e:
            print(f"쇼핑 API 설정 저장 오류: {e}")
    
    def check_api_status(self):
        """API 상태 체크 및 표시 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # foundation config에서 로드
            api_config = config_manager.load_api_config()
            
            # 검색광고 API 상태 체크
            if api_config.is_searchad_valid():
                self.searchad_status.setText("✅ 네이버 검색광고 API가 설정되었습니다.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            else:
                self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            
            # 쇼핑 API 상태 체크
            if api_config.is_shopping_valid():
                self.shopping_status.setText("✅ 네이버 개발자 API가 설정되었습니다.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            else:
                self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            
            # AI API 상태 체크
            if hasattr(self, 'ai_status'):
                has_ai = (api_config.openai_api_key or api_config.claude_api_key or 
                         getattr(api_config, 'gemini_api_key', ''))
                if has_ai:
                    # 어떤 AI가 설정되어 있는지 확인
                    if api_config.openai_api_key:
                        provider_name = "OpenAI"
                    elif api_config.claude_api_key:
                        provider_name = "Claude"
                    elif getattr(api_config, 'gemini_api_key', ''):
                        provider_name = "Gemini"
                    else:
                        provider_name = "AI"
                    
                    self.ai_status.setText(f"✅ {provider_name} API가 설정되었습니다.")
                    self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                else:
                    self.ai_status.setText("🟡 AI API를 설정해 주세요.")
                    self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
        except Exception as e:
            print(f"API 상태 체크 오류: {e}")
            # 오류시 기본 상태
            self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
            self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
            self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            if hasattr(self, 'ai_status'):
                self.ai_status.setText("🟡 AI API를 설정해 주세요.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
    

    def delete_shopping_api(self):
        """쇼핑 API 삭제 (foundation config_manager 사용)"""
        reply = QMessageBox.question(
            self, "확인", 
            "네이버 개발자 API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                # 현재 설정 로드
                api_config = config_manager.load_api_config()
                
                # 쇼핑 API 설정 초기화
                api_config.shopping_client_id = ""
                api_config.shopping_client_secret = ""
                
                # foundation config_manager로 저장
                config_manager.save_api_config(api_config)
                
                # UI 초기화
                self.shopping_client_id.clear()
                self.shopping_client_secret.clear()
                self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                # 시그널 발송
                self.api_settings_changed.emit()
                
                QMessageBox.information(self, "완료", "네이버 개발자 API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def delete_searchad_api(self):
        """검색광고 API 삭제 (foundation config_manager 사용)"""
        reply = QMessageBox.question(
            self, "확인", 
            "네이버 검색광고 API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                # 현재 설정 로드
                api_config = config_manager.load_api_config()
                
                # 검색광고 API 설정 초기화
                api_config.searchad_access_license = ""
                api_config.searchad_secret_key = ""
                api_config.searchad_customer_id = ""
                
                # foundation config_manager로 저장
                config_manager.save_api_config(api_config)
                
                # UI 초기화
                self.searchad_access_license.clear()
                self.searchad_secret_key.clear()
                self.searchad_customer_id.clear()
                self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                # 시그널 발송
                self.api_settings_changed.emit()
                
                QMessageBox.information(self, "완료", "네이버 검색광고 API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def delete_all_apis(self):
        """모든 API 삭제 (foundation config_manager 사용)"""
        reply = QMessageBox.question(
            self, "확인", 
            "모든 API 설정을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                from src.foundation.config import APIConfig
                
                # 빈 API 설정으로 초기화
                empty_config = APIConfig()
                config_manager.save_api_config(empty_config)
                
                # 모든 UI 초기화
                self.shopping_client_id.clear()
                self.shopping_client_secret.clear()
                self.searchad_access_license.clear()
                self.searchad_secret_key.clear()
                self.searchad_customer_id.clear()
                
                # AI 설정도 초기화
                if hasattr(self, 'ai_api_key'):
                    self.ai_api_key.clear()
                if hasattr(self, 'ai_provider_combo'):
                    self.ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                if hasattr(self, 'ai_config_group'):
                    self.ai_config_group.setVisible(False)
                
                # 상태 초기화
                self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                if hasattr(self, 'ai_status'):
                    self.ai_status.setText("🟡 API를 설정해 주세요.")
                    self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                # 시그널 발송
                self.api_settings_changed.emit()
                
                QMessageBox.information(self, "완료", "모든 API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")  