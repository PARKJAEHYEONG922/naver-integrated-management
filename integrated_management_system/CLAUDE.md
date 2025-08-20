# CLAUDE.md — 파일별 책임/편집 가이드

> **목표**: Claude Code(이하 ‘클로드’)가 이 저장소에서 작업할 때 *정확히 어디를 수정해야 하는지* 즉시 판단할 수 있도록, **파일별 역할/허용 작업/금지 작업**을 명확히 규정한다.
> **핵심 원칙**: 동작 불변(기능 변경 금지), UI 변경 금지(승인 전), 의존 방향 준수: `features → vendors → foundation` (단방향). `toolbox`는 어디서든 사용 가능, `desktop`은 앱 프레임으로 모두 참조 가능. `features` 간 직접 참조 금지.

---

## 1) 최상위 편집 수칙 (클로드 전용)

* **작업 범위 최소화**: 요청된 파일·모듈만 수정.
* **UI 레이아웃/문구/스타일 변경 금지**: 승인 없이 `features/*/ui*.py`, `desktop/*`, `toolbox/ui_kit/*`의 시각적 변경 금지.
* **절대 임포트 사용**: `from src.features.xxx.service import ...` (상대/와일드카드 금지).
* **의존 방향**: `service → adapters → vendors/foundation/toolbox` / `models`는 데이터 구조만. 역참조 금지.
* **리팩토링 허용 범위**: 미사용 import/변수 제거, 네이밍·주석·도크스트링 개선(동작 불변). 큰 구조 변경 전 사전 승인.

---

## 2) 디렉터리 개요와 편집 포인트

### 2.1 foundation/  (공용 토대)

* **config.py**: 경로/환경(APP\_MODE) 헬퍼.
* **http\_client.py**: 공통 HTTP(타임아웃/재시도).
* **logging.py**: 로깅 초기화.
* **db.py**: SQLite 헬퍼. 쿼리 텍스트는 `features/*/models.py`에서 정의.

### 2.2 vendors/  (외부 API 클라이언트, Raw 모델)

* Raw 호출·페이지네이션·최소 정규화.
* `client_factory.py`: 통합 접근.
* `models.py`/`normalizers.py`: Raw → 표준 필드 최소 통일.

> **클로드가 여기를 수정해야 할 때**: 새 엔드포인트 추가, 응답 필드 증감 등 **벤더 I/O층 개선**이 필요할 때.

### 2.3 toolbox/  (공용 유틸/UI)

