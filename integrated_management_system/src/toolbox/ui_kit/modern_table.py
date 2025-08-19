"""
통합 모던 테이블 컴포넌트
네이버카페DB추출, 파워링크광고비 등에서 공용으로 사용하는 테이블 시스템

CLAUDE.md 준수:
- toolbox 레이어: 완전 범용 UI 컴포넌트 (벤더/비즈니스 지식 없음)
- 재사용 가능한 테이블 위젯 시스템
- 아이템 체크 방식 체크박스로 일관된 디자인
"""
from typing import List, Dict, Callable, Optional, Any
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .modern_style import ModernStyle
from .sortable_items import SortableTableWidgetItem


class ModernTableWidget(QTableWidget):
    """
    통합 모던 테이블 위젯
    
    주요 기능:
    - 아이템 체크 방식 체크박스 (일관된 디자인)
    - 통일된 스타일링 (행 높이, 글씨, 색상)
    - 헤더 체크박스 자동 구현
    - 선택 상태 관리 자동화
    - 정렬 가능한 숫자 데이터 지원
    """
    
    # 시그널 정의
    selection_changed = Signal()  # 선택 상태 변경 시
    header_checked = Signal(bool)  # 헤더 체크박스 상태 변경 시
    
    def __init__(self, 
                 columns: List[str], 
                 has_checkboxes: bool = True,
                 has_header_checkbox: bool = True,
                 parent=None):
        """
        ModernTableWidget 초기화
        
        Args:
            columns: 컬럼 헤더 리스트 ['체크', '키워드', '검색량', ...]
            has_checkboxes: 각 행에 체크박스 포함 여부
            has_header_checkbox: 헤더에 전체선택 체크박스 포함 여부
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.columns = columns
        self.has_checkboxes = has_checkboxes
        self.has_header_checkbox = has_header_checkbox
        self._updating_header = False  # 헤더 업데이트 중복 방지
        self.header_checkbox = None  # 헤더 체크박스 위젯
        
        self.setup_table()
        self.setup_styling()
        self.setup_signals()
    
    def setup_table(self):
        """테이블 기본 설정"""
        # 컬럼 설정
        self.setColumnCount(len(self.columns))
        self.setHorizontalHeaderLabels(self.columns)
        
        # 헤더 설정
        header = self.horizontalHeader()
        header.setDefaultSectionSize(120)
        header.setStretchLastSection(True)
        header.setMinimumHeight(40)  # 헤더 높이 40px로 고정
        header.setMaximumHeight(40)  # 헤더 높이 40px로 고정
        
        # 체크박스 유무에 따른 컬럼 크기 조정 방식 설정
        if self.has_checkboxes:
            # 체크박스가 있는 경우: 첫 번째 컬럼 고정, 나머지는 조정 가능
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setSectionResizeMode(0, QHeaderView.Fixed)  # 체크박스 컬럼만 고정
        else:
            # 체크박스가 없는 경우: 모든 컬럼 조정 가능
            header.setSectionResizeMode(QHeaderView.Interactive)
        
        # 행 설정 (파워링크 이전기록과 동일)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(True)
        
        # 행 높이 35px로 설정
        self.verticalHeader().setDefaultSectionSize(35)
        
        # 헤더 체크박스 설정
        if self.has_checkboxes and self.has_header_checkbox:
            self.setup_header_checkbox()
            # 첫 번째 컬럼(체크박스 컬럼) 정렬 비활성화
            self.horizontalHeader().setSortIndicatorShown(False)
            self.horizontalHeader().setSectionsClickable(True)  # 클릭은 가능하게 (체크박스용)
    
    def setup_styling(self):
        """파워링크 이전기록 테이블 스타일 기준으로 완전 통일"""
        # 체크박스 유무에 따른 첫 번째 헤더 스타일 조건부 적용
        if self.has_checkboxes:
            first_header_style = f"""
            /* 첫 번째 컬럼 (체크박스 컬럼) - 체크박스가 있는 경우 */
            QHeaderView::section:first {{
                font-size: 16px;
                color: {ModernStyle.COLORS['text_secondary']};
                font-weight: bold;
                text-align: center;
            }}
            """
            # 체크박스 컬럼 너비 고정
            column_width_setting = "self.horizontalHeader().resizeSection(0, 50)"
        else:
            first_header_style = f"""
            /* 첫 번째 컬럼 (일반 컬럼) - 체크박스가 없는 경우 */
            QHeaderView::section:first {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_primary']};
                font-weight: 600;
                text-align: center;
            }}
            """
            column_width_setting = None
        
        self.setStyleSheet(f"""
            QTableWidget {{
                gridline-color: {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 13px;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 8px;
                alternate-background-color: {ModernStyle.COLORS['bg_secondary']};
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
                text-align: center;
            }}
            
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            
            /* 체크박스 스타일 - 파워링크 이전기록과 동일 */
            QTableWidget::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: white;
                margin: 2px;
            }}
            
            QTableWidget::indicator:checked {{
                background-color: {ModernStyle.COLORS['primary']};
                border-color: {ModernStyle.COLORS['primary']};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
            
            QTableWidget::indicator:hover {{
                border-color: #999999;
                background-color: #f8f9fa;
            }}
            
            QTableWidget::indicator:checked:hover {{
                background-color: #0056b3;
                border-color: #0056b3;
            }}
            
            
            /* 헤더 스타일 - 키워드분석기와 동일한 테두리 적용 */
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: 8px;
                border: none;
                border-right: 1px solid {ModernStyle.COLORS['border']};
                border-bottom: 2px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
                font-size: 13px;
            }}
            
            {first_header_style}
            
            /* 정렬 인디케이터 숨기기 (첫 번째 컬럼용) */
            QHeaderView::up-arrow, QHeaderView::down-arrow {{
                width: 0px;
                height: 0px;
            }}
        """)
        
        # 체크박스가 있는 경우 첫 번째 컬럼 너비 고정
        if self.has_checkboxes and column_width_setting:
            self.horizontalHeader().resizeSection(0, 50)
    
    def setup_header_checkbox(self):
        """헤더 체크박스 설정 (실제 체크박스 위젯 - 개별 체크박스와 완전 동일)"""
        if not self.has_checkboxes or not self.has_header_checkbox:
            return
            
        # 실제 체크박스 위젯 생성 (개별 체크박스와 동일한 스타일)
        self.header_checkbox = QCheckBox()
        self.header_checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #ccc;
                border-radius: 3px;
                background-color: white;
                margin: 2px;
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {ModernStyle.COLORS['primary']};
                border-color: {ModernStyle.COLORS['primary']};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }}
            
            QCheckBox::indicator:hover {{
                border-color: #999999;
                background-color: #f8f9fa;
            }}
            
            QCheckBox::indicator:checked:hover {{
                background-color: #0056b3;
                border-color: #0056b3;
            }}
        """)
        
        # 첫 번째 컬럼 헤더를 빈 문자열로 설정
        self.setHorizontalHeaderItem(0, QTableWidgetItem(""))
        
        # 헤더 뷰에서 첫 번째 섹션에 위젯 설정
        # Qt의 QHeaderView는 직접 위젯을 설정할 수 없으므로 커스텀 헤더 뷰 사용
        from PySide6.QtWidgets import QHeaderView
        
        # 헤더에 체크박스 위젯을 오버레이로 배치
        self.header_checkbox.setParent(self.horizontalHeader())
        self.header_checkbox.move(11, 8)  # x좌표 11로 조정
        # 마우스 이벤트 통과 설정 (개별 체크박스와 간섭 방지)
        self.header_checkbox.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.header_checkbox.show()
        
        # 헤더 클릭으로만 체크박스 제어 (직접 클릭 방지)
        
        # 헤더 클릭 시 체크박스 토글
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
    
    def setup_signals(self):
        """시그널 연결"""
        if self.has_checkboxes:
            self.itemChanged.connect(self.on_item_changed)
    
    def add_row_with_data(self, data: List[Any], checkable: bool = True) -> int:
        """
        데이터로 행 추가
        
        Args:
            data: 컬럼별 데이터 리스트 [키워드, 검색량, 클릭수, ...]
            checkable: 체크박스 활성화 여부
            
        Returns:
            추가된 행 번호
        """
        row = self.rowCount()
        self.insertRow(row)
        
        # 체크박스 컬럼 (첫 번째 컬럼)
        if self.has_checkboxes:
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Unchecked)
            if checkable:
                checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            else:
                checkbox_item.setFlags(Qt.ItemIsEnabled)
            self.setItem(row, 0, checkbox_item)
            
            # 데이터는 1번 컬럼부터 시작
            data_start_col = 1
        else:
            data_start_col = 0
        
        # 데이터 컬럼들
        for col, value in enumerate(data):
            if col + data_start_col >= self.columnCount():
                break
                
            if isinstance(value, (int, float)):
                # 숫자 데이터는 정렬 가능한 아이템 사용
                if isinstance(value, float):
                    display_text = f"{value:.2f}"
                else:
                    display_text = f"{value:,}"
                item = SortableTableWidgetItem(display_text, value)
            else:
                # 문자열 데이터
                item = QTableWidgetItem(str(value))
            
            self.setItem(row, col + data_start_col, item)
        
        return row
    
    def get_checked_rows(self) -> List[int]:
        """체크된 행 번호 리스트 반환"""
        if not self.has_checkboxes:
            return []
            
        checked_rows = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                checked_rows.append(row)
        return checked_rows
    
    def get_checked_data(self, data_column: int = 1) -> List[Any]:
        """체크된 행의 특정 컬럼 데이터 반환"""
        checked_data = []
        for row in self.get_checked_rows():
            item = self.item(row, data_column)
            if item:
                checked_data.append(item.text())
        return checked_data
    
    def set_all_checked(self, checked: bool):
        """모든 행 체크 상태 설정"""
        if not self.has_checkboxes:
            return
            
        # 시그널 중복 방지 (헤더 업데이트만 막고 selection_changed는 허용)
        self._updating_header = True
        
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        
        self._updating_header = False
        
        # 전체 선택/해제 후 selection_changed 시그널 발송
        self.selection_changed.emit()
    
    def update_header_checkbox_state(self):
        """헤더 체크박스 상태 업데이트 (최적화된 버전)"""
        if not self.has_checkboxes or not self.has_header_checkbox or not self.header_checkbox:
            return
            
        total_count = self.rowCount()
        if total_count == 0:
            self.header_checkbox.setCheckState(Qt.Unchecked)
            return
            
        # 빠른 체크: 전체 스캔 대신 점진적 카운트
        checked_count = 0
        for row in range(total_count):
            item = self.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                checked_count += 1
                # 부분 선택 상태를 빨리 감지
                if checked_count > 0 and checked_count < total_count and row < total_count - 1:
                    # 아직 더 남은 행이 있고 이미 부분 선택인 경우
                    break
        
        # 체크박스 상태 결정 (최적화)
        if checked_count == 0:
            self.header_checkbox.setCheckState(Qt.Unchecked)
        elif checked_count == total_count:
            self.header_checkbox.setCheckState(Qt.Checked)
        else:
            self.header_checkbox.setCheckState(Qt.PartiallyChecked)
    
    def update_header_checkbox_text(self):
        """헤더 체크박스 텍스트 업데이트 (하위 호환성을 위한 메서드)"""
        # 새로운 체크박스 방식으로 리다이렉트
        self.update_header_checkbox_state()
    
    
    def on_header_clicked(self, logical_index):
        """헤더 클릭 시 처리 (첫 번째 컬럼은 체크박스, 나머지는 정렬)"""
        if logical_index == 0 and self.has_checkboxes and self.has_header_checkbox:
            # 첫 번째 컬럼 클릭 시 전체 선택/해제
            checked_count = len(self.get_checked_rows())
            total_count = self.rowCount()
            
            if total_count == 0:
                return
                
            # 모두 체크되어 있으면 해제, 아니면 전체 선택
            new_checked = not (checked_count == total_count)
            
            # 헤더 체크박스 상태 업데이트
            if self.header_checkbox:
                self.header_checkbox.setCheckState(Qt.Checked if new_checked else Qt.Unchecked)
            
            # 모든 개별 체크박스 상태 변경
            self.set_all_checked(new_checked)
            self.header_checked.emit(new_checked)
        else:
            # 다른 컬럼은 정렬 허용
            if logical_index > 0:  # 첫 번째 컬럼 제외
                self.sortByColumn(logical_index, self.horizontalHeader().sortIndicatorOrder())
    
    def on_item_changed(self, item):
        """아이템 변경 처리 (체크박스 상태 변경)"""
        if item.column() == 0 and not self._updating_header:  # 체크박스 컬럼만 처리
            self.update_header_checkbox_state()
            self.selection_changed.emit()
    
    def clear_table(self):
        """테이블 모든 데이터 클리어"""
        self.setRowCount(0)
        # 헤더 체크박스 상태 업데이트
        self.update_header_checkbox_state()
    
    def get_selected_count(self) -> int:
        """선택된 행 개수 반환"""
        return len(self.get_checked_rows())
    
    def has_selection(self) -> bool:
        """선택된 행이 있는지 확인"""
        return self.get_selected_count() > 0


