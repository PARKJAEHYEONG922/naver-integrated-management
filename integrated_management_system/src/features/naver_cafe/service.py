"""
네이버 카페 DB 추출기 서비스
비즈니스 로직과 오케스트레이션 담당
CLAUDE.md 구조 준수: 오케스트레이션(흐름), adapters 경유, DB/엑셀 트리거
"""
from typing import List, Dict
from datetime import datetime
from pathlib import Path

from src.foundation.logging import get_logger
from src.toolbox.validators import validate_url
from .models import (
    CafeInfo, BoardInfo, ExtractedUser, ExtractionTask, ExtractionStatus,
    cafe_extraction_db
)
from .adapters import NaverCafeDataAdapter

logger = get_logger("features.naver_cafe.service")


class NaverCafeExtractionService:
    """네이버 카페 추출 서비스"""
    
    def __init__(self):
        self.adapter = NaverCafeDataAdapter()
        # 추출 관련 변수는 worker.py에서 관리
        
    # set_callbacks 메서드 제거 - worker.py에서 직접 처리
    
    async def search_cafes(self, query: str, browser_context=None) -> List[CafeInfo]:
        """카페 검색 - 비즈니스 로직 (입력 검증 → adapters 호출 → 로깅)"""
        try:
            logger.info(f"카페 검색 시작: {query}")
            
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not query or not query.strip():
                raise ValueError("검색어가 비어있습니다")
            
            # URL인 경우 추가 검증
            if "cafe.naver.com" in query:
                if not validate_url(query):
                    raise ValueError("올바르지 않은 카페 URL입니다")
            
            # 2. adapters 경유 (CLAUDE.md: 벤더 호출은 반드시 adapters 경유)
            cafes = await self.adapter.search_cafes_by_name(query, browser_context)
            
            # 3. 결과 검증 및 로깅
            logger.info(f"카페 검색 완료: {len(cafes)}개 발견")
            return cafes
                
        except Exception as e:
            logger.error(f"카페 검색 실패: {e}")
            return []
    
    async def get_boards_for_cafe(self, cafe_info: CafeInfo, browser_context=None) -> List[BoardInfo]:
        """게시판 목록 조회 - 비즈니스 로직 (검증 → adapters 호출 → 로깅)"""
        try:
            logger.info(f"게시판 목록 조회 시작: {cafe_info.name}")
            
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not cafe_info or not cafe_info.url:
                raise ValueError("올바르지 않은 카페 정보입니다")
            
            # 2. adapters 경유 (CLAUDE.md: 벤더 호출은 반드시 adapters 경유)
            boards = await self.adapter.get_cafe_boards(cafe_info, browser_context)
            
            # 3. 결과 검증 및 로깅
            logger.info(f"게시판 목록 조회 완료: {len(boards)}개 발견")
            return boards
            
        except Exception as e:
            logger.error(f"게시판 목록 조회 실패: {e}")
            return []
    
    
    def get_extraction_history(self) -> List[ExtractionTask]:
        """추출 기록 조회 - DB 조회는 foundation/db 경유"""
        try:
            from src.foundation.db import get_db
            from .models import CafeExtractionRepository
            
            # 1. foundation/db 경유로 데이터 조회
            task_dicts = get_db().get_cafe_extraction_tasks()
            
            # 2. models의 헬퍼로 DTO 변환
            tasks = []
            for task_dict in task_dicts:
                try:
                    task = CafeExtractionRepository.dict_to_task(task_dict)
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"추출 기록 변환 실패: {e}")
                    continue
            
            return tasks
            
        except Exception as e:
            logger.error(f"추출 기록 조회 실패: {e}")
            return []
    
    def get_extracted_users(self) -> List[ExtractedUser]:
        """추출된 사용자 목록 조회 - 메모리 기반"""
        return cafe_extraction_db.get_all_users()
    
    def get_users_by_task_id(self, task_id: str) -> List[ExtractedUser]:
        """특정 작업 ID의 사용자 목록 조회 - Foundation DB 기반"""
        try:
            from src.foundation.db import get_db
            
            # Foundation DB에서 추출 결과 조회
            db = get_db()
            user_dicts = db.get_cafe_extraction_results(task_id)
            
            # Dict를 ExtractedUser 객체로 변환
            users = []
            for user_dict in user_dicts:
                try:
                    user = ExtractedUser(
                        user_id=user_dict['user_id'],
                        nickname=user_dict['nickname'],
                        article_count=user_dict.get('article_count', 1),
                        first_seen=datetime.fromisoformat(user_dict['first_seen']) if user_dict.get('first_seen') else datetime.now(),
                        last_seen=datetime.fromisoformat(user_dict['last_seen']) if user_dict.get('last_seen') else datetime.now()
                    )
                    users.append(user)
                except Exception as e:
                    logger.warning(f"사용자 데이터 변환 실패: {e}")
                    continue
            
            logger.debug(f"Task {task_id} 사용자 조회: {len(users)}명")
            return users
            
        except Exception as e:
            logger.error(f"Task {task_id} 사용자 조회 실패: {e}")
            # 폴백: 메모리 기반 조회
            return cafe_extraction_db.get_users_by_task_id(task_id)
    
    def save_extraction_task(self, task: ExtractionTask):
        """추출 작업 기록 저장 - DB 저장은 foundation/db 경유"""
        try:
            from src.foundation.db import get_db
            from .models import CafeExtractionRepository
            
            # 1. models 헬퍼로 DTO 변환
            task_data = CafeExtractionRepository.task_to_dict(task)
            
            # 2. foundation/db 경유로 저장
            get_db().add_cafe_extraction_task(task_data)
            
            logger.info(f"추출 작업 기록 저장 완료: {task.task_id}")
            
        except Exception as e:
            logger.error(f"추출 작업 기록 저장 실패: {e}")
    
    def delete_extraction_task(self, task_id: str):
        """특정 추출 작업 기록 삭제 - DB 삭제는 foundation/db 경유"""
        try:
            from src.foundation.db import get_db
            
            # foundation/db 경유로 삭제
            get_db().delete_cafe_extraction_task(task_id)
            
            logger.info(f"추출 작업 기록 삭제 완료: {task_id}")
            
        except Exception as e:
            logger.error(f"추출 작업 기록 삭제 실패: {e}")
    
    def clear_all_data(self):
        """모든 데이터 초기화 - 메모리만 초기화"""
        cafe_extraction_db.clear_all()
        logger.info("모든 추출 데이터 초기화 완료 (메모리만)")
    
    def export_to_excel(self, file_path: str, users: List[ExtractedUser]) -> bool:
        """엑셀로 내보내기 - service에서 오케스트레이션, 실제 파일 I/O는 adapters"""
        try:
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not file_path or not file_path.strip():
                raise ValueError("파일 경로가 비어있습니다")
            
            if not users:
                raise ValueError("내보낼 사용자 데이터가 없습니다")
            
            # 2. adapters로 실제 파일 I/O 위임 (CLAUDE.md: 파일 I/O는 adapters)
            success = self.adapter.export_users_to_excel(file_path, users)
            
            # 3. 결과 로깅
            if success:
                logger.info(f"엑셀 내보내기 성공: {file_path} ({len(users)}명)")
            else:
                logger.error(f"엑셀 내보내기 실패: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"엑셀 내보내기 실패: {e}")
            return False
    
    def export_to_meta_csv(self, file_path: str, users: List[ExtractedUser]) -> bool:
        """Meta CSV로 내보내기 - service에서 오케스트레이션, 실제 파일 I/O는 adapters"""
        try:
            # 1. 입력 검증 (CLAUDE.md: service가 검증 담당)
            if not file_path or not file_path.strip():
                raise ValueError("파일 경로가 비어있습니다")
            
            if not users:
                raise ValueError("내보낼 사용자 데이터가 없습니다")
            
            # 2. adapters로 실제 파일 I/O 위임 (CLAUDE.md: 파일 I/O는 adapters)
            success = self.adapter.export_users_to_meta_csv(file_path, users)
            
            # 3. 결과 로깅
            if success:
                logger.info(f"Meta CSV 내보내기 성공: {file_path} ({len(users)}명)")
            else:
                logger.error(f"Meta CSV 내보내기 실패: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Meta CSV 내보내기 실패: {e}")
            return False
    
    
    def add_extracted_user(self, user: ExtractedUser):
        """개별 사용자 추출 시 메모리 데이터베이스에 추가"""
        try:
            cafe_extraction_db.add_user(user)
            logger.debug(f"사용자 추가: {user.user_id}")
        except Exception as e:
            logger.error(f"사용자 추가 실패: {e}")
    
    def save_extraction_result(self, result, unified_worker=None):
        """추출 완료 시 결과 저장 - foundation/db 경유"""
        try:
            from src.foundation.db import get_db
            from .models import CafeExtractionRepository
            
            # 1. 입력 검증
            if not result or not hasattr(result, 'task_id'):
                logger.warning("추출 기록 저장 실패: 결과 객체가 없습니다")
                return False
            
            # 2. 워커에서 카페/게시판 정보 가져오기
            if not unified_worker or not hasattr(unified_worker, 'selected_cafe') or not hasattr(unified_worker, 'selected_board'):
                logger.warning("추출 기록 저장 실패: 워커에서 카페/게시판 정보가 없습니다")
                return False
                
            selected_cafe = unified_worker.selected_cafe
            selected_board = unified_worker.selected_board
            
            if not selected_cafe or not selected_board:
                logger.warning("추출 기록 저장 실패: 카페/게시판이 설정되지 않았습니다")
                return False
            
            # 3. 데이터 변환
            task_data = {
                'task_id': result.task_id,
                'cafe_name': selected_cafe.name,
                'cafe_url': selected_cafe.url,
                'board_name': selected_board.name,
                'board_url': selected_board.url,
                'start_page': unified_worker.start_page,
                'end_page': unified_worker.end_page,
                'status': ExtractionStatus.COMPLETED.value,
                'current_page': unified_worker.end_page,
                'total_extracted': result.total_users,
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
                'error_message': None
            }
            
            # 4. foundation/db 경유로 저장
            get_db().add_cafe_extraction_task(task_data)
            
            logger.info(f"추출 기록 저장 완료: {selected_cafe.name} > {selected_board.name}")
            return True
            
        except Exception as e:
            logger.error(f"추출 기록 저장 실패: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """추출 통계 조회"""
        history = self.get_extraction_history()
        users = self.get_extracted_users()
        
        total_tasks = len(history)
        completed_tasks = len([task for task in history if task.status == ExtractionStatus.COMPLETED])
        failed_tasks = len([task for task in history if task.status == ExtractionStatus.FAILED])
        
        total_users = len(users)
        unique_users = len(set(user.user_id for user in users))
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_users": total_users,
            "unique_users": unique_users
        }
    
    def export_to_excel_with_dialog(self, users_data: List[List[str]], parent_widget=None) -> bool:
        """파일 대화상자를 포함한 엑셀 내보내기 - UI 오케스트레이션"""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            
            # 1. 입력 검증
            if not users_data:
                if parent_widget:
                    QMessageBox.information(parent_widget, "정보", "내보낼 데이터가 없습니다.")
                return False
            
            # 2. 파일 선택 대화상자
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "저장할 파일명을 입력하세요",
                f"네이버카페_추출결과_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel files (*.xlsx)"
            )
            
            if not file_path:
                return False
            
            # 3. 사용자 데이터를 ExtractedUser 객체로 변환
            users = []
            for row_data in users_data:
                if len(row_data) >= 4:
                    user = ExtractedUser(
                        user_id=row_data[1],
                        nickname=row_data[2],
                        last_seen=datetime.strptime(row_data[3], "%Y-%m-%d %H:%M:%S") if row_data[3] else datetime.now()
                    )
                    users.append(user)
            
            # 4. adapters 경유로 실제 파일 저장
            success = self.adapter.export_users_to_excel(file_path, users)
            
            if success:
                # 5. 성공 다이얼로그 표시
                filename = Path(file_path).name
                self._show_save_completion_dialog(
                    parent_widget,
                    "저장 완료",
                    f"카페 추출 데이터가 성공적으로 Excel 파일로 저장되었습니다.\n\n파일명: {filename}\n사용자 수: {len(users_data)}명",
                    file_path
                )
                logger.info(f"Excel 파일 저장 완료: {filename}")
            else:
                if parent_widget:
                    QMessageBox.critical(parent_widget, "오류", "엑셀 저장 중 오류가 발생했습니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"엑셀 내보내기 (대화상자 포함) 실패: {e}")
            if parent_widget:
                QMessageBox.critical(parent_widget, "오류", f"엑셀 저장 중 오류가 발생했습니다.\n{str(e)}")
            return False
    
    def export_to_meta_csv_with_dialog(self, users_data: List[List[str]], parent_widget=None) -> bool:
        """파일 대화상자를 포함한 Meta CSV 내보내기 - UI 오케스트레이션"""
        try:
            from PySide6.QtWidgets import QFileDialog, QMessageBox
            
            # 1. 입력 검증
            if not users_data:
                if parent_widget:
                    QMessageBox.information(parent_widget, "정보", "내보낼 데이터가 없습니다.")
                return False
            
            # 2. 파일 선택 대화상자
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Meta CSV 파일 저장",
                f"네이버카페_Meta_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "CSV files (*.csv)"
            )
            
            if not file_path:
                return False
            
            # 3. 사용자 데이터를 ExtractedUser 객체로 변환
            users = []
            for row_data in users_data:
                if len(row_data) >= 4:
                    user = ExtractedUser(
                        user_id=row_data[1],
                        nickname=row_data[2],
                        last_seen=datetime.strptime(row_data[3], "%Y-%m-%d %H:%M:%S") if row_data[3] else datetime.now()
                    )
                    users.append(user)
            
            # 4. adapters 경유로 실제 파일 저장
            success = self.adapter.export_users_to_meta_csv(file_path, users)
            
            if success:
                # 5. 성공 다이얼로그 표시
                filename = Path(file_path).name
                user_count = len([row_data for row_data in users_data if len(row_data) >= 2])
                self._show_save_completion_dialog(
                    parent_widget,
                    "Meta CSV 저장 완료",
                    f"Meta 광고용 CSV 파일이 성공적으로 저장되었습니다.\n\n파일명: {filename}\n사용자 ID: {user_count}개\n생성된 이메일: {user_count*3}개\n(@naver.com, @gmail.com, @daum.net)",
                    file_path
                )
                logger.info(f"Meta CSV 파일 저장 완료: {filename} (사용자 {user_count}명)")
            else:
                if parent_widget:
                    QMessageBox.critical(parent_widget, "오류", "CSV 저장 중 오류가 발생했습니다.")
            
            return success
            
        except Exception as e:
            logger.error(f"Meta CSV 내보내기 (대화상자 포함) 실패: {e}")
            if parent_widget:
                QMessageBox.critical(parent_widget, "오류", f"CSV 저장 중 오류가 발생했습니다.\n{str(e)}")
            return False
    
    def show_save_format_dialog_and_export(self, users_data: List[List[str]], parent_widget=None) -> bool:
        """저장 포맷 선택 다이얼로그를 표시하고 해당 포맷으로 내보내기 - 원본과 동일"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
            
            # 원본과 동일한 저장 방식 선택 다이얼로그
            dialog = QDialog(parent_widget)
            dialog.setWindowTitle("저장 방식 선택")
            dialog.setFixedSize(600, 300)
            dialog.setModal(True)
            
            # 레이아웃
            layout = QVBoxLayout(dialog)
            layout.setSpacing(20)
            layout.setContentsMargins(30, 30, 30, 30)
            
            # 제목
            title_label = QLabel("선택된 기록의 저장 방식을 선택해주세요")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3748;")
            layout.addWidget(title_label)
            
            # 설명
            desc_label = QLabel(f"• Excel: 사용자ID, 닉네임 등 전체 정보\n• Meta CSV: 이메일 형태로 Meta 광고 활용 가능\n• 사용자: {len(users_data)}명")
            desc_label.setStyleSheet("font-size: 12px; color: #4a5568; line-height: 1.4;")
            layout.addWidget(desc_label)
            
            # 버튼 레이아웃
            button_layout = QHBoxLayout()
            button_layout.setSpacing(20)
            button_layout.setContentsMargins(20, 0, 20, 0)
            
            excel_button = QPushButton("📊 Excel 파일")
            excel_button.setStyleSheet("""
                QPushButton {
                    background-color: #3182ce;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #2c5aa0;
                }
            """)
            
            meta_button = QPushButton("📧 Meta CSV")
            meta_button.setStyleSheet("""
                QPushButton {
                    background-color: #e53e3e;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #c53030;
                }
            """)
            
            cancel_button = QPushButton("취소")
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #718096;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #4a5568;
                }
            """)
            
            button_layout.addWidget(excel_button)
            button_layout.addWidget(meta_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            # 결과 변수
            result = None
            
            def on_excel():
                nonlocal result
                result = "excel"
                dialog.accept()
            
            def on_meta():
                nonlocal result
                result = "meta_csv"
                dialog.accept()
            
            def on_cancel():
                nonlocal result
                result = None
                dialog.reject()
            
            excel_button.clicked.connect(on_excel)
            meta_button.clicked.connect(on_meta)
            cancel_button.clicked.connect(on_cancel)
            
            # 다이얼로그 화면 중앙 위치 설정
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            center_x = screen_rect.x() + screen_rect.width() // 2 - dialog.width() // 2
            center_y = screen_rect.y() + screen_rect.height() // 2 - dialog.height() // 2
            dialog.move(center_x, center_y)
            
            dialog.exec()
            
            # 선택된 형식으로 내보내기
            if result == "excel":
                return self.export_to_excel_with_dialog(users_data, parent_widget)
            elif result == "meta_csv":
                return self.export_to_meta_csv_with_dialog(users_data, parent_widget)
            else:
                return False
                
        except Exception as e:
            logger.error(f"저장 포맷 선택 다이얼로그 오류: {e}")
            return False
    
    def _show_save_completion_dialog(self, parent_widget, title: str, message: str, file_path: str):
        """저장 완료 다이얼로그 표시 - toolbox 공용 컴포넌트 사용"""
        try:
            from src.toolbox.ui_kit.modern_dialog import ModernSaveCompletionDialog
            
            # toolbox 공용 다이얼로그 사용
            ModernSaveCompletionDialog.show_save_completion(
                parent_widget, 
                title, 
                message, 
                file_path
            )
        except Exception as e:
            logger.warning(f"저장 완료 다이얼로그 표시 실패: {e}")
            # 폴백: 일반 메시지박스
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(parent_widget, title, message)