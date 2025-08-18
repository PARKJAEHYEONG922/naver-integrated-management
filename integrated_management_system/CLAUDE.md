CLAUDE.md (Lite)

이 문서는 Claude Code가 이 저장소에서 작업할 때 따라야 할 규칙과 맥락을 제공합니다.
목표: 단순한 구조, 모듈별 동일한 틀, 빠른 개발과 쉬운 유지보수, 추후 확장(원격/.pyd) 여지 확보.

1) 최상위 원칙 (MUST)

동작하는 기능을 바꾸지 말 것. 변경/버그 수정은 요청된 범위만.
UI(레이아웃/스타일/문구) 변경 금지. 명시 승인 없으면 수정 금지.

의존 방향 고정:
features → vendors → foundation (단방향)
toolbox는 어디서든 사용 가능, desktop은 앱 프레임으로 모든 레이어 참조 가능.
features끼리 직접 참조 금지 vendors가 features 참조 금지 foundation은 상위(업무/벤더) 지식 금지

SOLID(실무 축약) 
SRP: 파일/클래스는 한 책임 
OCP: 새 기능은 파일 추가/확장으로, 기존 수정 최소 
ISP: 긴 함수는 작은 인터페이스/함수로 분리 
DIP: 의존성은 생성자/인자 주입, 전역 싱글톤 지양 리팩토링 허용 범위 미사용 import/변수 제거, 네이밍·주석 개선(동작 불변) 크리티컬 파일 변경 전: 이유를 요약해 승인 먼저 받기

분리 원칙(간단):
service.py = 흐름/오케스트레이션
adapters.py = 벤더 호출·변환·파일 I/O
models.py = 데이터 구조/스키마
(복잡해지면 그때 engine_local.py로 계산만 분리)
허용 리팩토링: 미사용 import/변수 제거, 네이밍·주석·도크스트링 개선(동작 불변).
PR 규칙: 작은 PR, 관련 파일만. 절대 임포트 사용(예: from src.features.xxx.service import ...), import * 금지.

