#!/usr/bin/env python3
"""Analyze code usage and identify dead code"""

import os
import ast
from pathlib import Path
from collections import defaultdict

def extract_definitions(file_path):
    """Extract all function and class definitions"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)

        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                definitions.append({
                    'type': 'function',
                    'name': node.name,
                    'line': node.lineno,
                    'is_private': node.name.startswith('_'),
                })
            elif isinstance(node, ast.ClassDef):
                definitions.append({
                    'type': 'class',
                    'name': node.name,
                    'line': node.lineno,
                    'is_private': node.name.startswith('_'),
                })

        return definitions
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

def extract_function_calls(file_path):
    """Extract all function calls"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)

        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.add(node.func.attr)

        return calls
    except Exception as e:
        return set()

def find_python_files(root_dir):
    """Find all Python files"""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.venv' and d != 'venv']
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_usage():
    """Analyze function usage across codebase"""
    root_dir = '/Users/anhnon/NavNexus/RabbitMQ'
    python_files = find_python_files(root_dir)

    # Track all definitions
    all_definitions = defaultdict(list)
    all_calls = set()

    for file_path in python_files:
        rel_path = os.path.relpath(file_path, root_dir)

        # Get definitions
        definitions = extract_definitions(file_path)
        for defn in definitions:
            all_definitions[defn['name']].append({
                'file': rel_path,
                'line': defn['line'],
                'type': defn['type'],
                'is_private': defn['is_private']
            })

        # Get calls
        calls = extract_function_calls(file_path)
        all_calls.update(calls)

    # Find unused definitions
    unused = {}
    for name, locations in all_definitions.items():
        # Skip private functions and special methods
        if name.startswith('_') or name == 'main':
            continue

        if name not in all_calls:
            unused[name] = locations

    return all_definitions, all_calls, unused

def main():
    print("="*80)
    print("CODE USAGE ANALYSIS")
    print("="*80)

    all_defs, all_calls, unused = analyze_usage()

    # Show unused functions
    print("\n" + "="*80)
    print("POTENTIALLY UNUSED FUNCTIONS/CLASSES")
    print("="*80)

    if unused:
        for name, locations in sorted(unused.items()):
            print(f"\n❌ {name} ({locations[0]['type']})")
            for loc in locations:
                print(f"  📄 {loc['file']}:{loc['line']}")
    else:
        print("\n✓ All public functions appear to be used")

    # Show duplicate function names
    print("\n" + "="*80)
    print("DUPLICATE FUNCTION NAMES (Potential Conflicts)")
    print("="*80)

    duplicates = {name: locs for name, locs in all_defs.items() if len(locs) > 1 and not name.startswith('_')}
    if duplicates:
        for name, locations in sorted(duplicates.items()):
            print(f"\n⚠️  {name} (defined {len(locations)} times)")
            for loc in locations:
                print(f"  📄 {loc['file']}:{loc['line']} ({loc['type']})")
    else:
        print("\n✓ No duplicate function names found")

    # Check specific pipeline functions
    print("\n" + "="*80)
    print("PIPELINE FUNCTION AVAILABILITY")
    print("="*80)

    required_functions = [
        'extract_hierarchical_structure_compact',
        'process_chunks_ultra_compact',
        'create_hierarchical_graph_with_cascading_dedup',
        'extract_merge_optimized_structure',
        'analyze_chunks_for_merging',
        'create_hierarchical_knowledge_graph',
    ]

    for func_name in required_functions:
        if func_name in all_defs:
            locs = all_defs[func_name]
            print(f"\n✓ {func_name}")
            for loc in locs:
                print(f"  📄 {loc['file']}:{loc['line']}")
        else:
            print(f"\n❌ {func_name} - NOT FOUND")

if __name__ == '__main__':
    main()
