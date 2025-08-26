import os

def final_fix():
    python_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # 이중 괄호 패턴들 수정
            content = content.replace('))', ')')
            
            if content != original:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed double brackets in {file_path}')
            
        except Exception as e:
            print(f'Error: {e}')

if __name__ == "__main__":
    final_fix()
    print("최종 수정 완료")