"""
Playwright 기반 웹 크롤링 공용 헬퍼
다른 모듈에서도 재사용 가능한 플레이라이트 래퍼
"""
import asyncio
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass

try:
    from playwright.async_api import async_playwright, Browser, Page, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright가 설치되지 않았습니다. 'pip install playwright' 후 'playwright install chromium'를 실행하세요.")

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print("⚠️ aiohttp가 설치되지 않았습니다. 'pip install aiohttp'를 실행하세요.")


@dataclass
class BrowserConfig:
    """브라우저 설정"""
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    timeout: int = 30000
    args: List[str] = None
    
    # 🚀 성능 최적화 옵션
    block_images: bool = True          # 이미지 차단
    block_css: bool = False            # CSS 차단 (레이아웃 필요시 False)
    block_ads: bool = True             # 광고 차단
    block_analytics: bool = True       # 분석 스크립트 차단
    fast_loading: bool = True          # 빠른 로딩 모드
    
    def __post_init__(self):
        if self.args is None:
            base_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-notifications',
                '--disable-gpu'
            ]
            
            # 🚀 성능 최적화 args 추가
            if self.fast_loading:
                base_args.extend([
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ])
            
            self.args = base_args


class PlaywrightHelper:
    """Playwright 기반 웹 크롤링 헬퍼 클래스"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.cleanup()
        
    async def initialize(self):
        """플레이라이트 초기화"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright가 설치되지 않았습니다.")
        
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp가 설치되지 않았습니다.")
        
        try:
            # Playwright 초기화
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=self.config.args
            )
            
            # 새 페이지 생성 (🚀 성능 최적화 적용)
            context_options = {
                "user_agent": self.config.user_agent,
                "viewport": {
                    "width": self.config.viewport_width, 
                    "height": self.config.viewport_height
                },
                # 🚀 성능 최적화 설정
                "bypass_csp": True,                    # CSP 우회로 빠른 로딩
                "ignore_https_errors": True,           # HTTPS 오류 무시
                "java_script_enabled": True,           # JS는 필요
                "extra_http_headers": {
                    "Cache-Control": "no-cache",       # 일관된 결과
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"
                }
            }
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            # 🚀 리소스 차단 설정
            await self._setup_resource_blocking()
            
            # aiohttp 세션 생성
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout / 1000),
                headers={
                    'User-Agent': self.config.user_agent
                }
            )
            
            self.is_running = True
            
        except Exception as e:
            await self.cleanup()
            raise RuntimeError(f"Playwright 초기화 실패: {e}")
            
    async def cleanup(self):
        """리소스 정리"""
        self.is_running = False
        
        if self.session:
            await self.session.close()
            
        if self.page:
            await self.page.close()
            
        if self.context:
            await self.context.close()
            
        if self.browser:
            await self.browser.close()
            
        if self.playwright:
            await self.playwright.stop()
    
    async def _setup_resource_blocking(self):
        """🚀 리소스 차단 설정 (성능 최적화)"""
        if not self.page:
            return
            
        # 이미지 차단
        if self.config.block_images:
            await self.page.route("**/*.{png,jpg,jpeg,gif,svg,webp,ico}", lambda route: route.abort())
            
        # CSS 차단 (필요시에만)
        if self.config.block_css:
            await self.page.route("**/*.css", lambda route: route.abort())
            
        # 광고 차단
        if self.config.block_ads:
            await self.page.route("**/ads/**", lambda route: route.abort())
            await self.page.route("**/ad/**", lambda route: route.abort())
            await self.page.route("**/*googleads*", lambda route: route.abort())
            await self.page.route("**/*doubleclick*", lambda route: route.abort())
            
        # 분석 스크립트 차단
        if self.config.block_analytics:
            await self.page.route("**/analytics/**", lambda route: route.abort())
            await self.page.route("**/*google-analytics*", lambda route: route.abort())
            await self.page.route("**/*gtag*", lambda route: route.abort())
            await self.page.route("**/*facebook.com/tr*", lambda route: route.abort())

    async def goto(self, url: str, wait_until: str = "networkidle", timeout: Optional[int] = None) -> None:
        """페이지 이동 (기본)"""
        if not self.is_running or not self.page:
            raise RuntimeError("Playwright가 초기화되지 않았습니다.")
            
        timeout = timeout or self.config.timeout
        await self.page.goto(url, wait_until=wait_until, timeout=timeout)
    
    async def goto_fast(self, url: str, timeout: Optional[int] = None) -> None:
        """🚀 빠른 페이지 이동 (domcontentloaded 사용)"""
        if not self.is_running or not self.page:
            raise RuntimeError("Playwright가 초기화되지 않았습니다.")
            
        timeout = timeout or (self.config.timeout // 2)  # 절반 시간
        await self.page.goto(url, wait_until='domcontentloaded', timeout=timeout)
    
    async def goto_instant(self, url: str, timeout: Optional[int] = None) -> None:
        """⚡ 즉시 페이지 이동 (commit 사용 - 가장 빠름)"""
        if not self.is_running or not self.page:
            raise RuntimeError("Playwright가 초기화되지 않았습니다.")
            
        timeout = timeout or (self.config.timeout // 3)  # 1/3 시간
        await self.page.goto(url, wait_until='commit', timeout=timeout)
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> None:
        """셀렉터 대기"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        timeout = timeout or self.config.timeout
        await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def query_selector_all(self, selector: str) -> List:
        """모든 요소 선택"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        return await self.page.query_selector_all(selector)
    
    async def query_selector(self, selector: str):
        """단일 요소 선택"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        return await self.page.query_selector(selector)
    
    async def get_content(self) -> str:
        """페이지 컨텐츠 가져오기"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        return await self.page.content()
    
    async def evaluate(self, expression: str) -> Any:
        """JavaScript 실행"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        return await self.page.evaluate(expression)
    
    async def locator(self, selector: str):
        """로케이터 반환"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        return self.page.locator(selector)
    
    async def screenshot(self, path: str, full_page: bool = False) -> None:
        """스크린샷 저장"""
        if not self.page:
            raise RuntimeError("페이지가 초기화되지 않았습니다.")
            
        await self.page.screenshot(path=path, full_page=full_page)
    
    async def http_get(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """HTTP GET 요청"""
        if not self.session:
            raise RuntimeError("HTTP 세션이 초기화되지 않았습니다.")
            
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP 요청 실패 - Status: {response.status}, Error: {error_text}")
        except Exception as e:
            raise Exception(f"HTTP GET 실패: {e}")
    
    async def http_post(self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """HTTP POST 요청"""
        if not self.session:
            raise RuntimeError("HTTP 세션이 초기화되지 않았습니다.")
            
        try:
            async with self.session.post(url, data=data, json=json) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP 요청 실패 - Status: {response.status}, Error: {error_text}")
        except Exception as e:
            raise Exception(f"HTTP POST 실패: {e}")


# 편의 함수들
async def create_playwright_helper(config: Optional[BrowserConfig] = None) -> PlaywrightHelper:
    """PlaywrightHelper 인스턴스 생성 및 초기화"""
    helper = PlaywrightHelper(config)
    await helper.initialize()
    return helper


def get_default_browser_config(headless: bool = True) -> BrowserConfig:
    """기본 브라우저 설정 반환"""
    return BrowserConfig(headless=headless)


def get_fast_browser_config(headless: bool = True) -> BrowserConfig:
    """🚀 빠른 브라우저 설정 반환 (최대 성능 최적화)"""
    return BrowserConfig(
        headless=headless,
        block_images=True,      # 이미지 차단
        block_css=False,        # CSS는 레이아웃을 위해 유지
        block_ads=True,         # 광고 차단
        block_analytics=True,   # 분석 스크립트 차단
        fast_loading=True,      # 빠른 로딩 모드
        timeout=15000           # 타임아웃 단축 (15초)
    )


def get_ultra_fast_browser_config(headless: bool = True) -> BrowserConfig:
    """⚡ 초고속 브라우저 설정 반환 (극한 최적화 - CSS도 차단)"""
    return BrowserConfig(
        headless=headless,
        block_images=True,      # 이미지 차단
        block_css=True,         # CSS도 차단 (레이아웃 무시)
        block_ads=True,         # 광고 차단
        block_analytics=True,   # 분석 스크립트 차단
        fast_loading=True,      # 빠른 로딩 모드
        timeout=10000           # 타임아웃 대폭 단축 (10초)
    )


# 상수 정의
DEFAULT_USER_AGENTS = {
    'chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
}


def get_user_agent(browser_type: str = 'chrome') -> str:
    """브라우저별 User-Agent 반환"""
    return DEFAULT_USER_AGENTS.get(browser_type, DEFAULT_USER_AGENTS['chrome'])