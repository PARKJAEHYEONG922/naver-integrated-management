# CLAUDE.md — 파일별 책임/편집 가이드 (최종본)

> **목표**: Claude Code(이하 ‘클로드’)가 이 저장소에서 작업할 때 *정확히 어디를 수정해야 하는지* 즉시 판단할 수 있도록, **파일별 역할/허용 작업/금지 작업**을 명확히 규정한다.  
> **핵심 원칙**: 동작 불변(기능 변경 금지), UI 변경 금지(승인 전), 의존 방향 준수: `features → vendors → foundation` (단방향). `toolbox`는 어디서든 사용 가능, `desktop`은 앱 프레임으로 모두 참조 가능. `features` 간 직접 참조 금지.

---

## 1) 최상위 편집 수칙 (클로드 전용)

- **작업 범위 최소화**: 요청된 파일·모듈만 수정.  
- **UI 레이아웃/문구/스타일 변경 금지**: 승인 없이 `features/*/ui*.py`, `desktop/*`, `toolbox/ui_kit/*`의 시각적 변경 금지.  
- **절대 임포트 사용**: `from src.features.xxx.service import ...` (상대/와일드카드 금지).  
- **의존 방향**: `service → adapters → vendors/foundation/toolbox` / `models`는 데이터 구조만. 역참조 금지.  
- **리팩토링 허용 범위**: 미사용 import/변수 제거, 네이밍·주석·도크스트링 개선(동작 불변). 큰 구조 변경 전 사전 승인.  

---

## 2) 디렉터리 개요와 편집 포인트

### 2.1 foundation/  
- config.py: 경로/환경(APP_MODE) 헬퍼  
- http_client.py: 공통 HTTP(타임아웃/재시도)  
- logging.py: 로깅 초기화  
- db.py: SQLite 헬퍼. 쿼리 텍스트는 `features/*/models.py`에서 정의  

### 2.2 vendors/  
- 외부 API 클라이언트, Raw 모델  
- client_factory.py: 통합 접근  
- models.py/normalizers.py: Raw → 표준 필드 최소 통일  

### 2.3 toolbox/  
- text_utils.py: 텍스트 처리·형식 검증(URL/키/경로/날짜 등). 네트워크 호출 금지  
- formatters.py: **표시/내보내기용 포맷 유틸**  
  - 규칙: DB/내부 계산엔 원시값 저장, UI/엑셀/CSV 등 사람이 읽는 결과에만 사용  
  - API 예시:  
    - `format_int`  
    - `format_float`  
    - `format_percent`  
    - `format_price_krw`  
    - `format_competition`  
    - `format_date`, `format_datetime`  
    - `safe_str`, `join_nonempty`  
- progress.py: **진행률 계산 유틸**  
  - `calc_percentage(done, total, clamp=True)` → 0~100 float (0/total 방지, 클램프)  
  - `throttle_ms(now_ms, last_ms, min_interval_ms)` → 과도한 업데이트 억제 (옵션)  
- ui_kit/: 공용 UI 컴포넌트  
  - components.py: 공용 버튼/입력/토스트/아이콘  
  - modern_dialog.py: 공통 다이얼로그(Form/Confirm/Progress/FileSave)  
  - modern_style.py: 모던 스타일 토큰/테마  
  - modern_table.py: 표준 테이블 위젯  
  - sortable_items.py: 안정 정렬 아이템(숫자/날짜/텍스트)  

### 2.4 desktop/  
- app.py/sidebar.py: 모듈 등록·라우팅  
- api_dialog.py: API 키 설정 창  
- api_checker.py: 네트워크 연결/권한 테스트  

### 2.5 features/<module>/  
- service.py *(오케스트레이션)*  
- adapters.py *(벤더 호출·정규화·엑셀/CSV 저장 I/O)*  
- models.py *(DTO/DDL/레포 헬퍼)*  
- ui*.py *(UI 화면/컴포넌트 — 다파일 분할 허용)*  
- worker.py *(장시간 작업/비동기 처리)*  

---

## 3) 파일별 책임

### service.py  
- 입력 검증(`toolbox.text_utils`)  
- adapters 통해 Raw 수집 → 정규화 데이터 획득  
- DB 읽기/쓰기(`foundation.db`)  
- adapters.export_to_excel() 트리거  
- 로깅/에러 핸들/재시도  
- 계산은 engine_local 호출 (직접 구현 ❌)  

### engine_local.py  
- 점수 계산, 랭킹, 필터/정렬, 통계 요약  
- 입력/출력: DTO(models) 또는 기본 타입  
- **I/O/로깅/시그널 금지**  

### adapters.py  
- vendors 호출, 정규화  
- 엑셀/CSV 저장(I/O), UI 포맷 변환  
- 벤더 예외 → 도메인 예외 매핑  

