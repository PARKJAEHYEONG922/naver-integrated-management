import re
import os

# 전체 프로젝트에서 ResponsiveUI 제거
def remove_responsive_ui():
    # src 디렉터리에서 모든 Python 파일 찾기
    python_files = []
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # ResponsiveUI 패턴들 모두 제거/치환
            patterns = [
                (r'ResponsiveUI\.scale\((\d+)\)', r'\1'),
                (r'ResponsiveUI\.get_font_size_pt\([\'"]normal[\'"]\)', r'14'),
                (r'ResponsiveUI\.get_font_size_pt\([\'"]small[\'"]\)', r'12'),
                (r'ResponsiveUI\.get_font_size_pt\([\'"]large[\'"]\)', r'16'),
                (r'ResponsiveUI\.get_font_size_pt\([\'"]header[\'"]\)', r'18'),
                (r'ResponsiveUI\.get_font_size_pt\([\'"]title[\'"]\)', r'20'),
                (r'layout\.setSpacing\((\d+)\)', r'layout.setSpacing(\1)'),
                (r'header\.resizeSection\(\d+,\s*(\d+)', r'header.resizeSection(\g<0>, \1'),
                # 괄호 문제들
                (r'(\w+)\s*=\s*(\d+)\)', r'\1 = \2'),
                (r'setFixedHeight\((\d+)\)', r'setFixedHeight(\1)'),
                (r'setFixedWidth\((\d+)\)', r'setFixedWidth(\1)'),
                (r'setSpacing\((\d+)\)', r'setSpacing(\1)'),
                # import 제거
                (r'from src\.toolbox\.ui_kit\.responsive import ResponsiveUI\n', r''),
                (r'from src\.toolbox\.ui_kit import.*ResponsiveUI.*\n', r''),
                # 스타일 패턴 수정
                (r'padding:\s*\{(\d+)\}px\s*\{(\d+)\}px;', r'padding: \1px \2px;'),
                (r'margin:\s*\{(\d+)\}px\s*\{(\d+)\}px;', r'margin: \1px \2px;'),
                (r'border-radius:\s*\{(\d+)\}px;', r'border-radius: \1px;'),
                (r'font-size:\s*\{(\d+)\}px;', r'font-size: \1px;'),
                (r'min-height:\s*\{(\d+)\}px;', r'min-height: \1px;'),
                (r'max-width:\s*\{(\d+)\}px;', r'max-width: \1px;'),
                (r'width:\s*\{(\d+)\}px;', r'width: \1px;'),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            # 이중 괄호 제거
            content = re.sub(r'\)\)', r')', content)
            
            if content != original:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed {file_path}')
            
        except Exception as e:
            print(f'Error in {file_path}: {e}')

    print("ResponsiveUI 완전 제거 완료")

if __name__ == "__main__":
    remove_responsive_ui()