* **text\_utils.py**: 텍스트 처리·형식 검증(URL/키/경로/날짜 등). 네트워크 호출 금지.
* **ui\_kit/**: 공용 UI 컴포넌트. 디자인 변경 금지.

> **클로드가 여기를 수정해야 할 때**: 입력 파싱·검증 규칙 강화, 재사용 유틸 추가.

### 2.4 desktop/  (앱 프레임)

* **app.py/sidebar.py**: 모듈 등록·라우팅.
* **api\_dialog.py**: API 키 설정 창.
* **api\_checker.py**: 네트워크 연결/권한 테스트.

### 2.5 features/<module>/  (비즈니스 모듈: **5파일 고정**)

* **service.py** *(오케스트레이션)*
* **adapters.py** *(벤더 호출·정규화·엑셀/CSV 저장 I/O)*
* **models.py** *(DTO/DDL/레포 헬퍼)*
* **ui\*.py** *(UI 화면/컴포넌트 — 다파일 분할 허용)*
* **worker.py** *(장시간 작업/비동기 처리)*

---

## 3) 파일별 책임 (5핵심 파일)

### service.py — 오케스트레이션(흐름)

**한다**

* 입력 검증 호출(`toolbox.text_utils`)
* `adapters` 통해 Raw 수집 → 정규화 데이터 획득
* 간단 계산/정렬/필터, 점수 집계
* `foundation.db` 경유 DB 읽기/쓰기
* `adapters.export_to_excel()` 트리거
* 로깅/에러 핸들/재시도/진행률 업데이트

**하지 않는다**

* 벤더 직접 호출
* 파일 저장(I/O)

**분할 규칙**

* **700\~1000줄 이상** 또는 함수 300줄↑이면 \*\*`engine_local.py`\*\*로 계산/랭킹/스코어링 **순수 로직 분리**.

  * `service.py`는 orchestration만 유지(입력→adapters→engine\_local→models→adapters(export)).
  * `engine_local.py`는 **I/O 금지**(파일/DB/HTTP 없음), **순수 함수/클래스**만.

---

### adapters.py — 입출력 접착(벤더/파일)

**한다**

* `vendors.*` 호출, 정규화
* 엑셀/CSV 저장(I/O), UI 포맷 변환
* 벤더 예외 → 도메인 예외 매핑

**하지 않는다**

* DB 접근
* 비즈니스 로직

---

### models.py — 데이터 구조/스키마

**한다**

* DTO/엔티티, Enum, 상수
* 테이블 DDL, 간단 레포 헬퍼

**하지 않는다**

* 파일/네트워크 I/O
* 비즈니스 로직

---

### ui\*.py — 화면/UI 로직 (분할 허용)

**한다**

* 모듈별 **UI 구성 요소와 화면 로직**
* `toolbox/ui_kit` 컴포넌트 활용
* 사용자 입력 이벤트 처리 후 `service` 호출
* **파일 분할 가이드**(권장 네이밍)

  * `ui_main.py` : 메인 화면(탭/레이아웃/상단 액션)
  * `ui_list.py` : 목록/필터/검색 바인딩(예: 키워드 리스트)
  * `ui_table.py`: 결과 테이블/정렬/페이징/엑셀 내보내기 버튼 바인딩
  * 필요 시 `ui_widgets.py`: 커스텀 소형 위젯(태그/배지/행 위젯 등)

**하지 않는다**

* 벤더 호출, DB 직접 접근, 비즈니스 계산
* **진행 스레드 직접 제어**(→ `worker.py`에 위임)

**의존 규칙**

* `ui*.py → service` (OK)
* `ui*.py → adapters/models` (직접 호출 금지, 필요 데이터는 `service` 경유)

---

### worker.py — 장시간 작업/비동기 처리

**한다**

* 큐/스레드/비동기 작업 실행(예: PySide6 QThread/QRunnable)
* 진행률 업데이트·취소/중단 핸들링(시그널/콜백)
* 완료 후 `service` 호출 및 결과 반환(또는 이벤트 방출)

**하지 않는다**

* UI 직접 제어(시그널로 전달)
* DB 트랜잭션/벤더 호출 직접 수행(필요 시 `service`에 위임)

**의존 규칙**

* `worker.py → service` (OK)
* `worker.py → adapters/models/ui` 직접 참조 금지

---

## 4) 보조 규칙: 검증/체커/계산 분리

* **text\_utils.py**: 형식 검증(네트워크 無).
* **desktop/api\_checker.py**: 네트워크 연결/권한 테스트.
* **engine\_local.py (옵션)**: 복잡한 계산식 전용(분할 트리거 기준 상기 참고).

---

## 5) 작업 유형별 배치 표

| 작업 유형        | 수정 위치                                    |
| ------------ | ---------------------------------------- |
| 입력 파싱/검증     | toolbox/text\_utils.py                   |
| API 키/권한 테스트 | desktop/api\_checker.py                  |
| 벤더 엔드포인트 추가  | vendors/\*                               |
| 응답 필드 매핑 수정  | vendors/\*/normalizers.py                |
| 엑셀/CSV 내보내기  | features/<module>/adapters.py            |
| 랭킹/점수 보정     | features/<module>/service.py             |
| 복잡한 계산식      | features/<module>/engine\_local.py       |
| DB 컬럼/DDL 추가 | features/<module>/models.py              |
| UI 화면/이벤트    | features/<module>/ui\_main.py 등 UI 분할 파일 |
| 장시간 배치/진행률   | features/<module>/worker.py              |

---

## 6) **금지 사항 체크리스트 (MUST NOT)**

* [ ] `service.py`에서 벤더 클라 직접 호출 ❌
* [ ] `adapters.py`에서 DB 접근 ❌
* [ ] `models.py`에서 파일/네트워크 I/O ❌
* [ ] `ui*.py`에서 비즈니스 계산·DB 접근 ❌
* [ ] `worker.py`에서 UI 직접 조작/벤더 직접 호출 ❌
* [ ] 승인 전 UI 레이아웃/문구/스타일 변경 ❌
* [ ] 상대/와일드카드 임포트 사용 ❌

---

## 7) 예시 트리 (UI 분할/엔진 분리 포함)

```
src/features/powerlink_analyzer/
 ├─ service.py
 ├─ adapters.py
 ├─ models.py
 ├─ engine_local.py           # 700~1000줄 이상시 계산·랭킹 분리
 ├─ worker.py                 # 장시간 수집/분석 작업
 ├─ ui_main.py                # 탭/상단 액션/라우팅
 ├─ ui_list.py                # 좌측 목록/검색/필터
 ├─ ui_table.py               # 결과 테이블/정렬/엑셀 버튼
```

---

## 8) 커밋/PR 규칙 (샘플)

* **메시지**: `feat(powerlink_analyzer): ui 분할(ui_main/ui_table) 및 engine_local 도입`
* **본문**: 변경 사유·영향 범위·테스트 결과·리스크(회귀 가능성) 명시.
* **PR 크기**: 작게 유지(한 목적/모듈 위주). 동작 변경 시 반드시 이유 선기재.

---

> 이제 모든 모듈은 **service/adapters/models/ui*/worker*\* 5파일이 기본 구조이며, UI는 목적별 파일 분할(`ui_main/ui_list/ui_table/`)을 권장한다. `service`가 비대해지면 즉시 `engine_local.py`로 계산을 분리한다.

현재 코드 구조
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
│  │  ├─ text_utils.py                 # 통합 텍스트 처리 유틸리티,형식 검증(URL/키/경로/날짜 등, 네트워크 X)
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
│  │  │  ├─ ui.py                      # 화면
│  │  │  └─ worker.py                  # 장시간 작업,비동기 작업
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