class ModernTableContainer(QWidget):
    """
    ModernTableWidget를 포함하는 컨테이너
    테이블 + 하단 버튼들을 포함하는 완전한 UI 블록
    """
    
    def __init__(self, 
                 title: str,
                 columns: List[str],
                 has_checkboxes: bool = True,
                 has_header_checkbox: bool = True,
                 parent=None):
        """
        ModernTableContainer 초기화
        
        Args:
            title: 테이블 제목
            columns: 컬럼 헤더 리스트
            has_checkboxes: 체크박스 포함 여부
            has_header_checkbox: 헤더 체크박스 포함 여부
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.title = title
        self.table = ModernTableWidget(columns, has_checkboxes, has_header_checkbox)
        self.setup_ui()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 제목
        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 16px;
                    font-weight: 700;
                    color: {ModernStyle.COLORS['text_primary']};
                    padding: 5px 0;
                }}
            """)
            layout.addWidget(title_label)
        
        # 테이블
        layout.addWidget(self.table)
        
        # 하단 버튼 영역 (서브클래스에서 오버라이드)
        button_layout = self.create_button_layout()
        if button_layout:
            layout.addLayout(button_layout)
    
    def create_button_layout(self) -> Optional[QHBoxLayout]:
        """하단 버튼 레이아웃 생성 (서브클래스에서 오버라이드)"""
        return None