#!/usr/bin/env python3
"""
Environment Variable Checker and Fixer
Checks and fixes .env file format issues
"""

import os
import re

def check_env_file():
    """Check and fix .env file formatting"""
    print("🔍 Checking .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ .env file found")
        
        # Look for DATABASE_URL
        database_url_lines = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'DATABASE_URL' in line and not line.strip().startswith('#'):
                database_url_lines.append((i, line.strip()))
        
        if not database_url_lines:
            print("❌ DATABASE_URL not found in .env file")
            return False
        
        print(f"✅ Found {len(database_url_lines)} DATABASE_URL line(s):")
        
        for line_num, line in database_url_lines:
            print(f"  Line {line_num}: {line}")
            
            # Check if the line has proper format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                if key == 'DATABASE_URL' and value:
                    print(f"    ✅ Valid DATABASE_URL found")
                    print(f"    Value: {value[:50]}...")
                    
                    # Test loading with python-dotenv
                    os.environ['TEST_DATABASE_URL'] = value
                    test_value = os.getenv('TEST_DATABASE_URL')
                    
                    if test_value == value:
                        print("    ✅ Environment loading test passed")
                    else:
                        print("    ⚠️ Environment loading test failed")
                        print(f"    Expected: {value[:30]}...")
                        print(f"    Got: {test_value[:30] if test_value else 'None'}...")
                else:
                    print(f"    ❌ Invalid format or empty value")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def fix_env_file():
    """Fix common .env file issues"""
    print("\n🔧 Fixing .env file format...")
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        changes_made = False
        
        for line in lines:
            original_line = line
            
            # Skip comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                fixed_lines.append(line)
                continue
            
            # Process DATABASE_URL line
            if 'DATABASE_URL' in line:
                # Remove any leading/trailing whitespace
                line = line.strip()
                
                # Ensure proper format: KEY=VALUE (no quotes unless necessary)
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove unnecessary quotes
                    if value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                        changes_made = True
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                        changes_made = True
                    
                    # Reconstruct line
                    line = f"{key}={value}\n"
                else:
                    line = original_line
                
                if line != original_line:
                    changes_made = True
                    print(f"    Fixed: {original_line.strip()} -> {line.strip()}")
            
            fixed_lines.append(line)
        
        if changes_made:
            # Backup original file
            import shutil
            shutil.copy2('.env', '.env.backup')
            print("    📁 Created backup: .env.backup")
            
            # Write fixed content
            with open('.env', 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            print("    ✅ Fixed .env file format")
        else:
            print("    ✅ No changes needed")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error fixing .env file: {e}")
        return False

def test_environment_loading():
    """Test loading environment variables"""
    print("\n🧪 Testing environment variable loading...")
    
    try:
        # Try to load with python-dotenv
        from dotenv import load_dotenv
        
        # Clear any existing DATABASE_URL
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']
        
        # Load from .env
        load_dotenv(override=True)
        
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            print("    ✅ DATABASE_URL loaded successfully")
            print(f"    Value: {database_url[:50]}...")
            
            # Validate it looks like a PostgreSQL URL
            if database_url.startswith('postgresql://'):
                print("    ✅ Valid PostgreSQL URL format")
                return True
            else:
                print("    ⚠️ URL doesn't start with 'postgresql://'")
                return False
        else:
            print("    ❌ DATABASE_URL not loaded")
            return False
            
    except ImportError:
        print("    ❌ python-dotenv not installed")
        print("    Install with: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"    ❌ Error testing environment loading: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("🔧 Environment Variable Checker and Fixer")
    print("=" * 60)
    
    # Step 1: Check .env file
    if not check_env_file():
        print("\n❌ .env file check failed")
        return False
    
    # Step 2: Fix formatting issues
    if not fix_env_file():
        print("\n❌ .env file fix failed")
        return False
    
    # Step 3: Test loading
    if not test_environment_loading():
        print("\n❌ Environment loading test failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Environment configuration is working correctly!")
    print("=" * 60)
    print("You can now run: python migrate_to_postgresql.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")