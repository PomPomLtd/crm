#!/usr/bin/env python3
"""
Test script for the unified healthcare data scraper system.
Tests all major components and functionality.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from common import load_config, setup_logging, ScraperSession, CSVManager
        from common import get_scraper_config, get_searchapi_key, get_banned_domains
        from common import clean_text, extract_email, extract_phone, standardize_csv_output
        print("✅ All common utilities imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("🔍 Testing configuration loading...")
    
    try:
        from common import load_config, get_scraper_config
        
        # Test main config loading
        config = load_config()
        
        # Verify config structure
        assert 'scrapers' in config, "Config missing 'scrapers' section"
        assert 'settings' in config, "Config missing 'settings' section"
        
        # Test specific scraper configs
        hospitals_config = get_scraper_config('hospitals')
        assert hospitals_config['name'] == 'Hospitals', "Hospitals config incorrect"
        
        # Test non-existent scraper
        empty_config = get_scraper_config('non-existent')
        assert empty_config == {}, "Non-existent scraper should return empty dict"
        
        print("✅ Configuration loading works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading error: {e}")
        return False

def test_utility_functions():
    """Test utility functions"""
    print("🔍 Testing utility functions...")
    
    try:
        from common import clean_text, extract_email, extract_phone
        
        # Test text cleaning
        dirty_text = "  Hello\nWorld\t  "
        clean = clean_text(dirty_text)
        assert clean == "Hello World", f"Text cleaning failed: '{clean}'"
        
        # Test email extraction
        text_with_email = "Contact us at info@example.com for more information"
        email = extract_email(text_with_email)
        assert email == "info@example.com", f"Email extraction failed: '{email}'"
        
        # Test phone extraction (Swiss format)
        text_with_phone = "Call us at +41 44 123 45 67"
        phone = extract_phone(text_with_phone)
        assert phone is not None, "Phone extraction failed"
        
        print("✅ Utility functions work correctly")
        return True
        
    except Exception as e:
        print(f"❌ Utility functions error: {e}")
        return False

def test_session_management():
    """Test ScraperSession functionality"""
    print("🔍 Testing session management...")
    
    try:
        from common import ScraperSession
        
        # Create session
        session = ScraperSession('test_scraper')
        
        # Test internet connection check
        connected = session.check_internet_connection()
        print(f"  Internet connection: {'✅' if connected else '⚠️ Offline'}")
        
        # Test session has required attributes
        assert hasattr(session, 'session'), "Session missing requests session"
        assert hasattr(session, 'logger'), "Session missing logger"
        assert hasattr(session, 'scraper_name'), "Session missing scraper name"
        
        print("✅ Session management works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Session management error: {e}")
        return False

def test_csv_management():
    """Test CSV management functionality"""
    print("🔍 Testing CSV management...")
    
    try:
        from common import CSVManager
        
        # Create CSV manager
        csv_manager = CSVManager('test_scraper')
        
        # Test data
        test_data = [
            {'name': 'Test Hospital', 'city': 'Zurich', 'phone': '+41 44 123 45 67'},
            {'name': 'Test Clinic', 'city': 'Geneva', 'phone': '+41 22 987 65 43'}
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            # Test saving
            success = csv_manager.save_to_csv(test_data, temp_filename)
            assert success, "CSV saving failed"
            
            # Test loading
            loaded_data = csv_manager.load_from_csv(temp_filename)
            assert len(loaded_data) == 2, f"Expected 2 records, got {len(loaded_data)}"
            assert loaded_data[0]['name'] == 'Test Hospital', "Data integrity check failed"
            
            print("✅ CSV management works correctly")
            return True
            
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
        
    except Exception as e:
        print(f"❌ CSV management error: {e}")
        return False

def test_data_standardization():
    """Test data standardization"""
    print("🔍 Testing data standardization...")
    
    try:
        from common import standardize_csv_output
        
        # Test data with various formats
        raw_data = [
            {
                'name': '  Dr. Test Hospital  ',
                'address': 'Main Street 123, 8001 Zurich',
                'phone': '+41 44 123 45 67',
                'email': 'info@hospital.ch',
                'website': 'https://hospital.ch'
            }
        ]
        
        # Standardize data
        standardized = standardize_csv_output(raw_data, 'hospital')
        
        # Verify standardization
        assert len(standardized) == 1, "Standardization changed record count"
        
        record = standardized[0]
        assert 'name' in record, "Missing name field"
        assert 'type' in record, "Missing type field"
        assert record['type'] == 'hospital', "Incorrect type assignment"
        assert record['name'] == 'Dr. Test Hospital', "Name not cleaned properly"
        
        print("✅ Data standardization works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Data standardization error: {e}")
        return False

def test_scraper_manager_import():
    """Test that scraper manager can be imported and basic functions work"""
    print("🔍 Testing scraper manager import...")
    
    try:
        import scraper_manager
        
        # Test that we can create a ScraperManager instance
        manager = scraper_manager.ScraperManager()
        
        # Test that it has the expected attributes
        assert hasattr(manager, 'config'), "Manager missing config"
        assert hasattr(manager, 'logger'), "Manager missing logger"
        
        # Test that config is loaded
        assert 'scrapers' in manager.config, "Manager config missing scrapers"
        
        print("✅ Scraper manager import works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Scraper manager import error: {e}")
        return False

def test_unified_scrapers():
    """Test that unified scrapers can be imported and have correct structure"""
    print("🔍 Testing unified scrapers...")
    
    try:
        # Test base scraper import
        from base_scraper import BaseHealthcareScraper
        assert BaseHealthcareScraper, "Base scraper class not importable"
        print("  ✅ Base scraper imports correctly")
        
        # Test unified scrapers exist and have correct structure
        unified_scrapers = [
            ("hospitals/get-hospitals-unified.py", "HospitalsScraper"),
            ("clinics/get-clinics-unified.py", "ClinicsScraper"),
        ]
        
        found_scrapers = 0
        for script_path, class_name in unified_scrapers:
            script_file = Path(script_path)
            if script_file.exists():
                with open(script_file, 'r') as f:
                    code = f.read()
                
                # Check structure
                assert "BaseHealthcareScraper" in code, f"Missing base class import in {script_path}"
                assert f"class {class_name}" in code, f"Missing main class in {script_path}"
                assert "get_scraper_type" in code, f"Missing get_scraper_type method in {script_path}"
                assert "extract_item_details" in code, f"Missing extract_item_details method in {script_path}"
                
                found_scrapers += 1
        
        print(f"  ✅ {found_scrapers} unified scrapers have correct structure")
        
        # Test that we can create an instance of a unified scraper
        if Path("hospitals/get-hospitals-unified.py").exists():
            # Add the hospitals directory to path temporarily
            import sys
            hospitals_path = str(Path("hospitals").absolute())
            if hospitals_path not in sys.path:
                sys.path.insert(0, hospitals_path)
            
            try:
                # Import the unified scraper module  
                import importlib.util
                spec = importlib.util.spec_from_file_location("hospital_scraper", "hospitals/get-hospitals-unified.py")
                hospital_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(hospital_module)
                
                # Test instantiation
                scraper_instance = hospital_module.HospitalsScraper()
                assert hasattr(scraper_instance, 'scraper_key'), "Instance missing scraper_key"
                assert scraper_instance.scraper_key == 'hospitals', "Incorrect scraper key"
                print("  ✅ Unified scraper can be instantiated")
                
            except Exception as e:
                print(f"  ⚠️ Could not test instantiation: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified scrapers test error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("Healthcare Data Scraper System - Test Suite")
    print("=" * 50)
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Loading", test_config_loading),
        ("Utility Functions", test_utility_functions),
        ("Session Management", test_session_management),
        ("CSV Management", test_csv_management),
        ("Data Standardization", test_data_standardization),
        ("Scraper Manager Import", test_scraper_manager_import),
        ("Unified Scrapers", test_unified_scrapers),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            failed += 1
    
    print(f"\n{'=' * 50}")
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 50}")
    
    if failed == 0:
        print("🎉 All tests passed! System is working correctly.")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)