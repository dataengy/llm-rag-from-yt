#!/usr/bin/env python3
"""
Script to update all import references after moving modules to _common.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path: Path):
    """Update imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update imports from moved modules
        replacements = [
            # Logging imports
            (r'from \.\.logging import', 'from .._common.logging import'),
            (r'from \.logging import', 'from ._common.logging import'),
            (r'from llm_rag_yt\.logging import', 'from llm_rag_yt._common.logging import'),
            
            # Config imports  
            (r'from \.\.config\.settings import', 'from .._common.config.settings import'),
            (r'from \.config\.settings import', 'from ._common.config.settings import'),
            (r'from llm_rag_yt\.config\.settings import', 'from llm_rag_yt._common.config.settings import'),
            
            # Utils imports
            (r'from \.\.utils import', 'from .._common.utils import'),
            (r'from \.utils import', 'from ._common.utils import'), 
            (r'from llm_rag_yt\.utils import', 'from llm_rag_yt._common.utils import'),
            
            # Direct imports from _common
            (r'from llm_rag_yt\._common import', 'from llm_rag_yt._common import'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Main function to update all imports."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    updated_files = []
    
    # Find all Python files in src directory
    for py_file in src_dir.rglob("*.py"):
        if update_imports_in_file(py_file):
            updated_files.append(py_file)
    
    # Also update test files
    test_dir = project_root / "tests"
    if test_dir.exists():
        for py_file in test_dir.rglob("*.py"):
            if update_imports_in_file(py_file):
                updated_files.append(py_file)
    
    # Update scripts
    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.rglob("*.py"):
            if update_imports_in_file(py_file):
                updated_files.append(py_file)
    
    # Update examples
    examples_dir = project_root / "examples"
    if examples_dir.exists():
        for py_file in examples_dir.rglob("*.py"):
            if update_imports_in_file(py_file):
                updated_files.append(py_file)
    
    print(f"\nUpdated {len(updated_files)} files:")
    for file_path in updated_files:
        print(f"  - {file_path.relative_to(project_root)}")

if __name__ == "__main__":
    main()