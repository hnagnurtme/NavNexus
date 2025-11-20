#!/usr/bin/env python3
"""Analyze Python imports and identify issues"""

import os
import ast
import sys
from pathlib import Path
from collections import defaultdict

def extract_imports(file_path):
    """Extract all imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'type': 'from',
                        'module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno
                    })

        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def find_python_files(root_dir):
    """Find all Python files in directory"""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.venv' and d != 'venv']

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return python_files

def check_module_exists(module_path, base_dir):
    """Check if a local module exists"""
    # Convert module path to file path
    parts = module_path.split('.')

    # Try as package
    package_path = os.path.join(base_dir, *parts, '__init__.py')
    if os.path.exists(package_path):
        return True

    # Try as module
    module_file = os.path.join(base_dir, *parts[:-1], f"{parts[-1]}.py")
    if os.path.exists(module_file):
        return True

    return False

def analyze_imports(root_dir):
    """Analyze all imports in the codebase"""
    python_files = find_python_files(root_dir)

    results = {
        'files_analyzed': len(python_files),
        'missing_modules': defaultdict(list),
        'all_imports': defaultdict(list),
        'local_imports': defaultdict(list),
    }

    for file_path in python_files:
        rel_path = os.path.relpath(file_path, root_dir)
        imports = extract_imports(file_path)

        for imp in imports:
            if imp['type'] == 'from':
                full_name = f"{imp['module']}.{imp['name']}" if imp['module'] else imp['name']
            else:
                full_name = imp['module']

            results['all_imports'][rel_path].append((full_name, imp['line']))

            # Check if it's a local import (starts with src or relative)
            if imp['module'] and (imp['module'].startswith('src') or imp['module'].startswith('.')):
                results['local_imports'][rel_path].append((full_name, imp['line']))

                # Check if module exists
                if imp['module'].startswith('src'):
                    module_parts = imp['module'].split('.')
                    if imp['type'] == 'from':
                        # Check if the imported name is a module or function
                        check_path = imp['module'].replace('.', '/')
                        module_file = os.path.join(root_dir, f"{check_path}.py")

                        if not os.path.exists(module_file):
                            # Check as package
                            package_path = os.path.join(root_dir, check_path, '__init__.py')
                            if not os.path.exists(package_path):
                                results['missing_modules'][rel_path].append({
                                    'import': full_name,
                                    'line': imp['line'],
                                    'module': imp['module'],
                                    'name': imp['name']
                                })

    return results

def main():
    root_dir = '/Users/anhnon/NavNexus/RabbitMQ'

    print("="*80)
    print("ANALYZING PYTHON IMPORTS")
    print("="*80)

    results = analyze_imports(root_dir)

    print(f"\nFiles analyzed: {results['files_analyzed']}")

    # Report missing modules
    print("\n" + "="*80)
    print("MISSING MODULES (Import Errors)")
    print("="*80)

    if results['missing_modules']:
        for file_path, missing in results['missing_modules'].items():
            if missing:
                print(f"\n📄 {file_path}:")
                for item in missing:
                    print(f"  Line {item['line']}: from {item['module']} import {item['name']}")
    else:
        print("\n✓ No missing modules detected")

    # Show key files and their imports
    print("\n" + "="*80)
    print("KEY FILES IMPORTS")
    print("="*80)

    key_files = ['worker.py', 'worker_enhanced.py', 'src/pipeline/main_pipeline.py']
    for key_file in key_files:
        if key_file in results['local_imports']:
            print(f"\n📄 {key_file}:")
            for imp, line in results['local_imports'][key_file]:
                print(f"  Line {line}: {imp}")

if __name__ == '__main__':
    main()
