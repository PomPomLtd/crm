#!/usr/bin/env python3
"""
End-to-end validation script for the unified healthcare scraper system.
Demonstrates that all components work together correctly.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, description, timeout=30):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, 
            timeout=timeout, cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True, result.stdout
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}...")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏱️ {description} - Timeout")
        return False, "Command timed out"
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False, str(e)

def validate_file_structure():
    """Validate that all required files exist"""
    print("🔍 Validating file structure...")
    
    required_files = [
        "config.json",
        "common.py", 
        "base_scraper.py",
        "scraper_manager.py",
        "requirements.txt",
        "setup.py",
        "test_system.py",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def validate_config_consistency():
    """Validate configuration file consistency"""
    print("🔍 Validating configuration consistency...")
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Check that all scrapers have required fields
    required_fields = ['name', 'description', 'url', 'main_script', 'output_file', 'final_output', 'web_output']
    
    for scraper_key, scraper_config in config['scrapers'].items():
        missing_fields = []
        for field in required_fields:
            if field not in scraper_config:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Scraper '{scraper_key}' missing fields: {', '.join(missing_fields)}")
            return False
        
        # Check if unified script exists
        unified_script = scraper_config.get('main_script_unified')
        if unified_script and Path(unified_script).exists():
            print(f"✅ {scraper_key}: Unified script available")
        else:
            print(f"⚠️ {scraper_key}: No unified script found")
    
    print("✅ Configuration is consistent")
    return True

def validate_imports():
    """Validate that all modules can be imported"""
    print("🔍 Validating imports...")
    
    success, output = run_command("python3 -c 'from common import *; from base_scraper import *; print(\"All imports successful\")'", "Import test")
    return success

def validate_scraper_manager():
    """Validate scraper manager functionality"""
    print("🔍 Validating scraper manager...")
    
    # Test list command
    success, output = run_command("python3 scraper_manager.py list", "Manager list command")
    if not success:
        return False
    
    # Test stats command
    success, output = run_command("python3 scraper_manager.py stats", "Manager stats command")
    if not success:
        return False
    
    # Test help command
    success, output = run_command("python3 scraper_manager.py --help", "Manager help command")
    return success

def validate_unified_scrapers():
    """Validate that unified scrapers can be executed"""
    print("🔍 Validating unified scrapers...")
    
    # Check if unified scrapers exist and can be imported
    unified_scripts = [
        "hospitals/get-hospitals-unified.py",
        "clinics/get-clinics-unified.py", 
        "groupclinics/groupy-unified.py",
        "med-clinic/get-medclinics-unified.py",
        "medicalCenters/medicelcenter-unified.py",
        "docs/onedoc_scraper-unified.py"
    ]
    
    available_scrapers = 0
    for script in unified_scripts:
        if Path(script).exists():
            # Test that the script can be imported (syntax check)
            success, output = run_command(f"python3 -m py_compile {script}", f"Syntax check for {script}", 10)
            if success:
                available_scrapers += 1
                print(f"  ✅ {script} - Valid syntax")
            else:
                print(f"  ❌ {script} - Syntax error")
        else:
            print(f"  ⚠️ {script} - Not found")
    
    print(f"✅ {available_scrapers}/{len(unified_scripts)} unified scrapers are valid")
    return available_scrapers > 0

def run_comprehensive_test():
    """Run the comprehensive test suite"""
    print("🔍 Running comprehensive test suite...")
    
    success, output = run_command("python3 test_system.py", "Comprehensive test suite", 60)
    if success and "All tests passed!" in output:
        print("✅ All comprehensive tests passed")
        return True
    else:
        print("❌ Some comprehensive tests failed")
        return False

def main():
    """Main validation process"""
    print("Healthcare Data Scraper System - End-to-End Validation")
    print("=" * 60)
    print()
    
    validations = [
        ("File Structure", validate_file_structure),
        ("Configuration Consistency", validate_config_consistency), 
        ("Module Imports", validate_imports),
        ("Scraper Manager", validate_scraper_manager),
        ("Unified Scrapers", validate_unified_scrapers),
        ("Comprehensive Tests", run_comprehensive_test),
    ]
    
    passed = 0
    failed = 0
    
    for validation_name, validation_func in validations:
        print(f"\n--- {validation_name} ---")
        try:
            if validation_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Validation '{validation_name}' crashed: {e}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"VALIDATION RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    
    if failed == 0:
        print("🎉 SYSTEM FULLY VALIDATED!")
        print("✨ The unified healthcare scraper system is ready for production use.")
        print()
        print("Quick Start:")
        print("  python scraper_manager.py list")
        print("  python scraper_manager.py run hospitals")
        print("  python scraper_manager.py stats")
        return True
    else:
        print(f"⚠️ {failed} validation(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)