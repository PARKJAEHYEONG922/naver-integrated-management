"""
네이버 상품명 생성기 메인 UI
컨트롤 위젯과 결과 위젯을 조합하는 컨테이너 역할
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSplitter, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.desktop.common_log import log_manager
from .ui_list import ProductTitleInputWidget
from .ui_table import ProductTitleResultWidget, RealTimeDebugDialog
from .worker import AnalysisWorker, TitleGenerationWorker
from .adapters import product_title_adapters


class ProductTitleGeneratorWidget(QWidget):
    """네이버 상품명 생성기 메인 UI 컨테이너"""
    
    def __init__(self):
        super().__init__()
        # AI 분석 디버깅용 데이터 저장 변수들
        self.analysis_debug_data = {
            'original_titles': [],     # 원본 상품명 100개
            'title_stats': {},        # 상품명 글자수 통계
            'ai_tokens': [],          # AI가 추출한 토큰들  
            'ai_prompt': '',          # AI에게 보낸 프롬프트
            'ai_response': '',        # AI 응답 원문
            'keyword_combinations': [], # 프로그램이 생성한 조합들
            'combinations_stats': {},  # 조합 통계 정보
            'search_volumes': {},     # 각 키워드별 검색량
            'filtered_keywords': [],  # 검색량 필터링 후 남은 키워드들
            'category_matches': {},   # 카테고리 일치 결과
            'final_keywords': []      # 최종 선별된 키워드들
        }
        self.debug_dialog = None  # 디버그 창 참조
        self.analysis_worker = None
        self.title_worker = None
        self.category_info = {}
        self.keyword_categories = {}
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 헤더 섹션 (제목 + 설명)
        self.setup_header(main_layout)
        
        # 입력 섹션 (고정 높이)
        input_group = self.input_widget = ProductTitleInputWidget()
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameStyle(QFrame.Sunken)
        
        # 상단 컨테이너 (입력 + 구분선)
        top_container = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setSpacing(0)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(input_group)
        top_layout.addWidget(line)
        top_container.setLayout(top_layout)
        
        # 스크롤 가능한 결과 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 스크롤 컨텐츠
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(15)
        
        # 결과 위젯 (진행상황 + 결과)
        self.result_widget = ProductTitleResultWidget()
        scroll_layout.addWidget(self.result_widget)
        
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        
        # QSplitter로 위/아래 비율 고정
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        splitter.addWidget(top_container)
        splitter.addWidget(scroll_area)
        
        # 초깃값 비율(위=220px, 아래=나머지)
        splitter.setSizes([220, 1200])
        # 아래쪽을 계속 넓게: 아래 패널에 스트레치
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # 입력 위젯이 레이아웃 계산된 후, 높이 고정
        QTimer.singleShot(0, lambda: self.input_widget.setMaximumHeight(self.input_widget.sizeHint().height()))
        
    def setup_header(self, layout):
        """메인 타이틀과 설명 추가"""
        # 제목
        title_label = QLabel("🏷️ 네이버 상품명 생성기")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: 10px;
            }}
        """)
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("AI와 네이버 API를 활용하여 SEO 최적화된 상품명을 자동 생성합니다.")
        desc_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                margin-bottom: 20px;
            }}
        """)
        layout.addWidget(desc_label)
        
    def setup_connections(self):
        """시그널 연결"""
        # 입력 위젯 시그널
        self.input_widget.analyze_requested.connect(self.start_analysis)
        self.input_widget.stop_requested.connect(self.stop_analysis)
        
        # 결과 위젯 시그널
        self.result_widget.debug_requested.connect(self.show_ai_analysis_debug)
        self.result_widget.export_requested.connect(self.export_to_excel)
        self.result_widget.generate_requested.connect(self.start_title_generation)
        
    def start_analysis(self, input_data: dict):
        """분석 시작"""
        # 필요한 설정은 service/adapters에서 내부적으로 처리됨
            
        # UI 상태 변경
        self.input_widget.set_analysis_mode(True)
        self.result_widget.set_progress_visible(True)
        
        log_manager.add_log(f"🔍 상품 분석 시작: {input_data['brand']} - {input_data['keyword']} ({input_data['spec']})", "info")
        
        # 분석 데이터 초기화
        self.analysis_debug_data = {
            'original_titles': [],
            'title_stats': {},
            'ai_tokens': [],
            'ai_prompt': '',
            'ai_response': '',
            'keyword_combinations': [],
            'combinations_stats': {},
            'search_volumes': {},
            'filtered_keywords': [],
            'category_matches': {},
            'final_keywords': []
        }
        
        # 분석 시작과 함께 상단 컴팩트 모드
        self.input_widget.set_compact_mode(True)
        
        # 워커 스레드 시작
        self.analysis_worker = AnalysisWorker(
            input_data['brand'], 
            input_data['keyword'], 
            input_data['spec']
        )
        self.analysis_worker.progress_updated.connect(self.result_widget.update_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        self.analysis_worker.start()
    
    def stop_analysis(self):
        """분석 정지"""
        if hasattr(self, 'analysis_worker') and self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            
            # UI 상태 복원
            self.input_widget.set_analysis_mode(False)
            self.result_widget.set_progress_visible(False)
            self.result_widget.reset_status()
            
            log_manager.add_log("⏹️ 분석이 사용자에 의해 중단되었습니다.", "warning")
    
    def on_debug_step_updated(self, step_name: str, data):
        """실시간 디버그 단계 업데이트"""
        if step_name == "original_titles":
            if isinstance(data, dict) and 'titles' in data:
                self.analysis_debug_data['original_titles'] = data['titles']
                self.analysis_debug_data['title_stats'] = {
                    'count': data['count'],
                    'avg_length': data['avg_length'],
                    'min_length': data['min_length'],
                    'max_length': data['max_length']
                }
            else:
                self.analysis_debug_data['original_titles'] = data
        elif step_name == "ai_analysis":
            self.analysis_debug_data['ai_keywords'] = data.get('ai_keywords', data.get('ai_tokens', []))
            self.analysis_debug_data['ai_tokens'] = data.get('ai_keywords', data.get('ai_tokens', []))
            self.analysis_debug_data['ai_prompt'] = data.get('ai_prompt', '')
            self.analysis_debug_data['ai_response'] = data.get('ai_response', '')
            self.analysis_debug_data['provider'] = data.get('provider', '')
            self.analysis_debug_data['total_keywords'] = data.get('total_keywords', 0)
        elif step_name == "combinations":
            self.analysis_debug_data['keyword_combinations'] = data['combinations']
            self.analysis_debug_data['combinations_stats'] = {
                'single_count': data['single_count'],
                'two_word_count': data['two_word_count'],
                'three_word_count': data['three_word_count'],
                'all_keywords': data.get('all_keywords', [])
            }
        elif step_name == "search_volumes":
            self.analysis_debug_data['search_volumes'] = data
        elif step_name == "volume_filtered":
            self.analysis_debug_data['filtered_keywords'] = list(data['filtered_combinations'].keys())
        elif step_name == "category_filtered":
            self.analysis_debug_data['category_matches'] = data['category_matches']
            self.analysis_debug_data['final_keywords'] = list(data['final_combinations'].keys())
        elif step_name == "final_result":
            # 최종 결과 데이터 저장
            self.analysis_debug_data['final_filtered_keywords'] = data['final_filtered_keywords']
            self.analysis_debug_data['final_tokens'] = data['final_tokens']
            self.analysis_debug_data['removed_by_category'] = data['removed_by_category']
            self.analysis_debug_data['total_processed'] = data['total_processed']
            self.analysis_debug_data['after_volume_filter'] = data['after_volume_filter']
            self.analysis_debug_data['final_count'] = data['final_count']
            
            # 모든 중간 데이터 영구 저장
            if 'search_volumes' in data:
                self.analysis_debug_data['search_volumes'] = data['search_volumes']
            if 'volume_filtered_combinations' in data:
                self.analysis_debug_data['volume_filtered_combinations'] = data['volume_filtered_combinations']
                self.analysis_debug_data['filtered_keywords'] = list(data['volume_filtered_combinations'].keys())
            if 'category_matches' in data:
                self.analysis_debug_data['category_matches'] = data['category_matches']
            
            self.analysis_debug_data['analysis_completed'] = True
        
        # 디버그 창이 열려있으면 실시간 업데이트
        if self.debug_dialog and self.debug_dialog.isVisible():
            self.debug_dialog.update_step(step_name, data)
    
    def on_analysis_completed(self, result):
        """분석 완료 (AnalysisResult 객체 수신)"""
        # AnalysisResult -> UI에서 쓰는 구조로 매핑
        self.category_info = {
            'main_category': result.main_category,
            'ratio': result.category_ratio
        }
        self.keyword_categories = {}  # 추후 필요시 확장
        
        # 토큰 체크박스 추가
        self.result_widget.add_token_checkboxes(
            result.final_tokens, 
            result.search_volumes, 
            self.keyword_categories
        )
        
        # UI 상태 복원
        self.input_widget.set_analysis_mode(False)
        
        log_manager.add_log("✅ 분석 완료! 키워드를 선택해주세요.", "success")
        log_manager.add_log(f"📂 메인 카테고리: {result.main_category} ({result.category_ratio:.1f}%)", "info")
        log_manager.add_log(f"🔍 추출된 키워드: {len(result.final_tokens)}개", "info")
    
    def on_analysis_error(self, error_message: str):
        """분석 오류"""
        log_manager.add_log(f"❌ {error_message}", "error")
        
        # UI 상태 복원
        self.input_widget.set_analysis_mode(False)
        self.result_widget.set_progress_visible(False)
        
    def start_title_generation(self, selected_tokens: list):
        """상품명 생성 시작"""
        input_data = self.input_widget.get_input_data()
        search_volumes = getattr(self.input_widget, 'search_volumes', {})
        
        log_manager.add_log(f"✨ 선택된 키워드로 상품명 생성 중: {', '.join(selected_tokens)}", "info")
        
        # 워커 스레드 시작
        self.title_worker = TitleGenerationWorker(
            input_data['brand'], 
            input_data['keyword'], 
            input_data['spec'], 
            selected_tokens, 
            search_volumes
        )
        self.title_worker.titles_generated.connect(self.on_titles_generated)
        self.title_worker.progress_updated.connect(self.result_widget.update_progress)
        self.title_worker.error_occurred.connect(self.on_title_generation_error)
        self.title_worker.start()
    
    def on_titles_generated(self, titles: list):
        """상품명 생성 완료"""
        # 결과 표시
        self.result_widget.display_results(titles, self.category_info)
        
        log_manager.add_log("🎉 상품명 생성 완료!", "success")
    
    def on_title_generation_error(self, error_message: str):
        """상품명 생성 오류"""
        log_manager.add_log(f"❌ 상품명 생성 오류: {error_message}", "error")
        
    def show_ai_analysis_debug(self):
        """실시간 분석 과정 디버그 창 표시"""
        # 디버그 창이 이미 열려있다면 앞으로 가져오기
        if self.debug_dialog and self.debug_dialog.isVisible():
            self.debug_dialog.raise_()
            self.debug_dialog.activateWindow()
            return
        
        # 디버그 창 생성 (실시간 업데이트용)
        self.debug_dialog = RealTimeDebugDialog(self, self.analysis_debug_data)
        self.debug_dialog.show()
        
    def export_to_excel(self):
        """엑셀 저장"""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime
        
        results_data = self.result_widget.get_results_data()
        if not results_data['titles']:
            log_manager.add_log("❌ 저장할 데이터가 없습니다.", "error")
            return
        
        input_data = self.input_widget.get_input_data()
        selected_tokens = []
        for cb in self.result_widget.token_checkboxes:
            if cb.isChecked():
                text = cb.text()
                if ' / ' in text:
                    keyword_part = text.split(' / ')[0].strip()
                else:
                    keyword_part = text.strip()
                if keyword_part:
                    selected_tokens.append(keyword_part)
        
        # 파일 저장 위치 선택 (UI에서 처리)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        brand = input_data.get('brand', '')
        keyword = input_data.get('keyword', '')
        default_filename = f"상품명생성_{brand}_{keyword}_{timestamp}.xlsx"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "결과 저장 (엑셀)",
            default_filename,
            "Excel 파일 (*.xlsx);;모든 파일 (*)"
        )
        
        if not file_path:
            return
        
        # GeneratedTitle 필드명 매핑 (어댑터 호환)
        converted_titles = []
        for t in results_data['titles']:
            if isinstance(t, dict):
                # dict 형태
                converted_titles.append({
                    'title': t.get('title', ''),
                    'score': t.get('seo_score', t.get('score', 0.0)),
                    'search_volume': t.get('estimated_volume', t.get('search_volume', 0)),
                    'char_count': t.get('char_count', len(t.get('title', '')))
                })
            else:
                # GeneratedTitle 객체
                converted_titles.append({
                    'title': getattr(t, 'title', ''),
                    'score': getattr(t, 'seo_score', 0.0),
                    'search_volume': getattr(t, 'estimated_volume', 0),
                    'char_count': getattr(t, 'char_count', 0)
                })
        
        try:
            # adapters에서 엑셀 저장 함수 호출 (file_path 직접 전달)
            product_title_adapters.export_results_to_excel(
                file_path,
                input_data,
                converted_titles,
                results_data['category_info'],
                selected_tokens
            )
            log_manager.add_log(f"📊 엑셀 파일이 저장되었습니다: {file_path}", "success")
        except Exception as e:
            log_manager.add_log(f"❌ 엑셀 저장 실패: {str(e)}", "error")