### models.py  
- DTO/엔티티, Enum, 상수  
- 테이블 DDL, 간단 레포 헬퍼  

### ui*.py  
- 모듈 UI 화면/컴포넌트  
- toolbox/ui_kit 컴포넌트 적극 활용  
- 사용자 입력 이벤트 처리 후 service 호출  

### worker.py  
- 큐/스레드/비동기 실행(QThread/QRunnable)  
- 진행률 업데이트·취소/중단 시그널 발행  
- 완료/에러 시그널 방출  
- **진행률 % 계산은 toolbox.progress.calc_percentage 사용 권장**  

---

## 4) 보조 규칙
- text_utils.py: 형식 검증  
- api_checker.py: 네트워크 테스트  
- engine_local.py: 복잡 계산식 전용  
- formatters.py: **표시/내보내기 전용 포맷** (DB/연산 금지)  
- progress.py: **진행률 계산/업데이트 빈도 제어**  

---

## 5) 작업 유형별 배치

| 작업 유형              | 수정 위치 |
|-----------------------|-----------|
| 입력 파싱/검증         | toolbox/text_utils.py |
| API 키/권한 테스트     | desktop/api_checker.py |
| 벤더 엔드포인트 추가   | vendors/* |
| 응답 필드 매핑 수정    | vendors/*/normalizers.py |
| 엑셀/CSV 내보내기      | features/<module>/adapters.py |
| 랭킹/점수 보정         | features/<module>/engine_local.py |
| 복잡한 계산식          | features/<module>/engine_local.py |
| DB 컬럼/DDL 추가       | features/<module>/models.py |
| UI 화면/이벤트         | features/<module>/ui_main.py 등 |
| 장시간 배치/진행률     | features/<module>/worker.py |
| 문자열/숫자/날짜 포맷 | toolbox/formatters.py |
| 진행률 계산(%)         | toolbox/progress.py |

---

## 6) 금지 사항 체크리스트
- [ ] service.py에서 벤더 직접 호출 ❌  
- [ ] adapters.py에서 DB 접근 ❌  
- [ ] models.py에서 파일/네트워크 I/O ❌  
- [ ] ui*.py에서 비즈니스 계산·DB 접근 ❌  
- [ ] worker.py에서 UI 직접 조작/벤더 직접 호출 ❌  
- [ ] 승인 전 UI 레이아웃/문구/스타일 변경 ❌  
- [ ] 상대/와일드카드 임포트 ❌  

---

## 7) 예시 트리 (UI 분할/엔진 분리 포함)

```
src/features/powerlink_analyzer/
├─ service.py # 오케스트레이션(검증→adapters→engine_local→DB/엑셀 트리거)
├─ engine_local.py # 스코어/랭킹/계산(순수 함수, 모든 모듈 필수)
├─ adapters.py # 벤더 호출·정규화·엑셀/CSV 저장(I/O)
├─ models.py # DTO/엔티티/DDL·레포 헬퍼
├─ worker.py # 장시간 작업/취소/진행률(QThread/시그널)
├─ ui_main.py # 탭/레이아웃/상단 액션·서비스 호출 진입점
├─ ui_list.py # 목록/검색/필터 패널(공용 버튼 사용)
├─ ui_table.py # 결과 테이블/정렬/페이징(ModernTable + SortableItems)
└─ ui_widgets.py # (옵션) 모듈 전용 소형 위젯
```

---

## 8) **전체 저장소 트리(설명 포함)**

