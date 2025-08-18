# 통합 관리 시스템 (Integrated Management System)

> 네이버 플랫폼 기반 마케팅 데이터 분석 통합 도구

## 📋 개요

통합 관리 시스템은 네이버 검색광고, 쇼핑, 카페 등의 플랫폼에서 마케팅 데이터를 자동으로 수집하고 분석하는 데스크톱 애플리케이션입니다. 키워드 분석, 상품 순위 추적, 카페 회원 추출, 파워링크 분석 등의 기능을 제공합니다.

## ✨ 주요 기능

### 🔍 키워드 분석 (Keyword Analysis)
- **검색량 분석**: 네이버 검색광고 API를 통한 월간 검색량 조회
- **카테고리 분석**: 키워드별 상위 카테고리 및 상품 수 분석
- **경쟁강도 계산**: 검색량 대비 상품 수를 통한 경쟁 강도 산출
- **병렬 처리**: 다중 키워드 동시 분석으로 처리 속도 향상

### 📊 순위 추적 (Rank Tracking)
- **상품 순위 모니터링**: 특정 키워드에서 네이버 쇼핑 상품 순위 추적
- **프로젝트 관리**: 상품별 키워드 그룹 관리 및 추적
- **자동 업데이트**: 상품 정보 및 순위 이력 자동 갱신
- **통계 분석**: 시간별 순위 변화 추적 및 성과 분석

### 👥 네이버 카페 추출 (Naver Cafe)
- **회원 정보 수집**: 지정 카페 게시판의 작성자 정보 추출
- **게시판별 크롤링**: 특정 게시판 선택적 데이터 추출
- **중복 제거**: 동일 사용자 중복 추출 방지
- **광고 활용**: Meta 광고용 CSV 파일 생성

### 💰 파워링크 분석 (Powerlink Analyzer)
- **입찰가 분석**: PC/모바일 키워드별 입찰가 정보 수집
- **노출 위치 확인**: 실제 검색 결과에서 광고 위치 크롤링
- **효율성 순위**: 검색량, 클릭수, 입찰가 종합 추천 순위
- **최적화**: API 호출과 크롤링 병렬 처리

## 🛠 기술 스택

- **GUI**: PySide6 (Qt6 기반)
- **데이터베이스**: SQLite3
- **웹 크롤링**: Playwright
- **데이터 처리**: Pandas, NumPy
- **엑셀 처리**: OpenPyXL
- **HTTP 클라이언트**: Requests

## 📁 프로젝트 구조

```
integrated_management_system/
├── main.py                     # 애플리케이션 진입점
├── data/                       # 데이터 저장소
│   └── app.db                  # 통합 SQLite 데이터베이스
├── logs/                       # 로그 파일
├── config/                     # 설정 파일
└── src/
    ├── foundation/             # 핵심 인프라 (설정, DB, 로깅, HTTP)
    ├── vendors/                # 외부 API 클라이언트
    │   ├── naver/             # 네이버 API 통합
    │   ├── google/            # 구글 API (향후 확장)
    │   └── openai/            # OpenAI API
    ├── features/              # 비즈니스 기능 모듈
    │   ├── keyword_analysis/  # 키워드 분석
    │   ├── rank_tracking/     # 순위 추적
    │   ├── naver_cafe/        # 카페 회원 추출
    │   └── powerlink_analyzer/ # 파워링크 분석
    ├── toolbox/               # 공용 유틸리티
    └── desktop/               # 데스크톱 UI 프레임워크
```

## 🚀 설치 및 실행

### 필수 요구사항
- Python 3.8 이상
- Windows 10/11 (주 개발 환경)

### 설치 방법

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd integrated_management_system
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **Playwright 브라우저 설치**
   ```bash
   playwright install chromium
   ```

4. **애플리케이션 실행**
   ```bash
   python main.py
   ```

### EXE 빌드 (선택사항)

PyInstaller를 사용하여 독립 실행 파일 생성:
```bash
# build_exe.bat 실행
build_exe.bat
```

## ⚙️ 설정

### API 키 설정
애플리케이션 실행 후 다음 API 키들을 설정해야 합니다:

1. **네이버 검색광고 API**
   - Customer ID
   - Access License
   - Secret Key

2. **네이버 개발자 API**
   - Client ID
   - Client Secret

3. **OpenAI API** (선택사항)
   - API Key

### 주요 설정 항목
- **병렬 처리**: 동시 처리 스레드 수 설정
- **재시도 로직**: API 호출 실패 시 재시도 횟수
- **로그 레벨**: 디버그/정보/경고/에러 로그 레벨
- **크롤링 속도**: 웹 크롤링 속도 제한 설정

## 📖 사용법

### 1. 키워드 분석
1. "키워드 분석" 탭 선택
2. 키워드 목록 입력 (줄바꿈 또는 쉼표로 구분)
3. "분석 시작" 버튼 클릭
4. 결과를 엑셀로 내보내기

### 2. 순위 추적
1. "순위 추적" 탭에서 새 프로젝트 생성
2. 네이버 쇼핑 상품 URL 입력
3. 추적할 키워드 목록 추가
4. 자동 또는 수동으로 순위 업데이트

### 3. 카페 회원 추출
1. "네이버 카페" 탭 선택
2. 카페 이름 또는 URL 입력
3. 추출할 페이지 범위 설정
4. 크롤링 시작 및 결과 내보내기

### 4. 파워링크 분석
1. "파워링크 분석" 탭 선택
2. 분석할 키워드 입력
3. PC/모바일 입찰가 및 순위 분석
4. 추천 순위 기반 결과 확인

## 🔒 보안 및 주의사항

- **API 키 보안**: 모든 API 키는 암호화되어 로컬 데이터베이스에 저장
- **Rate Limiting**: 각 API의 호출 제한을 준수하여 안전한 사용
- **개인정보**: 수집된 데이터는 로컬에만 저장되며 외부 전송 없음
- **이용약관**: 각 플랫폼의 이용약관 및 로봇 정책 준수 필요

## 🔧 개발 및 기여

### 개발 환경 설정
```bash
# 개발 의존성 설치
pip install -r requirements.txt

# 테스트 실행
pytest

# 코드 품질 검사
pylint src/
```

### 아키텍처 원칙
- **레이어 분리**: foundation → vendors → features → desktop
- **SOLID 원칙**: 단일 책임, 개방-폐쇄, 의존성 역전 등
- **플러그인 아키텍처**: 새 기능 모듈 독립적 추가 가능

### 기여 방법
1. Fork 저장소
2. 기능 브랜치 생성 (`git checkout -b feature/new-feature`)
3. 변경사항 커밋 (`git commit -am 'Add new feature'`)
4. 브랜치 푸시 (`git push origin feature/new-feature`)
5. Pull Request 생성

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원 및 문의

- **버그 리포트**: GitHub Issues 페이지 활용
- **기능 요청**: GitHub Discussions 또는 Issues
- **문서 개선**: Wiki 기여 환영

## 🔄 업데이트 로그

### v1.0.0 (Current)
- 키워드 분석 기능 구현
- 순위 추적 시스템 구축
- 네이버 카페 회원 추출 기능
- 파워링크 분석 도구
- 통합 데스크톱 UI 완성

## 개발 정보

- 개발자: PARKJAEHYEONG922
- 이메일: wogud922@gmail.com
- GitHub: https://github.com/PARKJAEHYEONG922/MY-APP

---

*이 도구는 마케팅 분석 업무의 효율성 향상을 위해 개발되었습니다. 합법적이고 윤리적인 사용을 권장합니다.*