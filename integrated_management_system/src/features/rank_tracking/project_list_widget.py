"""
프로젝트 목록 위젯 - 순위추적 프로젝트 관리
기존 UI와 완전 동일한 스타일 및 기능
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QDialog, QMessageBox,
    QAbstractItemView, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.toolbox.ui_kit import ModernStyle, ModernConfirmDialog, ModernTextInputDialog, ModernInfoDialog
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernDangerButton
from src.desktop.common_log import log_manager
# Import removed to avoid circular import - will import locally when needed
from src.foundation.logging import get_logger

from .service import rank_tracking_service

logger = get_logger("features.rank_tracking.project_list_widget")


class ProjectListWidget(QWidget):
    """프로젝트 목록 위젯 - 기존과 완전 동일"""
    
    project_selected = Signal(object)  # 프로젝트 선택 시그널
    project_deleted = Signal(int)      # 프로젝트 삭제 시그널
    projects_selection_changed = Signal(list)  # 다중 프로젝트 선택 변경 시그널
    
    def __init__(self):
        super().__init__()
        self.current_project = None
        self.setup_ui()
        self.load_projects()
    
    def setup_ui(self):
        """UI 구성 - 기존과 완전 동일"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 헤더 (제목만)
        title_label = QLabel("📋 프로젝트 목록")
        title_label.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_primary']};")
        layout.addWidget(title_label)
        
        # 프로젝트 트리 (기존 스타일 정확히 복사)
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderHidden(True)
        self.project_tree.setRootIsDecorated(False)
        # 다중 선택 모드 설정
        self.project_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # itemSelectionChanged만 사용하여 중복 로그 방지
        self.project_tree.itemSelectionChanged.connect(self.on_project_selection_changed)
        
        layout.addWidget(self.project_tree)
        
        # 버튼 레이아웃 (트리 아래에 위치)
        button_layout = QHBoxLayout()
        
        # 새 프로젝트 추가 버튼
        self.add_button = ModernPrimaryButton("➕ 새 프로젝트")
        self.add_button.clicked.connect(self.add_project)
        button_layout.addWidget(self.add_button)
        
        # 프로젝트 삭제 버튼
        self.delete_button = ModernDangerButton("🗑️ 프로젝트 삭제")
        self.delete_button.clicked.connect(self.delete_selected_project)
        self.delete_button.setEnabled(False)  # 처음에는 비활성화
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    
    def apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: 8px;
            }}
            QTreeWidget {{
                background-color: {ModernStyle.COLORS['bg_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 12px;
                font-size: 15px;
                selection-background-color: transparent;
                outline: none;
                padding: 8px;
            }}
            QTreeWidget::item {{
                height: 45px;
                padding: 10px 15px;
                margin: 3px 2px;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                background-color: {ModernStyle.COLORS['bg_card']};
                font-weight: 500;
                font-size: 14px;
            }}
            QTreeWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']}15;
                border: 2px solid {ModernStyle.COLORS['primary']};
                color: {ModernStyle.COLORS['text_primary']};
                font-weight: 600;
            }}
            QTreeWidget::item:hover {{
                background-color: {ModernStyle.COLORS['primary']}08;
                border-color: {ModernStyle.COLORS['primary']}60;
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
        """)
    
    
    def add_project(self):
        """새 프로젝트 추가 - 기존 다이얼로그와 동일"""
        # 새 프로젝트 다이얼로그 표시
        # Local import to avoid circular dependency
        from .ui import NewProjectDialog
        project_url, product_name, ok = NewProjectDialog.getProjectData(self, self.add_button)
        if ok and project_url and product_name:
            self.create_project_from_data(project_url, product_name)
    
    def create_project_from_data(self, url: str, product_name: str):
        """URL과 상품명으로부터 프로젝트 생성 - 기존 원본과 완전 동일"""
        from .adapters import rank_tracking_adapter
        
        log_manager.add_log(f"🚀 새 프로젝트 생성 시작: {url}", "info")
        log_manager.add_log(f"📝 입력된 상품명: {product_name}", "info")
        
        # 1. URL에서 product ID 추출
        try:
            product_id = rank_tracking_adapter.extract_product_id_from_url(url)
        except ValueError as e:
            log_manager.add_log("❌ URL에서 상품 ID를 추출할 수 없습니다.", "error")
            from src.toolbox.ui_kit import ModernInfoDialog
            ModernInfoDialog.error(self, "오류", str(e))
            return
        
        log_manager.add_log(f"🔍 상품 ID 추출 완료: {product_id}", "success")
        
        # 2. 기존 프로젝트 중복 확인
        try:
            existing_project = rank_tracking_service.get_project_by_product_id(product_id)
            if existing_project:
                log_manager.add_log("⚠️ 이미 등록된 상품입니다.", "warning")
                log_manager.add_log(f"📂 기존 프로젝트: {existing_project.current_name}", "info")
                
                # 사용자에게 확인 요청 (기존과 동일)
                from src.toolbox.ui_kit import ModernConfirmDialog
                result = ModernConfirmDialog.question(
                    self, 
                    "중복 상품 발견", 
                    f"이미 등록된 상품입니다.\n\n상품명: {product_name}\n기존 프로젝트: {existing_project.current_name}\n\n기존 프로젝트로 이동하시겠습니까?",
                    "이동",
                    "취소"
                )
                
                if result:
                    # 기존 프로젝트를 선택하고 UI 새로고침
                    self.load_projects()
                    
                    # 해당 프로젝트를 찾아서 선택
                    for i in range(self.project_tree.topLevelItemCount()):
                        item = self.project_tree.topLevelItem(i)
                        item_project = item.data(0, Qt.UserRole)
                        if item_project and hasattr(item_project, 'id') and item_project.id == existing_project.id:
                            self.project_tree.setCurrentItem(item)
                            item.setSelected(True)
                            # 자동 선택 시에는 selection changed 이벤트가 자동으로 발생함
                            break
                    
                    log_manager.add_log("✅ 기존 프로젝트로 이동했습니다.", "success")
                
                return
        except Exception as e:
            log_manager.add_log(f"❌ 중복 확인 오류: {str(e)}", "error")
        
        # 3. 네이버 쇼핑 API로 상품 정보 조회
        log_manager.add_log("🔍 네이버 쇼핑 API로 상품 정보 조회 중...", "info")
        
        api_product_info = rank_tracking_adapter.get_product_info(product_name, product_id)
        
        if not api_product_info:
            # API 정보를 찾지 못한 경우 - 기존과 동일하게 중단
            log_manager.add_log("❌ 상품 정보 조회 실패", "error")
            log_manager.add_log("💡 검색될 수 있는 키워드 또는 상품명을 입력해 주세요", "warning")
            log_manager.add_log(f"   • URL: {url}", "info")
            log_manager.add_log(f"   • 상품명: {product_name}", "info")
            
            from src.toolbox.ui_kit import ModernInfoDialog
            ModernInfoDialog.warning(
                self, 
                "상품 정보 조회 실패", 
                f"네이버 쇼핑 API에서 상품 정보를 찾을 수 없습니다.\n\n"
                f"다음 사항을 확인해주세요:\n"
                f"• URL이 올바른 네이버 쇼핑 URL인지 확인\n"
                f"• 상품명이 정확한지 확인\n"
                f"• 해당 상품이 현재 판매중인지 확인\n\n"
                f"URL: {url}\n"
                f"상품명: {product_name}"
            )
            return
        
        # 4. 프로젝트 생성 데이터 준비
        project_data = {
            'product_id': product_id,
            'product_url': url,
            'current_name': product_name,  # 기본값
            'store_name': '',
            'price': 0,
            'category': '',
            'image_url': '',
        }
        
        if api_product_info:
            # API에서 가져온 정보로 업데이트
            project_data.update({
                'current_name': api_product_info.name or product_name,
                'store_name': api_product_info.store_name or '',
                'price': api_product_info.price or 0,
                'category': api_product_info.category or '',
                'image_url': api_product_info.image_url or '',
            })
            
            log_manager.add_log("✅ API 상품 정보 조회 성공:", "success")
            log_manager.add_log(f"   📝 실제 상품명: {project_data['current_name']}", "info")
            log_manager.add_log(f"   📂 카테고리: {project_data['category']}", "info")
            log_manager.add_log(f"   🏪 스토어명: {project_data['store_name']}", "info") 
            log_manager.add_log(f"   💰 가격: {project_data['price']:,}원", "info")
        
        # 5. 프로젝트 저장
        try:
            project = rank_tracking_service.create_project(url, product_name)
            log_manager.add_log(f"✅ 프로젝트 생성 완료 (ID: {project.id})", "success")
        except Exception as e:
            log_manager.add_log(f"❌ 프로젝트 저장 오류: {str(e)}", "error")
            from src.toolbox.ui_kit import ModernInfoDialog
            ModernInfoDialog.error(self, "오류", f"프로젝트 저장 중 오류가 발생했습니다.\n{str(e)}")
            return
        
        # 6. UI 새로고침 및 자동 선택
        self.load_projects()
        
        # 새로 생성된 프로젝트 자동 선택
        for i in range(self.project_tree.topLevelItemCount()):
            item = self.project_tree.topLevelItem(i)
            item_project = item.data(0, Qt.UserRole)
            if item_project and hasattr(item_project, 'id') and item_project.id == project.id:
                self.project_tree.setCurrentItem(item)
                item.setSelected(True)
                # 자동 선택 시에는 selection changed 이벤트가 자동으로 발생함
                break
        
        # 7. 완료 메시지
        log_manager.add_log("🎉 프로젝트 생성이 완료되었습니다!", "success")
        log_manager.add_log(f"📝 등록된 상품명: {project.current_name}", "info")
        log_manager.add_log("💡 이제 '➕ 키워드 추가' 버튼을 클릭해서 추적할 키워드를 추가하세요.", "info")
        
        from src.toolbox.ui_kit import ModernInfoDialog
        ModernInfoDialog.success(self, "생성 완료", f"프로젝트가 성공적으로 생성되었습니다.\n\n상품명: {project.current_name}\n\n키워드를 추가하려면 '➕ 키워드 추가' 버튼을 클릭하세요.")
    
    def handle_duplicate_project(self, error: 'DuplicateProjectError', product_name: str):
        """중복 프로젝트 처리 - 원본 로직과 동일"""
        from src.toolbox.ui_kit import ModernConfirmDialog
        
        existing_project = error.existing_project
        log_manager.add_log("⚠️ 이미 등록된 상품입니다.", "warning")
        log_manager.add_log(f"📂 기존 프로젝트: {existing_project.current_name}", "info")
        
        # 사용자에게 확인 요청
        result = ModernConfirmDialog.question(
            self, 
            "중복 상품 발견", 
            f"이미 등록된 상품입니다.\n\n상품명: {product_name}\n기존 프로젝트: {existing_project.current_name}\n\n기존 프로젝트로 이동하시겠습니까?",
            "이동",
            "취소"
        )
        
        if result:
            # 기존 프로젝트를 선택하고 UI 새로고침
            self.load_projects()
            
            # 해당 프로젝트를 찾아서 선택
            for i in range(self.project_tree.topLevelItemCount()):
                item = self.project_tree.topLevelItem(i)
                item_project = item.data(0, Qt.UserRole)
                if item_project and hasattr(item_project, 'id') and item_project.id == existing_project.id:
                    self.project_tree.setCurrentItem(item)
                    item.setSelected(True)
                    # 자동 선택 시에는 selection changed 이벤트가 자동으로 발생함
                    break
            
            log_manager.add_log("✅ 기존 프로젝트로 이동했습니다.", "success")
        else:
            log_manager.add_log("❌ 프로젝트 생성이 취소되었습니다.", "info")
    
    def delete_selected_project(self):
        """선택된 프로젝트들 삭제 (다중 선택 지원)"""
        selected_items = self.project_tree.selectedItems()
        if not selected_items:
            return
        
        # 선택된 프로젝트들의 정보 수집
        projects_to_delete = []
        for item in selected_items:
            project = item.data(0, Qt.UserRole)
            if project:
                projects_to_delete.append(project)
        
        if not projects_to_delete:
            return
        
        # 확인 다이얼로그
        count = len(projects_to_delete)
        if count == 1:
            project_name = projects_to_delete[0].current_name
            dialog_text = f"프로젝트 '{project_name}'를 삭제하시겠습니까?\n\n⚠️ 모든 키워드와 순위 이력이 함께 삭제됩니다."
        else:
            project_names = [p.current_name for p in projects_to_delete[:3]]
            names_text = "• " + "\n• ".join(project_names)
            if count > 3:
                names_text += f"\n• ... 외 {count - 3}개"
            dialog_text = f"{count}개의 프로젝트를 삭제하시겠습니까?\n\n{names_text}\n\n⚠️ 모든 키워드와 순위 이력이 함께 삭제됩니다."
        
        reply = ModernConfirmDialog.question(
            self, 
            "프로젝트 삭제",
            dialog_text,
            "삭제", "취소"
        )
        
        if reply:
            success_count = 0
            for project in projects_to_delete:
                try:
                    rank_tracking_service.delete_project(project.id)
                    success_count += 1
                    log_manager.add_log(f"프로젝트 '{project.current_name}' 삭제 완료", "success")
                except Exception as e:
                    log_manager.add_log(f"프로젝트 '{project.current_name}' 삭제 실패: {e}", "error")
            
            log_manager.add_log(f"{success_count}개 프로젝트 삭제 완료", "success")
            
            # UI 상태 초기화
            self.current_project = None
            self.delete_button.setEnabled(False)
            self.delete_button.setText("🗑️ 프로젝트 삭제")
            self.load_projects()  # 목록 새로고침
            self.project_deleted.emit(0)  # 프로젝트 삭제 시그널 발송
    

    def load_projects(self):
        """프로젝트 목록 로드"""
        try:
            self.project_tree.clear()
            projects = rank_tracking_service.get_all_projects(active_only=True)
            
            if projects:
                for project in projects:
                    item = QTreeWidgetItem([f"🏷️ {project.current_name}"])
                    item.setData(0, Qt.UserRole, project)  # 프로젝트 객체 전체 저장
                    self.project_tree.addTopLevelItem(item)
                log_manager.add_log(f"📋 프로젝트 목록 로드됨: {len(projects)}개", "info")
            else:
                # 프로젝트가 없을 때 안내 메시지 표시
                empty_item = QTreeWidgetItem(["📝 새 프로젝트를 추가하세요"])
                empty_item.setDisabled(True)
                empty_item.setData(0, Qt.UserRole, None)
                self.project_tree.addTopLevelItem(empty_item)
                log_manager.add_log("프로젝트가 없습니다 - 안내 메시지 표시", "info")
        except Exception as e:
            log_manager.add_log(f"❌ 프로젝트 목록 로드 실패: {e}", "error")

    def on_project_selection_changed(self):
        """선택 변경 이벤트 (다중 선택 지원)"""
        selected_items = self.project_tree.selectedItems()
        count = len(selected_items)
        
        # 선택된 프로젝트들 수집
        selected_projects = []
        for item in selected_items:
            project = item.data(0, Qt.UserRole)
            if project and hasattr(project, 'id'):
                selected_projects.append(project)
        
        # 다중 프로젝트 선택 시그널 발송 (항상)
        self.projects_selection_changed.emit(selected_projects)
        
        if count == 0:
            self.delete_button.setEnabled(False)
            self.delete_button.setText("🗑️ 프로젝트 삭제")
        elif count == 1:
            self.delete_button.setEnabled(True)
            self.delete_button.setText("🗑️ 프로젝트 삭제")
            # 단일 선택 시에만 프로젝트 상세 정보 표시
            item = selected_items[0]
            project = item.data(0, Qt.UserRole)
            if project and hasattr(project, 'id'):
                self.project_selected.emit(project.id)
                log_manager.add_log(f"🎯 {project.current_name} 프로젝트를 선택했습니다.", "info")
        else:
            self.delete_button.setEnabled(True)
            self.delete_button.setText(f"🗑️ 프로젝트 삭제 ({count}개)")
            # 다중 선택 시 기본정보는 메인 UI에서 처리
            log_manager.add_log(f"🎯 {count}개 프로젝트를 선택했습니다.", "info")
    


