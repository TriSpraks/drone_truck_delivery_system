#!/usr/bin/env python3
# find_frontend_api_call.py - Find where your frontend calls the backend API

import os
import re

def search_files_for_api_calls(directory):
    """Search all Python files for backend API calls"""
    
    patterns_to_find = [
        r'localhost:8000',
        r'8000/api/config',
        r'requests\.get.*api/config',
        r'http://.*:8000',
        r'Failed to get backend config'
    ]
    
    matches = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.txt')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for i, line in enumerate(content.splitlines(), 1):
                        for pattern in patterns_to_find:
                            if re.search(pattern, line, re.IGNORECASE):
                                matches.append({
                                    'file': file_path,
                                    'line_number': i,
                                    'line_content': line.strip(),
                                    'pattern': pattern
                                })
                                
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return matches

def main():
    print("🔍 Searching for API calls in your frontend...")
    print("=" * 60)
    
    # Search in current directory and subdirectories
    current_dir = '.'
    
    matches = search_files_for_api_calls(current_dir)
    
    if matches:
        print(f"✅ Found {len(matches)} potential API call locations:\n")
        
        for match in matches:
            print(f"📁 File: {match['file']}")
            print(f"📍 Line {match['line_number']}: {match['line_content']}")
            print(f"🔍 Pattern: {match['pattern']}")
            print("-" * 40)
        
        print("\n🛠️  TO FIX THE 404 ERROR:")
        print("1. Open the files listed above")
        print("2. Find lines containing 'localhost:8000' or '8000/api/config'") 
        print("3. Change port 8000 to 8001")
        print("4. Example:")
        print("   OLD: requests.get('http://localhost:8000/api/config')")
        print("   NEW: requests.get('http://localhost:8001/api/config')")
        
    else:
        print("❌ No API calls found in current directory")
        print("\n🔍 Let's check a few more things:")
        
        # Check if we're in the right directory
        if os.path.exists('frontend'):
            print("✅ Found 'frontend' directory")
            print("💡 Try running this script from inside the frontend directory:")
            print("   cd frontend")
            print("   python ../find_frontend_api_call.py")
        else:
            print("❌ No 'frontend' directory found")
            print("💡 Make sure you're in the right project directory")
        
        # List Python files in current directory
        py_files = [f for f in os.listdir('.') if f.endswith('.py')]
        if py_files:
            print(f"\n📁 Python files in current directory: {', '.join(py_files)}")
        else:
            print("\n❌ No Python files found in current directory")

if __name__ == "__main__":
    main()