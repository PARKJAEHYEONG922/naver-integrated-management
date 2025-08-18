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
        
        # UserRole 데이터가 없으면 기본 텍스트로 정렬
        return super().__lt__(other)


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
    try:
        if rank_text == "-" or not rank_text.strip():
            # "-" 또는 빈 값은 가장 뒤로 정렬
            item.setData(column, Qt.UserRole, 999)
        elif rank_text.startswith("100+"):
            # "100+" 형태는 201로 처리
            item.setData(column, Qt.UserRole, 201)
        elif rank_text == "순위권 밖":
            # "순위권 밖"은 202로 처리
            item.setData(column, Qt.UserRole, 202)
        else:
            # 일반 숫자 순위
            rank_num = int(rank_text)
            item.setData(column, Qt.UserRole, rank_num)
    except (ValueError, TypeError):
        # 파싱 실패 시 가장 뒤로
        item.setData(column, Qt.UserRole, 999)