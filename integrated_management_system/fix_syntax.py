import re
import os

# features 디렉터리에서 모든 Python 파일 찾기
features_path = "src/features"
python_files = []
for root, dirs, files in os.walk(features_path):
    for file in files:
        if file.endswith('.py'):
            python_files.append(os.path.join(root, file))

for file_path in python_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 패턴 수정
        content = re.sub(r'setFixedHeight\((\d+)\)\)', r'setFixedHeight(\1)', content)
        content = re.sub(r'setFixedWidth\((\d+)\)\)', r'setFixedWidth(\1)', content) 
        content = re.sub(r'setSpacing\((\d+)\)\)', r'setSpacing(\1)', content)
        content = re.sub(r'(\w+) = (\d+)\)', r'\1 = \2', content)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed {file_path}')
        
    except Exception as e:
        print(f'Error in {file_path}: {e}')

print("구문 수정 완료")