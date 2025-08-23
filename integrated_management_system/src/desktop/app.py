"""
통합 관리 시스템 메인 데스크톱 애플리케이션
PySide6 기반 GUI 애플리케이션 - 기존 통합관리프로그램 UI 구조 사용
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QLabel, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer

from src.foundation.logging import get_logger
from src.desktop.sidebar import Sidebar
from src.desktop.common_log import CommonLogWidget
from .components import PlaceholderWidget, HeaderWidget, ErrorWidget
from .styles import AppStyles, WindowConfig, apply_global_styles

logger = get_logger("desktop.app")




class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.pages = {}  # 페이지 캐시
        self.feature_widgets = {}  # 등록된 기능 위젯들
        self.setup_ui()
        self.setup_window()
    
    def setup_window(self):
        """윈도우 기본 설정"""
        self.setWindowTitle("통합 관리 시스템")
        
        # 화면 크기 가져오기
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        
        # 화면 크기의 80% 정도로 설정, 최소 크기 보장
        width = max(WindowConfig.MIN_WIDTH, int(screen_size.width() * WindowConfig.SCREEN_WIDTH_RATIO))
        height = max(WindowConfig.MIN_HEIGHT, int(screen_size.height() * WindowConfig.SCREEN_HEIGHT_RATIO))
        
        self.setMinimumSize(WindowConfig.MIN_WIDTH, WindowConfig.MIN_HEIGHT)
        self.resize(width, height)
        
        # 화면 중앙에 배치
        screen_center = screen.availableGeometry().center()
        window_rect = self.frameGeometry()
        window_rect.moveCenter(screen_center)
        self.move(window_rect.topLeft())
        
        # 전체 윈도우 스타일
        self.setStyleSheet(AppStyles.get_main_window_style())
    
    def setup_ui(self):
        """UI 구성"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 전체 레이아웃 (수직)
        main_container_layout = QVBoxLayout()
        main_container_layout.setContentsMargins(WindowConfig.MAIN_MARGIN, WindowConfig.MAIN_MARGIN, 
                                                WindowConfig.MAIN_MARGIN, WindowConfig.MAIN_MARGIN)
        main_container_layout.setSpacing(0)
        
        # 헤더 추가
        self.setup_header(main_container_layout)
        
        # 메인 레이아웃 (수평)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(WindowConfig.MAIN_MARGIN, WindowConfig.MAIN_MARGIN,
                                      WindowConfig.MAIN_MARGIN, WindowConfig.MAIN_MARGIN)
        main_layout.setSpacing(0)
        
        # 사이드바 (모듈별 네비게이션)
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.switch_page)
        
        # 메인 스플리터 (컨텐츠 + 로그 분할)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 메인 컨텐츠 영역
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(AppStyles.get_content_stack_style())
        
        # 공통 로그 위젯
        self.common_log = CommonLogWidget()
        self.common_log.setMinimumWidth(WindowConfig.LOG_MIN_WIDTH)
        self.common_log.setMaximumWidth(WindowConfig.LOG_MAX_WIDTH)
        
        # 스플리터에 추가
        main_splitter.addWidget(self.content_stack)
        main_splitter.addWidget(self.common_log)
        
        # 비율 설정 (컨텐츠 70%, 로그 30%)
        main_splitter.setSizes(WindowConfig.CONTENT_LOG_RATIO)
        
        # 메인 레이아웃에 추가
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(main_splitter, 1)  # 확장 가능
        
        # 메인 영역을 위젯으로 만들어서 컨테이너에 추가
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        main_container_layout.addWidget(main_widget)
        
        central_widget.setLayout(main_container_layout)
        
        # 초기 페이지 로드 (UI 완전 초기화 후)
        QTimer.singleShot(0, self.load_initial_page)
    
    def setup_header(self, layout):
        """헤더 설정"""
        self.header = HeaderWidget()
        self.header.api_settings_requested.connect(self.open_api_settings)
        layout.addWidget(self.header)
    
    def open_api_settings(self):
        """통합 API 설정 열기"""
        try:
            from src.desktop.api_dialog import APISettingsDialog
            from PySide6.QtWidgets import QDialog
            
            dialog = APISettingsDialog(self)
            
            # API 설정 변경 시그널 연결
            if hasattr(dialog, 'api_settings_changed'):
                dialog.api_settings_changed.connect(self.on_api_settings_changed)
            
            if dialog.exec() == QDialog.Accepted:
                # API 설정 저장됨을 로그에 알림
                from src.desktop.common_log import log_manager
                log_manager.add_log("🔄 통합 API 설정이 업데이트되었습니다.", "success")
        except Exception as e:
            logger.error(f"API 설정 오류: {e}")
            QMessageBox.critical(self, "오류", f"API 설정 오류: {str(e)}")
    
    def on_api_settings_changed(self):
        """API 설정이 변경되었을 때 호출되는 함수"""
        try:
            from src.desktop.common_log import log_manager
            from src.desktop.api_checker import APIChecker
            
            log_manager.add_log("🔄 API 설정이 변경되었습니다. 연결 상태를 다시 확인합니다.", "info")
            
            # 캐시 무효화 후 API 상태 재확인
            APIChecker.invalidate_all_caches()
            QTimer.singleShot(500, self.recheck_api_status)
            
        except Exception as e:
            logger.error(f"API 설정 변경 처리 오류: {e}")
    
    def recheck_api_status(self):
        """API 상태 재확인"""
        try:
            from src.desktop.api_checker import check_api_status_on_startup
            
            is_ready = check_api_status_on_startup()
            
            if is_ready:
                from src.desktop.common_log import log_manager
                log_manager.add_log("🎉 API 설정이 완료되었습니다! 모든 기능을 사용할 수 있습니다.", "success")
            
        except Exception as e:
            logger.error(f"API 상태 재확인 오류: {e}")
    
    def load_initial_page(self):
        """초기 페이지 로드"""
        # API 상태 확인 (최우선)
        self.check_api_status_on_startup()
        
        if self.sidebar.current_page:
            self.switch_page(self.sidebar.current_page)
    
    def check_api_status_on_startup(self):
        """시작 시 API 상태 확인"""
        try:
            from src.desktop.api_checker import check_api_status_on_startup
            
            # 로그 창에 API 상태 표시
            is_ready = check_api_status_on_startup()
            
            if not is_ready:
                # 필수 API 미설정 시 추가 안내
                QTimer.singleShot(2000, self.show_api_setup_reminder)
            
        except Exception as e:
            logger.error(f"API 상태 확인 오류: {e}")
    
    def show_api_setup_reminder(self):
        """API 설정 안내 메시지 (지연 표시)"""
        try:
            from src.desktop.common_log import log_manager
            log_manager.add_log("💡 팁: 상단 메뉴의 '⚙️ API 설정' 버튼을 클릭하여 필수 API를 설정하세요.", "info")
            
        except Exception as e:
            logger.error(f"API 설정 안내 오류: {e}")
    
    def switch_page(self, page_id):
        """페이지 전환"""
        try:
            # 페이지가 이미 로드되어 있으면 재사용
            if page_id in self.pages:
                widget = self.pages[page_id]
            else:
                # 새 페이지 로드
                widget = self.load_page(page_id)
                self.pages[page_id] = widget
                self.content_stack.addWidget(widget)
            
            # 페이지 전환
            self.content_stack.setCurrentWidget(widget)
            
        except Exception as e:
            logger.error(f"페이지 로드 오류: {e}")
            QMessageBox.critical(self, "오류", f"페이지 로드 오류: {str(e)}")
    
    def load_page(self, page_id):
        """페이지 로드"""
        try:
            # 등록된 기능 위젯이 있으면 반환
            if page_id in self.feature_widgets:
                return self.feature_widgets[page_id]
            
            # 기본적으로는 플레이스홀더 표시
            module_name = self.get_module_name(page_id)
            return PlaceholderWidget(module_name, page_id)
            
        except Exception as e:
            # 오류 발생시 오류 페이지 표시
            return ErrorWidget(str(e))
    
    def get_module_name(self, module_id):
        """모듈 ID에서 이름 가져오기"""
        module_names = {
            'keyword_analysis': '키워드 검색기',
            'rank_tracking': '네이버상품 순위추적',
            'naver_cafe': '네이버 카페DB추출',
            'powerlink_analyzer': 'PowerLink 분석',
            'naver_product_title_generator': '네이버 상품명 생성기',
        }
        return module_names.get(module_id, module_id)
    
    def add_feature_tab(self, widget, title):
        """기능 탭 추가 (기존 탭 방식 호환)"""
        # 탭 제목을 기반으로 page_id 생성
        page_id = self.title_to_page_id(title)
        
        # 기능 위젯 등록
        self.feature_widgets[page_id] = widget
        
        # 사이드바에 메뉴 항목이 있으면 활성화, 없으면 추가
        if not self.sidebar.has_page(page_id):
            self.sidebar.add_page(page_id, title, "📊")
        
        logger.info(f"기능 탭 추가됨: {title} (page_id: {page_id})")
    
    def title_to_page_id(self, title):
        """탭 제목을 page_id로 변환"""
        title_map = {
            '키워드 검색기': 'keyword_analysis',
            '네이버상품 순위추적': 'rank_tracking',
            '네이버 카페DB추출': 'naver_cafe',
            'PowerLink 분석': 'powerlink_analyzer',
            '네이버 상품명 생성기': 'naver_product_title_generator',
        }
        return title_map.get(title, title.lower().replace(' ', '_'))


def run_app(load_features_func=None):
    """애플리케이션 실행"""
    try:
        app = QApplication(sys.argv)
        
        # 전역 스타일 적용
        apply_global_styles(app)
        
        # 메인 윈도우 생성
        main_window = MainWindow()
        
        # 기능 모듈 로드 (있는 경우)
        if load_features_func:
            load_features_func(main_window)
        
        main_window.show()
        
        logger.info("데스크톱 애플리케이션 시작됨")
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"애플리케이션 실행 실패: {e}")
        raise