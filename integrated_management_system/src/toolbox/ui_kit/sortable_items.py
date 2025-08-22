"""
정렬 가능한 테이블/트리 위젯 아이템들
모든 모듈에서 재사용 가능한 공용 정렬 기능
"""
from PySide6.QtWidgets import QTreeWidgetItem, QTableWidgetItem
from PySide6.QtCore import Qt
from src.foundation.logging import get_logger

logger = get_logger("toolbox.ui_kit.sortable_items")


class SortableTreeWidgetItem(QTreeWidgetItem):
    """정렬 가능한 트리 위젯 아이템 (공용 버전)"""
    
    def __init__(self, strings: list):
        super().__init__(strings)
    
    def __lt__(self, other):
        """정렬 시 Qt.UserRole 데이터를 사용하여 비교"""
        column = self.treeWidget().sortColumn()
        
        # 내 데이터와 다른 아이템의 데이터 가져오기
        my_data = self.data(column, Qt.UserRole)
        other_data = other.data(column, Qt.UserRole)
        
        # UserRole 데이터가 있으면 그것으로 정렬
        if my_data is not None and other_data is not None:
            try:
                # 숫자로 비교 (정렬용 데이터)
                return float(my_data) < float(other_data)
            except (ValueError, TypeError):
                # 숫자가 아니면 문자열로 비교
                return str(my_data) < str(other_data)
        
        # UserRole 데이터가 없으면 기본 텍스트로 정렬
        my_text = self.text(column)
        other_text = other.text(column)
        
        # 숫자 문자열 처리 (1,234 같은 형식)
        try:
            my_num = float(my_text.replace(',', '').replace('-', '0'))
            other_num = float(other_text.replace(',', '').replace('-', '0'))
            return my_num < other_num
        except (ValueError, TypeError):
            return my_text < other_text


class SortableTableWidgetItem(QTableWidgetItem):
    """정렬 가능한 테이블 위젯 아이템 (공용 버전)"""
    
    def __init__(self, text: str, sort_value=None):
        super().__init__(text)
        if sort_value is not None:
            self.setData(Qt.UserRole, sort_value)
    
    def __lt__(self, other):
        """정렬 시 UserRole 데이터를 사용하여 비교"""
        # 타입 체크 - 다른 타입이면 텍스트 비교
        if not isinstance(other, QTableWidgetItem):
            return str(self.text()) < str(other)
        
        my_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole)
        
        # UserRole 데이터가 있으면 그것으로 정렬
        if my_data is not None and other_data is not None:
            try:
                # 숫자로 비교
                return float(my_data) < float(other_data)
            except (ValueError, TypeError):
                # 숫자가 아니면 문자열로 비교
                return str(my_data) < str(other_data)
        
        # UserRole 데이터가 없으면 텍스트로 정렬 (재귀 방지)
        my_text = self.text() or ""
        other_text = other.text() or ""
        
        # 숫자 문자열 처리 시도 (단위 제거 포함)
        try:
            my_num = self._extract_number(my_text)
            other_num = self._extract_number(other_text)
            return my_num < other_num
        except (ValueError, TypeError):
            return my_text < other_text
    
    def _extract_number(self, text: str) -> float:
        """텍스트에서 숫자 추출 (단위 제거) 또는 날짜/시간을 타임스탬프로 변환"""
        if not text:
            return 0.0
        
        # 날짜/시간 패턴 체크 먼저
        datetime_value = self._extract_datetime(text)
        if datetime_value is not None:
            return datetime_value
            
        # 단위 제거 (원, 위, %, 개, 명 등)
        import re
        # 숫자와 쉼표, 소수점만 추출
        number_match = re.search(r'[\d,]+\.?\d*', str(text))
        if number_match:
            number_str = number_match.group()
            # 쉼표 제거하고 숫자 변환
            return float(number_str.replace(',', ''))
        else:
            # 숫자가 없으면 0 반환
            return 0.0
    
    def _extract_datetime(self, text: str) -> float:
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


# 편의 함수들
def create_sortable_tree_item(strings: list) -> SortableTreeWidgetItem:
    """정렬 가능한 트리 아이템 생성 편의 함수"""
    return SortableTreeWidgetItem(strings)


def create_sortable_table_item(text: str, sort_value=None) -> SortableTableWidgetItem:
    """정렬 가능한 테이블 아이템 생성 편의 함수"""
    return SortableTableWidgetItem(text, sort_value)


def set_numeric_sort_data(item, column: int, value):
    """숫자 정렬 데이터 설정 편의 함수"""
    try:
        # 숫자 변환 시도
        if isinstance(value, str):
            # 쉼표 제거하고 숫자 변환
            numeric_value = float(value.replace(',', '').replace('-', '0'))
        else:
            numeric_value = float(value)
        
        item.setData(column, Qt.UserRole, numeric_value)
    except (ValueError, TypeError):
        # 숫자가 아니면 문자열로 저장
        item.setData(column, Qt.UserRole, str(value))


def set_rank_sort_data(item, column: int, rank_text: str):
    """순위 정렬 데이터 설정 편의 함수 (순위 전용)"""
    import re
    
    try:
        if rank_text == "-" or not rank_text.strip():
            # "-" 또는 빈 값은 가장 뒤로 정렬
            item.setData(Qt.UserRole, 999)
        elif "200위밖" in rank_text or "200+" in rank_text:
            # "200위밖" 형태는 201로 처리
            item.setData(Qt.UserRole, 201)
        elif rank_text.startswith("100+"):
            # "100+" 형태는 201로 처리
            item.setData(Qt.UserRole, 201)
        elif rank_text == "순위권 밖":
            # "순위권 밖"은 202로 처리
            item.setData(Qt.UserRole, 202)
        else:
            # 숫자 추출 (예: "1위" -> 1, "10위" -> 10)
            numbers = re.findall(r'\d+', rank_text)
            if numbers:
                rank_num = int(numbers[0])
                item.setData(Qt.UserRole, rank_num)
            else:
                # 숫자를 찾을 수 없으면 가장 뒤로
                item.setData(Qt.UserRole, 999)
    except (ValueError, TypeError):
        # 파싱 실패 시 가장 뒤로
        item.setData(Qt.UserRole, 999)