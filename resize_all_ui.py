#!/usr/bin/env python3
"""
AxCrypt UI Auto-Resizer
=======================
Automatically makes all UI elements 60% larger for better readability.

Usage:
    python resize_all_ui.py

This will update all UI files in place with larger fonts and spacing.
"""

import re
import os
import shutil
from pathlib import Path

# 60% size increase
SCALE = 1.6

FILES_TO_UPDATE = [
    'ui/dashboard.py',
    'ui/encrypt_panel.py',
    'ui/decrypt_panel.py',
    'ui/history_panel.py',
    'ui/settings_panel.py',
    'ui/lock_panel.py',
    'ui/widgets.py',
    'ui/app.py',
]

def backup_files():
    """Create backups before modification"""
    backup_dir = Path('ui_backups_original')
    backup_dir.mkdir(exist_ok=True)
    
    for filepath in FILES_TO_UPDATE:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            shutil.copy2(filepath, backup_dir / filename)
            print(f'📦 Backed up {filepath}')
    
    print(f'\n✓ Backups saved to {backup_dir}/\n')

def scale_font(match):
    """Scale font sizes by SCALE factor"""
    font_name = match.group(1)
    size = int(match.group(2))
    rest = match.group(3)
    new_size = max(12, int(size * SCALE))  # Minimum 12px
    return f'font=("{font_name}", {new_size}{rest})'

def scale_size(match):
    """Scale dimensions by SCALE factor"""
    param = match.group(1)
    value = int(match.group(2))
    new_value = int(value * SCALE)
    return f'{param}={new_value}'

def scale_tuple_font(match):
    """Scale tuple-style fonts: ("Segoe UI", 11)"""
    font_name = match.group(1)
    size = int(match.group(2))
    rest = match.group(3)
    new_size = max(12, int(size * SCALE))
    return f'("{font_name}", {new_size}{rest})'

def update_file(filepath):
    """Update a single file with scaled sizes"""
    if not os.path.exists(filepath):
        print(f'⚠ Skipping {filepath} (not found)')
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Scale font= parameters
    content = re.sub(
        r'font=\("([^"]+)",\s*(\d+)((?:,\s*"[^"]*")?)\)',
        scale_font,
        content
    )
    
    # Scale tuple fonts in variables
    content = re.sub(
        r'\("([^"]+)",\s*(\d+)((?:,\s*"[^"]*")?)\)',
        scale_tuple_font,
        content
    )
    
    # Scale width, height, padx, pady, ipadx, ipady
    for param in ['width', 'height', 'padx', 'pady', 'ipadx', 'ipady']:
        content = re.sub(
            rf'\b({param})=(\d+)\b',
            scale_size,
            content
        )
    
    # Scale resize() calls for images
    content = re.sub(
        r'resize\((\d+),\s*(\d+)\)',
        lambda m: f'resize({int(int(m.group(1)) * SCALE)}, {int(int(m.group(2)) * SCALE)})',
        content
    )
    
    # Write back only if changed
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'✓ Updated {filepath}')
    else:
        print(f'= No changes needed for {filepath}')

def main():
    print('🎨 AxCrypt UI Auto-Resizer')
    print('=' * 50)
    print(f'Scale factor: {SCALE}x ({int((SCALE-1)*100)}% larger)\n')
    
    # Backup first
    backup_files()
    
    # Update each file
    for filepath in FILES_TO_UPDATE:
        update_file(filepath)
    
    print('\n' + '=' * 50)
    print('🎉 Resize complete!')
    print('\nNext steps:')
    print('1. Restart your AxCrypt app')
    print('2. Check if sizes look good')
    print('3. If too large, restore from ui_backups_original/')
    print('4. If too small, increase SCALE in this script')

if __name__ == '__main__':
    main()