```
integrated_management_system/
├─ src/
│  ├─ foundation/                      # 공용 토대(설정/HTTP/로깅/DB)
│  │  ├─ config.py                     # 경로/환경(APP_MODE) 헬퍼
│  │  ├─ http_client.py                # 공통 HTTP(타임아웃/재시도)
│  │  ├─ logging.py                    # 로깅 초기화
│  │  └─ db.py                         # SQLite 헬퍼(연결/트랜잭션/기본 CRUD)
│  │
│  ├─ vendors/                         # 외부 API(Raw) + 최소 정규화
│  │  ├─ naver/
│  │  │  ├─ client_factory.py          # 네이버 API 통합 접근
│  │  │  ├─ models.py                  # 네이버 표준 모델
│  │  │  ├─ normalizers.py             # Raw→표준 필드 정규화
│  │  │  ├─ developer/                 # 네이버 개발자센터 검색 API
│  │  │  │  ├─ shopping_client.py      # 쇼핑 검색
│  │  │  │  ├─ news_client.py          # 뉴스 검색
│  │  │  │  ├─ blog_client.py          # 블로그 검색
│  │  │  │  ├─ cafe_client.py          # 카페 검색
│  │  │  │  └─ book_client.py          # 도서 검색
│  │  │  └─ searchad/
│  │  │     └─ keyword_client.py       # 검색광고 키워드 도구
│  │  ├─ openai/
│  │  │  └─ client.py                  # OpenAI 클라이언트(향후)
│  │  └─ web_automation/
│  │     └─ playwright_helper.py       # Playwright 헬퍼
│  │
│  ├─ toolbox/                         # 공용 유틸/공용 UI
│  │  ├─ formatters.py
│  │  ├─ progress.py
│  │  ├─ text_utils.py                 # 형식 검증·텍스트 유틸(네트워크 X)
│  │  └─ ui_kit/
│  │     ├─ components.py              # 공용 버튼/입력/토스트
│  │     ├─ modern_dialog.py           # 공통 다이얼로그(Form/Confirm/Progress/FileSave)
│  │     ├─ modern_style.py            # 모던 스타일 토큰/테마
│  │     ├─ modern_table.py            # 표준 테이블 위젯
│  │     └─ sortable_items.py          # 정렬 가능한 아이템(숫자/날짜 안정 정렬)
│  │
│  ├─ features/                        # 각 비즈니스 모듈(5파일 + 분할 UI)
│  │  ├─ keyword_analysis/
│  │  │  ├─ service.py | adapters.py | models.py | engine_local.py | worker.py
│  │  │  ├─ ui_main.py | ui_list.py | ui_table.py | ui_widgets.py
│  │  ├─ rank_tracking/                # 동일 구조
│  │  ├─ naver_cafe/                   # 동일 구조
│  │  └─ powerlink_analyzer/           # 동일 구조
│  │
│  ├─ desktop/                         # 데스크톱 앱 프레임
│  │  ├─ app.py                        # 메인 윈도우/앱 실행
│  │  ├─ sidebar.py                    # 모듈 register(app)
│  │  ├─ api_dialog.py                 # API 설정 다이얼로그
│  │  ├─ api_checker.py                # 라이브 상태 점검(네트워크 O)
│  │  ├─ components.py | styles.py     # 앱 전용 공용 컴포넌트/스타일
│  │
│  └─ main.py                          # 진입점
│
├─ assets/                              # 아이콘/이미지
├─ data/                                # 런타임 데이터(예: app.db)
├─ scripts/
│  ├─ nuitka_compile_core.bat          # (.pyd 빌드 스크립트 예시)
│  └─ build_windows.bat                # (EXE 빌드 스크립트 예시)
└─ updater/
   └─ version.json                     # (옵션) 자동 업데이트 매니페스트
```

---

## 9) 커밋/PR 규칙 (샘플)

* **메시지**: `feat(powerlink_analyzer): ui 분할(ui_main/ui_table) 및 engine_local 도입`
* **본문**: 변경 사유·영향 범위·테스트 결과·리스크(회귀 가능성) 명시.
* **PR 크기**: 작게 유지(한 목적/모듈 위주). 동작 변경 시 반드시 이유 선기재.

---

## 10) 배포/보호 전략 — .pyd & EXE 가이드

* **.pyd 대상**: `engine_local.py` (순수 계산) 권장. `service.py`는 I/O·의존 많아 비권장.
* **인터페이스 체크**: 입력/출력 타입 단순화, `__all__`로 공개 범위 제한, 예외 매핑은 로컬 예외 사용.
* **빌드 예시**: Nuitka로 .pyd 생성 → PyInstaller로 desktop/app.py EXE 패킹 시 함께 포함.

---

## 11) SOLID 실무 요약 (가이드에 이미 반영됨)

* **SRP (단일 책임)**: 파일 하나 = 한 책임. `service/adapters/models/ui*/worker/engine_local`로 분리.
* **OCP (개방/폐쇄)**: 새 기능은 파일 추가/확장 우선, 기존 코드 수정 최소.
* **ISP (인터페이스 분리)**: 긴 함수/복합 클래스를 작은 인터페이스/함수로 쪼갬. UI는 화면별 파일 분할.
* **DIP (의존 역전)**: 엔진은 순수 함수, 외부 의존은 `service/adapters`에서 주입. 전역 싱글톤 지양.

---

> 이제 모든 모듈은 **service/adapters/models/ui*/worker*\* 5파일 기본 구조이며, UI는 목적별 분할(`ui_main/ui_list/ui_table`)을 권장한다. **공용 다이얼로그는 `modern_dialog`**, **모듈 전용 다이얼로그는 해당 `ui*.py`**, **모든 버튼은 `components`의 공용 버튼**을 사용한다. 민감 계산 로직은 `engine_local.py`로 분리해 `.pyd`로 보호한다.
