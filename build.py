#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Build script for AutoLabel Deluge Plugin
# Builds Python egg files for all available Python versions
#

import os
import subprocess
import sys
from shutil import which

# Python versions to try building for
PYTHON_VERSIONS = ['3.6', '3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13', '3.14']


def find_python_executables():
    """Find all available Python executables."""
    executables = []
    
    for version in PYTHON_VERSIONS:
        # Try common executable names
        names_to_try = [
            f'python{version}',
            f'python{version.replace(".", "")}',
        ]
        
        for name in names_to_try:
            if which(name):
                executables.append((version, name))
                break
    
    # Also try the current Python
    current_version = f'{sys.version_info.major}.{sys.version_info.minor}'
    if not any(v == current_version for v, _ in executables):
        executables.append((current_version, sys.executable))
    
    return executables


def build_egg(python_executable):
    """Build an egg file using the specified Python executable."""
    print(f'\n{"=" * 60}')
    print(f'Building with: {python_executable}')
    print("=" * 60)
    
    try:
        result = subprocess.run(
            [python_executable, 'setup.py', 'bdist_egg'],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f'Error building: {e}')
        if e.stderr:
            print(e.stderr)
        return False
    except FileNotFoundError:
        print(f'Python executable not found: {python_executable}')
        return False


def main():
    """Main build function."""
    print("AutoLabel Deluge Plugin - Build Script")
    print("=" * 60)
    
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Find available Python executables
    python_executables = find_python_executables()
    
    if not python_executables:
        print("No Python executables found!")
        sys.exit(1)
    
    print(f"\nFound {len(python_executables)} Python version(s):")
    for version, exe in python_executables:
        print(f"  - Python {version}: {exe}")
    
    # Build for each Python version
    success_count = 0
    failed_count = 0
    
    for version, exe in python_executables:
        if build_egg(exe):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Build Summary")
    print("=" * 60)
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    
    if success_count > 0:
        print(f"\nEgg files are in the 'dist' directory.")
        # List built eggs
        if os.path.exists('dist'):
            eggs = [f for f in os.listdir('dist') if f.endswith('.egg')]
            for egg in sorted(eggs):
                print(f"  - {egg}")
    
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == '__main__':
    main()

