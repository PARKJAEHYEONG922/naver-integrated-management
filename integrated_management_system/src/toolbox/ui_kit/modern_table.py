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
from . import tokens


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
        header.setDefaultSectionSize(100)  # 원본과 동일한 기본 크기
        header.setStretchLastSection(False)  # 🔧 FIX: 마지막 컬럼 늘어나지 않게 설정 (원본과 동일)
        header.setMinimumSectionSize(50)   # 원본과 동일한 최소 크기
        header.setMinimumHeight(40)  # 헤더 높이 40px
        header.setMaximumHeight(40)  # 헤더 높이 40px
        
        # 🔧 FIX: 모든 컬럼 너비 고정 (원본과 동일하게 설정)
        # 원본은 모든 컬럼이 고정된 너비를 가지고 있음
        header.setSectionResizeMode(QHeaderView.Fixed)  # 모든 컬럼 고정
        
        # 체크박스가 있는 경우에만 첫 번째 컬럼 특별 처리
        if self.has_checkboxes:
            # 체크박스 컬럼은 이미 Fixed 모드로 설정됨
            pass
        
        # 행 설정 (파워링크 이전기록과 동일)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(False)  # 정렬 비활성화 - 최신이 맨 위에 오도록
        
        # 편집 비활성화 (공용 설정)
        self.setEditTriggers(QTableWidget.NoEditTriggers)  # 편집 비활성화
        
        # 포커스 정책 설정 - 모든 경우에 포커스 표시 제거
        self.setFocusPolicy(Qt.NoFocus)  # 포커스 비활성화 (점선 테두리 제거)
        
        # 체크박스가 없는 경우 선택도 비활성화
        if not self.has_checkboxes:
            self.setSelectionMode(QTableWidget.NoSelection)  # 선택도 비활성화
        
        # 행 높이 35px
        self.verticalHeader().setDefaultSectionSize(35)
        
        # 헤더 체크박스 설정
        if self.has_checkboxes and self.has_header_checkbox:
            self.setup_header_checkbox()
            
        # 모든 정렬 기능 완전 비활성화
        self.horizontalHeader().setSortIndicatorShown(False)
        self.horizontalHeader().setSectionsClickable(self.has_checkboxes and self.has_header_checkbox)  # 체크박스가 있을 때만 클릭 가능
    
    def setup_styling(self):
        """파워링크 이전기록 테이블 스타일 기준으로 완전 통일"""
        # 체크박스 유무에 따른 첫 번째 헤더 스타일 조건부 적용
        if self.has_checkboxes:
            first_header_style = f"""
            /* 첫 번째 컬럼 (체크박스 컬럼) - 체크박스가 있는 경우 */
            QHeaderView::section:first {{
                font-size: {tokens.get_font_size('large')}px;
                color: {tokens.COLOR_TEXT_SECONDARY};
                font-weight: bold;
                text-align: center;
            }}
            """
        else:
            first_header_style = f"""
            /* 첫 번째 컬럼 (일반 컬럼) - 체크박스가 없는 경우 */
            QHeaderView::section:first {{
                font-size: 12px;
                color: {ModernStyle.COLORS['text_primary']};
                font-weight: 600;
                text-align: center;
            }}
            """
        
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
            
            QTableWidget::item:focus {{
                outline: none;
                border: none;
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
                font-size: 12px;
            }}
            
            {first_header_style}
            
            /* 정렬 인디케이터 숨기기 (첫 번째 컬럼용) */
            QHeaderView::up-arrow, QHeaderView::down-arrow {{
                width: 0px;
                height: 0px;
            }}
        """)
        
        # 체크박스가 있는 경우 첫 번째 컬럼 너비 고정
        if self.has_checkboxes:
            self.horizontalHeader().resizeSection(0, 50)
    
    def setup_header_checkbox(self):
        """헤더 체크박스 설정 (실제 체크박스 위젯 - 개별 체크박스와 완전 동일)"""
        if not self.has_checkboxes or not self.has_header_checkbox:
            return
        
        # 🔧 FIX: 기존 헤더 체크박스 완전 정리 (원본 방식)
        if hasattr(self, 'header_checkbox') and self.header_checkbox:
            try:
                self.header_checkbox.setParent(None)
                self.header_checkbox.deleteLater()
                self.header_checkbox = None
            except:
                pass
        
        # 🔧 FIX: 시그널 연결 상태 초기화 (원본 방식)
        if hasattr(self, '_header_signal_connected') and self._header_signal_connected:
            try:
                self.horizontalHeader().sectionClicked.disconnect(self.on_header_clicked)
            except:
                pass
        self._header_signal_connected = False
            
        # 실제 체크박스 위젯 생성 (개별 체크박스와 동일한 스타일)
        self.header_checkbox = QCheckBox()
        self.header_checkbox.setFocusPolicy(Qt.NoFocus)  # 포커스 표시 제거
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
        
        # 헤더 클릭 시 체크박스 토글 (중복 연결 방지)
        if not self._header_signal_connected:
            self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
            self._header_signal_connected = True
    
    def setup_signals(self):
        """시그널 연결"""
        if self.has_checkboxes:
            self.itemChanged.connect(self.on_item_changed)
    
    def add_row_with_data(self, data: List[Any], checkable: bool = True, rank_columns: List[int] = None) -> int:
        """
        데이터로 행 추가
        
        Args:
            data: 컬럼별 데이터 리스트 [키워드, 검색량, 클릭수, ...]
            checkable: 체크박스 활성화 여부
            rank_columns: 순위 데이터 컬럼 인덱스 리스트 (0부터 시작, 체크박스 제외)
            
        Returns:
            추가된 행 번호
        """
        # 정렬 기능이 비활성화되어 있으므로 별도 처리 불필요
            
        # 새 행을 맨 위에 추가 (최신이 위에 오도록)
        row = 0
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
        rank_columns = rank_columns or []
        
        for col, value in enumerate(data):
            if col + data_start_col >= self.columnCount():
                break
                
            str_value = str(value)
            
            # 순위 컬럼인지 확인
            if col in rank_columns:
                # 순위 데이터 특수 처리
                item = SortableTableWidgetItem(str_value)
                from .sortable_items import set_rank_sort_data
                set_rank_sort_data(item, col + data_start_col, str_value)  # UserRole에 순위 정렬 데이터 설정
            elif isinstance(value, (int, float)):
                # 숫자 데이터는 정렬 가능한 아이템 사용
                if isinstance(value, float):
                    display_text = f"{value:.2f}"
                else:
                    display_text = f"{value:,}"
                item = SortableTableWidgetItem(display_text, value)
            else:
                # 문자열 데이터도 숫자/날짜 가능성 체크하여 정렬 가능한 아이템 사용
                try:
                    # 1. 날짜/시간 패턴 체크 먼저
                    datetime_value = self._extract_datetime_value(str_value)
                    if datetime_value is not None:
                        item = SortableTableWidgetItem(str_value, datetime_value)
                    else:
                        # 2. 단위가 붙은 숫자 추출 (1000원, 2위 등)
                        import re
                        number_match = re.search(r'[\d,]+\.?\d*', str_value)
                        if number_match:
                            number_str = number_match.group()
                            numeric_value = float(number_str.replace(',', ''))
                            item = SortableTableWidgetItem(str_value, numeric_value)
                        else:
                            # 숫자가 없으면 일반 아이템
                            item = SortableTableWidgetItem(str_value)
                except (ValueError, TypeError):
                    # 순수 문자열인 경우만 일반 아이템 사용
                    item = SortableTableWidgetItem(str_value)
            
            self.setItem(row, col + data_start_col, item)
            
            # 데이터 설정 직후 검증
            set_item = self.item(row, col + data_start_col)
            if not set_item or set_item.text() != str_value:
                # 재시도
                self.setItem(row, col + data_start_col, SortableTableWidgetItem(str_value))
        
        # 맨 위 행으로 스크롤 (새로 추가된 행이 보이도록)
        self.scrollToTop()
            
        # 테이블 강제 업데이트
        self.viewport().update()
        
        return row
    
    def _extract_datetime_value(self, text: str) -> float:
        """날짜/시간 문자열을 타임스탬프로 변환"""
        if not text:
            return None
            
        import re
        from datetime import datetime
        
        # 실제 사용되는 날짜/시간 패턴 (카페DB 추출에서 확인됨)
        patterns = [
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$',             # 2025-08-17 21:20 (실제 사용)
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$',       # 2025-08-17 21:20:30
            r'^\d{4}-\d{2}-\d{2}$',                            # 2025-08-17
            r'^\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}$',       # 2025-8-17 2:20 (0 패딩 없는 경우)
            r'^\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}$',             # 2025/08/17 21:20
            r'^\d{4}/\d{2}/\d{2}$',                            # 2025/08/17
        ]
        
        formats = [
            '%Y-%m-%d %H:%M',      # 가장 많이 사용되는 형식 (카페DB에서 확인)
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M',      # 0 패딩 없는 경우용
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.match(pattern, str(text).strip())
            if match:
                try:
                    dt = datetime.strptime(match.group(), formats[i])
                    # 타임스탬프로 변환 (1970년 1월 1일부터의 초)
                    return dt.timestamp()
                except ValueError:
                    continue
        
        # 백업: 더 간단한 날짜 패턴 시도
        simple_patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})', '%Y-%m-%d %H:%M'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
        ]
        
        for pattern, fmt in simple_patterns:
            match = re.search(pattern, str(text))
            if match:
                try:
                    dt = datetime.strptime(match.group(), fmt)
                    return dt.timestamp()
                except ValueError:
                    continue
        
        return None
    
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
    
    def add_dynamic_column(self, column_title: str, column_data: List[Any] = None, column_width: int = 100) -> int:
        """
        동적으로 새 컬럼 추가 (순위추적 등에서 사용)
        
        Args:
            column_title: 새 컬럼 제목
            column_data: 각 행에 넣을 데이터 리스트 (None이면 빈 값)
            column_width: 컬럼 너비
            
        Returns:
            추가된 컬럼 인덱스
        """
        # 새 컬럼 추가
        new_column_index = self.columnCount()
        self.insertColumn(new_column_index)
        
        # 헤더 설정
        self.setHorizontalHeaderItem(new_column_index, QTableWidgetItem(column_title))
        
        # 컬럼 너비 설정
        self.setColumnWidth(new_column_index, column_width)
        
        # 🔧 FIX: 새로 추가된 컬럼도 고정 너비로 설정 (원본과 동일)
        self.horizontalHeader().setSectionResizeMode(new_column_index, QHeaderView.Fixed)
        
        # 기존 행들에 데이터 추가
        if column_data:
            for row in range(min(self.rowCount(), len(column_data))):
                value = column_data[row]
                str_value = str(value) if value is not None else ""
                
                # 순위 데이터인지 체크 (숫자나 "-" 포함)
                if self._is_rank_data(str_value):
                    item = SortableTableWidgetItem(str_value)
                    from .sortable_items import set_rank_sort_data
                    set_rank_sort_data(item, 0, str_value)
                else:
                    item = SortableTableWidgetItem(str_value)
                
                self.setItem(row, new_column_index, item)
        else:
            # 빈 데이터로 채우기
            for row in range(self.rowCount()):
                item = SortableTableWidgetItem("")
                self.setItem(row, new_column_index, item)
        
        return new_column_index
    
    def insert_column_at_position(self, position: int, column_title: str, column_data: List[Any] = None, column_width: int = 100) -> bool:
        """
        특정 위치에 컬럼 삽입 (원본 순위추적과 동일한 로직)
        
        Args:
            position: 삽입할 위치 (0-based index)
            column_title: 새 컬럼 제목  
            column_data: 각 행에 넣을 데이터 리스트 (None이면 빈 값)
            column_width: 컬럼 너비
            
        Returns:
            삽입 성공 여부
        """
        if position < 0 or position > self.columnCount():
            return False
            
        try:
            # 1. 기존 모든 데이터 백업
            backup_data = []
            for row in range(self.rowCount()):
                row_data = []
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item:
                        row_data.append({
                            'text': item.text(),
                            'data': item.data(Qt.UserRole),
                            'checkState': item.checkState() if col == 0 and self.has_checkboxes else None
                        })
                    else:
                        row_data.append({'text': '', 'data': None, 'checkState': None})
                backup_data.append(row_data)
            
            # 2. 기존 헤더 백업
            old_headers = []
            for col in range(self.columnCount()):
                header_item = self.horizontalHeaderItem(col)
                old_headers.append(header_item.text() if header_item else "")
            
            # 3. 새 컬럼 추가 (맨 뒤에 임시로)
            self.insertColumn(self.columnCount())
            
            # 4. 새로운 헤더 순서 만들기 - position 위치에 새 헤더 삽입
            new_headers = []
            for i in range(self.columnCount()):
                if i < position:
                    # position 전까지는 기존 헤더
                    if i < len(old_headers):
                        new_headers.append(old_headers[i])
                    else:
                        new_headers.append("")
                elif i == position:
                    # position 위치에 새 헤더
                    new_headers.append(column_title)
                else:
                    # position 후는 기존 헤더를 한 칸씩 뒤로
                    original_index = i - 1
                    if original_index < len(old_headers):
                        new_headers.append(old_headers[original_index])
                    else:
                        new_headers.append("")
            
            # 5. 헤더 적용
            self.setHorizontalHeaderLabels(new_headers)
            
            # 6. 데이터 재배치 - position 위치에 새 데이터 삽입
            for row in range(len(backup_data)):
                row_backup = backup_data[row]
                
                for col in range(self.columnCount()):
                    if col < position:
                        # position 전까지는 기존 데이터
                        if col < len(row_backup):
                            self._restore_item(row, col, row_backup[col])
                    elif col == position:
                        # position 위치에 새 데이터
                        if column_data and row < len(column_data):
                            value = column_data[row]
                            str_value = str(value) if value is not None else ""
                            
                            if self._is_rank_data(str_value):
                                item = SortableTableWidgetItem(str_value)
                                from .sortable_items import set_rank_sort_data
                                set_rank_sort_data(item, 0, str_value)
                            else:
                                item = SortableTableWidgetItem(str_value)
                        else:
                            item = SortableTableWidgetItem("")
                        
                        self.setItem(row, col, item)
                    else:
                        # position 후는 기존 데이터를 한 칸씩 뒤로
                        original_col = col - 1
                        if original_col < len(row_backup):
                            self._restore_item(row, col, row_backup[original_col])
            
            # 7. 새 컬럼 너비 설정
            self.setColumnWidth(position, column_width)
            self.horizontalHeader().setSectionResizeMode(position, QHeaderView.Fixed)
            
            return True
            
        except Exception as e:
            # 오류 시 원복은 너무 복잡하므로 로그만 남김
            from src.foundation.logging import get_logger
            logger = get_logger("toolbox.modern_table")
            logger.error(f"컬럼 삽입 실패: position={position}, title={column_title}: {e}")
            return False
    
    def _restore_item(self, row: int, col: int, backup_item: dict):
        """백업된 아이템 복원"""
        if self._is_rank_data(backup_item['text']):
            item = SortableTableWidgetItem(backup_item['text'])
            from .sortable_items import set_rank_sort_data
            set_rank_sort_data(item, 0, backup_item['text'])
        else:
            item = SortableTableWidgetItem(backup_item['text'])
        
        if backup_item['data'] is not None:
            item.setData(Qt.UserRole, backup_item['data'])
            
        if backup_item['checkState'] is not None and col == 0 and self.has_checkboxes:
            item.setCheckState(backup_item['checkState'])
            
        self.setItem(row, col, item)
    
    def _is_rank_data(self, value: str) -> bool:
        """값이 순위 데이터인지 판단"""
        if not value or value == "-":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def remove_column_by_title(self, column_title: str) -> bool:
        """
        컬럼 제목으로 컬럼 삭제
        
        Args:
            column_title: 삭제할 컬럼 제목
            
        Returns:
            삭제 성공 여부
        """
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item and header_item.text() == column_title:
                self.removeColumn(col)
                return True
        return False
    
    def get_column_titles(self) -> List[str]:
        """모든 컬럼 제목 리스트 반환"""
        titles = []
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                titles.append(header_item.text())
            else:
                titles.append("")
        return titles
    
    def update_column_data(self, column_index: int, column_data: List[Any]):
        """
        특정 컬럼의 모든 데이터 업데이트
        
        Args:
            column_index: 컬럼 인덱스
            column_data: 새 데이터 리스트
        """
        if column_index >= self.columnCount():
            return
            
        for row in range(min(self.rowCount(), len(column_data))):
            value = column_data[row]
            str_value = str(value) if value is not None else ""
            
            # 순위 데이터인지 체크
            if self._is_rank_data(str_value):
                item = SortableTableWidgetItem(str_value)
                from .sortable_items import set_rank_sort_data
                set_rank_sort_data(item, 0, str_value)
            else:
                item = SortableTableWidgetItem(str_value)
            
            self.setItem(row, column_index, item)
    
    def has_checked_items(self) -> bool:
        """체크된 아이템이 있는지 확인"""
        if not self.has_checkboxes:
            return False
            
        for row in range(self.rowCount()):
            checkbox_item = self.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                return True
        return False
    
    def is_row_checked(self, row: int) -> bool:
        """특정 행이 체크되어 있는지 확인"""
        if not self.has_checkboxes or row >= self.rowCount():
            return False
            
        checkbox_item = self.item(row, 0)
        return checkbox_item and checkbox_item.checkState() == Qt.Checked
    
    def get_checked_rows(self) -> List[int]:
        """체크된 행의 인덱스 리스트 반환"""
        checked_rows = []
        if not self.has_checkboxes:
            return checked_rows
            
        for row in range(self.rowCount()):
            if self.is_row_checked(row):
                checked_rows.append(row)
                
        return checked_rows
    
    def set_row_checked(self, row: int, checked: bool):
        """특정 행의 체크 상태 설정"""
        if not self.has_checkboxes or row >= self.rowCount():
            return
            
        checkbox_item = self.item(row, 0)
        if checkbox_item:
            checkbox_item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
    
    def check_all_rows(self, checked: bool):
        """모든 행의 체크 상태 설정"""
        if not self.has_checkboxes:
            return
            
        for row in range(self.rowCount()):
            self.set_row_checked(row, checked)


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