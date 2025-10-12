import os
import re

def check_config_references():
    """Check all Python files for config.Config references"""
    python_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    config_pattern = re.compile(r'config\.Config')
    
    print("🔍 Checking for config.Config references...")
    found_issues = False
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if config_pattern.search(line):
                        print(f"❌ Found in {file_path}:{line_num}")
                        print(f"   {line.strip()}")
                        found_issues = True
        except Exception as e:
            print(f"⚠️ Could not read {file_path}: {e}")
    
    if not found_issues:
        print("✅ No config.Config references found!")
    else:
        print("\n💡 Please update these references to use config directly")

if __name__ == "__main__":
    check_config_references()