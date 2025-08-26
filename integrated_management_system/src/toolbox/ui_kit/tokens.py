"""
디스코드 스타일 디자인 토큰
업계 표준 방식: 고정 px 값 + OS DPI 자동 처리
"""

# ---- Typography (px) --------------------------------------------------------
FONT_TITLE  = 20
FONT_HEADER = 18
FONT_LARGE  = 16
FONT_NORMAL = 14
FONT_SMALL  = 12
FONT_TINY   = 11

# 선택: 접근성용 가변 배율 (원하면 1.0 고정)
USER_TEXT_SCALE = 1.0
def fpx(v: int) -> int:
    """접근성 옵션 적용된 폰트 px 반환"""
    return int(round(v * USER_TEXT_SCALE))

# ---- Spacing / Sizing (px) --------------------------------------------------
GAP_1  = 1
GAP_2  = 2
GAP_3  = 3
GAP_4  = 4
GAP_5  = 5
GAP_6  = 6
GAP_8  = 8
GAP_10 = 10
GAP_12 = 12
GAP_14 = 14
GAP_15 = 15
GAP_16 = 16
GAP_18 = 18
GAP_20 = 20
GAP_24 = 24
GAP_28 = 28
GAP_32 = 32
GAP_36 = 36
GAP_40 = 40
GAP_48 = 48
GAP_50 = 50
GAP_56 = 56
GAP_60 = 60
GAP_64 = 64
GAP_72 = 72
GAP_80 = 80
GAP_96 = 96
GAP_110 = 110
GAP_120 = 120
GAP_130 = 130
GAP_140 = 140
GAP_150 = 150

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 12

BTN_H_SM = 22
BTN_H_MD = 32
BTN_H_LG = 40

ICON_SM = 16
ICON_MD = 20
ICON_LG = 24

BORDER_1 = 1
BORDER_2 = 2

# ---- Color (Light Theme) - 현재 ModernStyle 색상 기준 ---------------------
# 필요하면 나중에 DARK_* 세트 추가해서 테마 스위치 가능
COLOR_BG_PRIMARY   = "#ffffff"
COLOR_BG_SECONDARY = "#f8fafc"
COLOR_BG_TERTIARY  = "#e2e8f0"  # 추가된 색상
COLOR_BG_CARD      = "#ffffff"
COLOR_BG_INPUT     = "#f1f5f9"
COLOR_BG_MUTED     = "#e2e8f0"  # 추가된 색상

COLOR_TEXT_PRIMARY   = "#1e293b"
COLOR_TEXT_SECONDARY = "#64748b"
COLOR_TEXT_TERTIARY  = "#94a3b8"  # 추가된 색상
COLOR_TEXT_MUTED     = "#94a3b8"

COLOR_BORDER  = "#e2e8f0"
COLOR_SHADOW  = "rgba(15, 23, 42, 0.1)"  # 추가된 색상

# 메인 색상들
COLOR_PRIMARY = "#2563eb"  # 파랑
COLOR_SUCCESS = "#10b981"  # 초록
COLOR_WARNING = "#f59e0b"  # 주황
COLOR_DANGER  = "#ef4444"  # 빨강
COLOR_INFO    = "#3b82f6"  # 정보

# 호버 색상들 (더 진한 버전)
COLOR_PRIMARY_HOVER = "#1d4ed8"  # 파랑 호버
COLOR_SUCCESS_HOVER = "#059669"  # 초록 호버
COLOR_WARNING_HOVER = "#d97706"  # 주황 호버
COLOR_DANGER_HOVER  = "#dc2626"  # 빨강 호버
COLOR_INFO_HOVER    = "#2563eb"  # 정보 호버

# 눌림 색상들 (가장 진한 버전)
COLOR_PRIMARY_PRESSED = "#1e40af"  # 파랑 눌림
COLOR_SUCCESS_PRESSED = "#047857"  # 초록 눌림
COLOR_WARNING_PRESSED = "#b45309"  # 주황 눌림
COLOR_DANGER_PRESSED  = "#b91c1c"  # 빨강 눌림
COLOR_INFO_PRESSED    = "#1d4ed8"  # 정보 눌림

# ---- Shadow / Elevation -----------------------------------------------------
SHADOW_CARD = "0px 2px 8px rgba(15, 23, 42, 0.1)"
SHADOW_POP  = "0px 8px 24px rgba(15, 23, 42, 0.15)"

# ---- Motion -----------------------------------------------------------------
DUR_FAST = 120   # ms
DUR_BASE = 180
DUR_SLOW = 260
EASE_OUT = "cubic-bezier(0.16, 1, 0.3, 1)"

# ---- 편의 함수들 -------------------------------------------------------------
def get_font_size(size_name: str = 'normal') -> int:
    """폰트 크기 반환 (접근성 배율 적용)"""
    sizes = {
        'title': FONT_TITLE,
        'header': FONT_HEADER,
        'large': FONT_LARGE,
        'normal': FONT_NORMAL,
        'small': FONT_SMALL,
        'tiny': FONT_TINY
    }
    return fpx(sizes.get(size_name, FONT_NORMAL))

def get_spacing(size_name: str = 'md') -> int:
    """간격 반환"""
    spacings = {
        'xs': GAP_2,
        'sm': GAP_4,
        'md': GAP_6,
        'lg': GAP_10,
        'xl': GAP_16,
        'xxl': GAP_20
    }
    return spacings.get(size_name, GAP_6)

def get_radius(size_name: str = 'md') -> int:
    """반지름 반환"""
    radius = {
        'sm': RADIUS_SM,
        'md': RADIUS_MD,
        'lg': RADIUS_LG
    }
    return radius.get(size_name, RADIUS_MD)

# ---- 하위 호환성을 위한 별칭 ------------------------------------------------
# 기존 코드에서 바로 사용할 수 있도록
COLORS = {
    'primary': COLOR_PRIMARY,
    'primary_hover': COLOR_PRIMARY_HOVER,
    'primary_pressed': COLOR_PRIMARY_PRESSED,
    
    'secondary': COLOR_SUCCESS,  # secondary는 success와 동일
    'secondary_hover': COLOR_SUCCESS_HOVER,
    'secondary_pressed': COLOR_SUCCESS_PRESSED,
    
    'success': COLOR_SUCCESS,
    'success_hover': COLOR_SUCCESS_HOVER,
    'success_pressed': COLOR_SUCCESS_PRESSED,
    
    'warning': COLOR_WARNING,
    'warning_hover': COLOR_WARNING_HOVER,
    'warning_pressed': COLOR_WARNING_PRESSED,
    
    'danger': COLOR_DANGER,
    'danger_hover': COLOR_DANGER_HOVER,
    'danger_pressed': COLOR_DANGER_PRESSED,
    
    'info': COLOR_INFO,
    'info_hover': COLOR_INFO_HOVER,
    'info_pressed': COLOR_INFO_PRESSED,
    
    'bg_primary': COLOR_BG_PRIMARY,
    'bg_secondary': COLOR_BG_SECONDARY,
    'bg_tertiary': COLOR_BG_TERTIARY,
    'bg_card': COLOR_BG_CARD,
    'bg_input': COLOR_BG_INPUT,
    'bg_muted': COLOR_BG_MUTED,
    
    'text_primary': COLOR_TEXT_PRIMARY,
    'text_secondary': COLOR_TEXT_SECONDARY,
    'text_tertiary': COLOR_TEXT_TERTIARY,
    'text_muted': COLOR_TEXT_MUTED,
    
    'border': COLOR_BORDER,
    'shadow': COLOR_SHADOW
}