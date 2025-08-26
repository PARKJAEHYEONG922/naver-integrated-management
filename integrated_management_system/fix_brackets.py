import re
import os

# 괄호 문제 수정
def fix_bracket_issues():
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
            
            # 괄호 문제들 수정
            patterns = [
                # 함수 호출에서 닫는 괄호 누락
                (r'\.setStyleSheet\([^)]*$', lambda m: m.group(0) + ')'),
                (r'\.setText\([^)]*$', lambda m: m.group(0) + ')'),
                (r'\.move\([^)]*$', lambda m: m.group(0) + ')'),
                (r'\.exec\([^)]*$', lambda m: m.group(0) + ')'),
                (r'\.connect\([^)]*$', lambda m: m.group(0) + ')'),
                (r'\.setSizes\([^)]*$', lambda m: m.group(0) + ')'),
                (r'ErrorWidget\([^)]*$', lambda m: m.group(0) + ')'),
                (r'\.replace\([^)]*$', lambda m: m.group(0) + ')'),
                # range 함수
                (r'range\(len\([^)]*\):', r'range(len(\g<1>)):'),
                # setSpacing, setFixedHeight 등
                (r'layout\.setSpacing\((\d+)([^)])', r'layout.setSpacing(\1)'),
                (r'\.setFixedHeight\((\d+)([^)])', r'.setFixedHeight(\1)'),
                # 기타 함수 호출들
                (r'get_placeholder_title_style\(\)', r'get_placeholder_title_style()'),
                (r'get_placeholder_description_style\(\)', r'get_placeholder_description_style()'),
                (r'get_placeholder_module_id_style\(\)', r'get_placeholder_module_id_style()'),
                (r'get_error_widget_style\(\)', r'get_error_widget_style()'),
                (r'get_content_stack_style\(\)', r'get_content_stack_style()'),
                (r'get_content_log_ratio\(\)', r'get_content_log_ratio()'),
                (r'get_button_style\(\'[^\']*\'\)', lambda m: m.group(0)),
                (r'get_input_style\(\)', r'get_input_style()'),
                # QTableWidgetItem 등
                (r'QTableWidgetItem\(([^)]+)\)', r'QTableWidgetItem(\1)'),
                # 변수 할당 괄호 문제
                (r'(\w+) = ([^=\n]+)\)', r'\1 = \2'),
                # 기타 일반적인 괄호 문제들
                (r'\)\)([^)])', r')\1'),
            ]
            
            for pattern, replacement in patterns:
                if callable(replacement):
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                else:
                    content = re.sub(pattern, replacement, content)
            
            # 수동으로 자주 발생하는 문제들 수정
            specific_fixes = [
                # topLeft() 등
                ('self.move(window_rect.topLeft(', 'self.move(window_rect.topLeft())'),
                ('app.exec(', 'app.exec())'),
                ('styleSheet(', 'styleSheet())'),
                # header.resizeSection 수정
                ('header.resizeSection(header.resizeSection(', 'header.resizeSection('),
                # for loop 수정  
                ('for idx, kw in enumerate(keywords, start = 1:', 'for idx, kw in enumerate(keywords, start=1):'),
                ('range(self.results_tree.columnCount(:', 'range(self.results_tree.columnCount()):'),
                ('range(self.results_tree.topLevelItemCount(', 'range(self.results_tree.topLevelItemCount())'),
                ('if not (result and hasattr(result, \'keywords\':', 'if not (result and hasattr(result, \'keywords\')):'),
                ('self.progress_bar.setMaximum(len(unique_keywords)', 'self.progress_bar.setMaximum(len(unique_keywords))'),
            ]
            
            for old, new in specific_fixes:
                content = content.replace(old, new)
            
            if content != original:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed brackets in {file_path}')
            
        except Exception as e:
            print(f'Error fixing {file_path}: {e}')

    print("괄호 수정 완료")

if __name__ == "__main__":
    fix_bracket_issues()