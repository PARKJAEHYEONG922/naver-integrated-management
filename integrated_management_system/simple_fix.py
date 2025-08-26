import os

# 간단한 문자열 치환으로 수정
def simple_fix():
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
            
            # 간단한 치환들
            replacements = [
                ('self.move(window_rect.topLeft(', 'self.move(window_rect.topLeft())'),
                ('app.exec(', 'app.exec())'),
                ('layout.setSpacing(15', 'layout.setSpacing(15)'),
                ('layout.setSpacing(12', 'layout.setSpacing(12)'),
                ('layout.setSpacing(10', 'layout.setSpacing(10)'),
                ('layout.setSpacing(8', 'layout.setSpacing(8)'),
                ('layout.setSpacing(6', 'layout.setSpacing(6)'),
                ('self.setFixedHeight(15', 'self.setFixedHeight(15)'),
                ('self.setFixedHeight(35', 'self.setFixedHeight(35)'),
                ('self.setFixedHeight(140', 'self.setFixedHeight(140)'),
                ('button.clicked.connect(lambda: self.switch_to_page(page_id)', 'button.clicked.connect(lambda: self.switch_to_page(page_id))'),
                ('.setStyleSheet(AppStyles.get_placeholder_title_style(', '.setStyleSheet(AppStyles.get_placeholder_title_style())'),
                ('.setStyleSheet(AppStyles.get_placeholder_description_style(', '.setStyleSheet(AppStyles.get_placeholder_description_style())'),
                ('.setStyleSheet(AppStyles.get_placeholder_module_id_style(', '.setStyleSheet(AppStyles.get_placeholder_module_id_style())'),
                ('.setStyleSheet(AppStyles.get_error_widget_style(', '.setStyleSheet(AppStyles.get_error_widget_style())'),
                ('.setStyleSheet(AppStyles.get_content_stack_style(', '.setStyleSheet(AppStyles.get_content_stack_style())'),
                ('.setSizes(WindowConfig.get_content_log_ratio(', '.setSizes(WindowConfig.get_content_log_ratio())'),
                ('return ErrorWidget(str(e)', 'return ErrorWidget(str(e))'),
                ('return title_map.get(title, title.lower().replace(\' \', \'_\')', 'return title_map.get(title, title.lower().replace(\' \', \'_\'))'),
                # ModernStyle 관련
                ('.setStyleSheet(ModernStyle.get_button_style(\'primary\')', '.setStyleSheet(ModernStyle.get_button_style(\'primary\'))'),
                ('.setStyleSheet(ModernStyle.get_button_style(\'secondary\')', '.setStyleSheet(ModernStyle.get_button_style(\'secondary\'))'),
                ('.setStyleSheet(ModernStyle.get_button_style(\'danger\')', '.setStyleSheet(ModernStyle.get_button_style(\'danger\'))'),
                ('.setStyleSheet(ModernStyle.get_button_style(\'outline\')', '.setStyleSheet(ModernStyle.get_button_style(\'outline\'))'),
                ('.setStyleSheet(ModernStyle.get_input_style(', '.setStyleSheet(ModernStyle.get_input_style())'),
                ('.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL)', '.setFont(QFont(ModernStyle.DEFAULT_FONT, ModernStyle.FONT_SIZE_NORMAL))'),
                # 기타
                ('for i in range(self.results_tree.columnCount(:', 'for i in range(self.results_tree.columnCount()):'),
                ('for i in range(self.results_tree.topLevelItemCount(', 'for i in range(self.results_tree.topLevelItemCount())'),
                ('self.progress_bar.setMaximum(len(unique_keywords)', 'self.progress_bar.setMaximum(len(unique_keywords))'),
                ('for i in range(len(self.progress_steps):', 'for i in range(len(self.progress_steps)):'),
                ('if not (result and hasattr(result, \'keywords\':', 'if not (result and hasattr(result, \'keywords\')):'),
                ('for idx, kw in enumerate(keywords, start = 1:', 'for idx, kw in enumerate(keywords, start=1):'),
                # QTableWidgetItem
                ('QTableWidgetItem(str(row + 1)', 'QTableWidgetItem(str(row + 1))'),
                ('QTableWidgetItem(user.user_id)', 'QTableWidgetItem(user.user_id)'),
                ('QTableWidgetItem(user.nickname)', 'QTableWidgetItem(user.nickname)'),
                # 스타일 딕셔너리 수정
                ('\'category\': max(200, int(base_width * 1.3),', '\'category\': max(200, int(base_width * 1.3)),'),
                ('\'volume\': max(100, int(base_width * 0.7),', '\'volume\': max(100, int(base_width * 0.7)),'),
                ('\'products\': max(100, int(base_width * 0.7),', '\'products\': max(100, int(base_width * 0.7)),'),
                ('\'strength\': max(100, int(base_width * 0.7)', '\'strength\': max(100, int(base_width * 0.7))'),
            ]
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            if content != original:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Fixed {file_path}')
            
        except Exception as e:
            print(f'Error: {e}')

if __name__ == "__main__":
    simple_fix()
    print("간단한 수정 완료")