2) 저장소 개요(현재 규모에 맞춘 구조)
integrated_management_system/
├─ src/
│  ├─ foundation/                      # 공용 토대(설정/HTTP/로깅/DB)
│  │  ├─ __init__.py
│  │  ├─ config.py                     # 경로/환경(APP_MODE="local") 헬퍼
│  │  ├─ http_client.py                # 공통 HTTP(타임아웃/재시도)
│  │  ├─ logging.py                    # 로깅 초기화
│  │  └─ db.py                         # (필요 시) SQLite 헬퍼
│  │
│  ├─ vendors/                         # 외부 API(Raw) + 최소 정규화만
│  │  ├─ __init__.py
│  │  ├─ naver/
│  │  │  ├─ __init__.py
│  │  │  ├─ client_factory.py          # 통합 팩토리 (모든 네이버 API 접근)
│  │  │  ├─ models.py                  # 공통 모델 (응답 데이터 구조)
│  │  │  ├─ normalizers.py             # 공통 정규화 (필드명/타입 통일)
│  │  │  ├─ developer/                 # 네이버 개발자 센터 API
│  │  │  │  ├─ __init__.py
│  │  │  │  ├─ base_client.py          # 검색 API 공통 베이스
│  │  │  │  ├─ search_apis.py          # 검색 API 메타데이터
│  │  │  │  ├─ shopping_client.py      # 쇼핑 검색 API
│  │  │  │  ├─ news_client.py          # 뉴스 검색 API
│  │  │  │  ├─ blog_client.py          # 블로그 검색 API
│  │  │  │  ├─ cafe_client.py          # 카페 검색 API
│  │  │  │  └─ book_client.py          # 도서 검색 API
│  │  │  └─ searchad/                  # 네이버 검색광고 API
│  │  │     ├─ __init__.py
│  │  │     ├─ base_client.py          # 검색광고 API 공통 베이스
│  │  │     ├─ apis.py                 # 검색광고 API 메타데이터
│  │  │     └─ keyword_client.py       # 키워드 도구 API
│  │  ├─ google/                       # 구글 API (향후 확장용)
│  │  │  ├─ __init__.py
│  │  │  ├─ search/
│  │  │  │  └─ __init__.py
│  │  │  └─ youtube/
│  │  │     └─ __init__.py
│  │  ├─ openai/
│  │  │  ├─ __init__.py
│  │  │  └─ client.py
│  │  └─ web_automation/
│  │     ├─ __init__.py
│  │     └─ playwright_helper.py
│  │
│  ├─ toolbox/                         # 공용 유틸/공용 UI(벤더·비즈 지식 없음)
│  │  ├─ __init__.py
│  │  ├─ validators.py                 # 형식 검증(URL/키/경로/날짜 등, 네트워크 X)
│  │  ├─ text_utils.py                 # 통합 텍스트 처리 유틸리티
│  │  └─ ui_kit/
│  │     ├─ __init__.py
│  │     ├─ modern_style.py            # CSS 스타일 시스템
│  │     ├─ components.py              # 공용 위젯(Button/Input/Table/Toast)
│  │     ├─ modern_dialog.py           # 범용 다이얼로그(Form/Confirm/Progress/FileSave)
│  │     └─ sortable_items.py          # 정렬 가능한 테이블/트리 아이템
│  │
│  ├─ features/                        # 비즈니스 기능(모듈별 동일 3파일 + 옵션)
│  │  ├─ keyword_analysis/
│  │  │  ├─ __init__.py
│  │  │  ├─ service.py                 # 오케스트레이션(검증→벤더→가공→저장/엑셀)
│  │  │  ├─ adapters.py                # 벤더 호출·정규화·엑셀/CSV 저장
│  │  │  ├─ models.py                  # DTO/엔티티/DDL 헬퍼
│  │  │  ├─ ui.py                      # (옵션) 화면
│  │  │  └─ worker.py                  # (옵션) 장시간 작업
│  │  ├─ rank_tracking/                # ⟵ 동일 구조
│  │  ├─ naver_cafe/                   # ⟵ 동일 구조
│  │  └─ powerlink_analyzer/           # ⟵ 동일 구조
│  │
│  ├─ desktop/                         # 데스크톱 앱 프레임
│  │  ├─ __init__.py
│  │  ├─ app.py                        # 메인 윈도우/앱 실행
│  │  ├─ sidebar.py                    # 모듈 register(app) 연결
│  │  ├─ api_dialog.py                 # API 설정 다이얼로그
│  │  ├─ api_checker.py                # 라이브 상태 점검(네트워크 O)
│  │  ├─ components.py                 # 앱 전용 공용 컴포넌트
│  │  └─ styles.py                     # 앱 전용 스타일 확장
│  │
│  └─ main.py                          # 진입점
│
├─ assets/                              # 아이콘/이미지
├─ data/                                # 런타임 데이터(예: app.db)
├─ scripts/
│  ├─ nuitka_compile_core.bat          # (옵션) 나중에 .pyd 필요 시 사용
│  └─ build_windows.bat                # (옵션) EXE 빌드
└─ updater/
   └─ version.json                     # (옵션) 자동 업데이트 매니페스트(스텁)


지금은 원격/서버 없음 → engine_remote.py, engine.py, server/, installer/ 없음.
필수는 3파일: service.py / adapters.py / models.py (모듈 공통).

3) 파일별 책임(딱 3개 기준)
service.py — 오케스트레이션(흐름)
-한다: 입력 형식 검증 호출(validators) → adapters로 벤더 Raw 수집/정규화 → (간단) 계산/정렬/필터 → DB 읽기/쓰기 → 엑셀 내보내기 트리거(실제 파일 저장은 adapters) → 로깅/에러/재시도/진행률.
-하지 않는다: 벤더 클라 직접 호출(반드시 adapters 경유), 엑셀 포맷 정의·파일 I/O.

adapters.py — 입출력 접착(벤더/파일)
-한다: vendors.* 호출로 Raw 수집, 필드·타입 정규화, 엑셀/CSV 저장(I/O), UI표시용 포맷 변환, 벤더 예외→도메인 예외 매핑.
-하지 않는다: DB 접근, 점수식/랭킹 등 비즈니스 결정 로직.

models.py — 데이터 구조/스키마
-한다: DTO/엔티티(dataclass/TypedDict), 상수/Enum, DDL/간단 레포 헬퍼(테이블 생성/INSERT 등) — 트랜잭션은 service에서.
-하지 않는다: 벤더/파일/네트워크/로깅 등 I/O, 비즈니스 로직.

