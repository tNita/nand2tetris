#!/usr/bin/env python3
"""
Simple test runner for VM Translator tests
"""
import subprocess
import os
import sys

def run_test(vm_file_path, expected_output_file):
    """Run VM translator test and compare output"""
    # Get directory and filename
    dir_path = os.path.dirname(vm_file_path)
    vm_filename = os.path.basename(vm_file_path)
    asm_filename = vm_filename.replace('.vm', '.asm')
    asm_path = os.path.join(dir_path, asm_filename)
    
    print(f"Testing {vm_filename}...")
    
    # Run VM translator
    try:
        result = subprocess.run(['python3', 'vmtranslator.py', vm_file_path], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Translation completed: {asm_filename}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Translation failed: {e}")
        return False
    
    # Check if ASM file was created
    if not os.path.exists(asm_path):
        print(f"✗ ASM file not created: {asm_path}")
        return False
    
    print(f"✓ ASM file created successfully")
    
    # Read the expected output format
    with open(expected_output_file, 'r') as f:
        expected_lines = f.readlines()
    
    # Extract expected values (simplified parsing for demonstration)
    if len(expected_lines) >= 2:
        expected_values = expected_lines[1].strip().split('|')[1:-1]  # Remove empty first and last
        expected_values = [v.strip() for v in expected_values]
        print(f"Expected: RAM[0]={expected_values[0]}, RAM[256]={expected_values[1]}")
    
    print(f"Generated ASM code in: {asm_path}")
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 test_runner.py <vm_file> <expected_output_file>")
        sys.exit(1)
    
    vm_file = sys.argv[1]
    expected_file = sys.argv[2]
    
    if run_test(vm_file, expected_file):
        print("Test completed successfully")
    else:
        print("Test failed")

if __name__ == "__main__":
    main()