4) 의존 규칙

service.py → adapters.py, models.py, foundation/*, toolbox/* OK
adapters.py → vendors/*, toolbox/* OK, (service/models 호출 금지)
models.py → 표준 라이브러리/typing만 (service/adapters/벤더 호출 금지)

5) 작업 순서(Claude 워크플로)

요청 범위 확인 → 해당 모듈만 열기
service.py에서 흐름 확인/수정
벤더 호출/정규화는 항상 adapters.py 수정
데이터 구조/DDL은 models.py 수정
형식검증은 toolbox/validators.py, 라이브 확인은 desktop/api_checker.py
DB는 foundation/db.py 경유

UI 변경 금지(승인 전)

6) 새 기능 추가 체크리스트 (모듈 템플릿)
src/features/<new_module>/ 생성
파일 생성: service.py, adapters.py, models.py (필요시 ui.py, worker.py)
service.py에 오케스트레이션 작성 (adapters 경유, DB/엑셀 트리거 포함)
adapters.py에 벤더 호출/정규화/엑셀 저장 작성
models.py에 DTO/DDL/레포 헬퍼 작성 → service.py에서 호출
실행 확인 → 작은 PR

7) 커졌을 때의 "점진 확장" (트리거 & 액션)
service.py가 400줄↑ / 계산 규칙 복잡 → engine_local.py 추가, 계산만 옮기기(.pyd 대상)
코드 보호/중앙 통제 필요 → 그때 engine_remote.py+engine.py(스위치)와 server/(FastAPI) 도입
배포 자동화/업데이트 필요 → scripts/, updater/ 내용 채우기

8) 빌드/배포(옵션)

.pyd 보호 대상: 각 모듈의 engine_local.py 만 (있을 때)
EXE 빌드: scripts/build_windows.bat (PyInstaller) — 나중에 작성
자동 업데이트: updater/version.json 스텁 유지(후에 연결)

9) 빠른 위치 안내

네이버 API 통합 접근 → vendors/naver/client_factory.py
정규화/엑셀 저장 → features/<module>/adapters.py
DB DDL/INSERT 헬퍼 → features/<module>/models.py
흐름/검증/저장/로그 → features/<module>/service.py
형식검증 → toolbox/validators.py
라이브 점검 → desktop/api_checker.py
공용 버튼/다이얼로그 → toolbox/ui_kit/{components.py, modern_dialog.py}
텍스트 처리 → toolbox/text_utils.py
테이블 정렬 → toolbox/ui_kit/sortable_items.py

10) 변경 전 체크리스트

이 변경이 맞는 레이어에 있는가?
의존 방향을 깨지 않았는가?
UI 변경이 없는가(승인 전 금지)?
기존 동작 회귀 위험은 없는가?
의도/사유를 주석/도크스트링으로 남겼는가?

11) 커밋/PR 규칙

메시지 예: feat(keyword_analysis): 후보 키워드 정규화 추가
하나의 PR엔 하나의 목적만. 테스트/실행 결과 간단 첨부.
크리티컬 파일 변경 사유를 PR 본문에 명확히.

12) 빠른 위치 안내(FAQ 스타일) 
네이버 쇼핑/뉴스/블로그 Raw 호출? → vendors/naver/developer/shopping_client.py, news_client.py, blog_client.py 
네이버 검색광고 월검색량/예상실적? → vendors/naver/searchad/keyword_client.py 
네이버 응답 표준화? → vendors/naver/normalizers.py + vendors/naver/models.py
네이버 API 통합 접근? → vendors/naver/client_factory.py 
키/권한 라이브 점검? → desktop/api_checker.py URL/
키 포맷·경로·날짜 검증? → toolbox/validators.py 
모듈별 알고리즘(핵심 로직)? → features/<module>/service.py (.pyd 배포) 
엑셀/포맷 가공? → features/<module>/adapters.py 
DB 연결/트랜잭션/헬퍼? → foundation/db.py 
공용 버튼/다이얼로그? → toolbox/ui_kit/{components,modern_dialog}.py
텍스트 처리? → toolbox/text_utils.py
테이블 정렬? → toolbox/ui_kit/sortable_items.py