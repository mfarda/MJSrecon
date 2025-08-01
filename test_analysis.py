#!/usr/bin/env python3
"""
Test script for the analysis module.
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.analyzer import run as analysis_run, analyze_single_file
from common.config import CONFIG
from common.logger import Logger

def test_analyze_single_file():
    """Test the analyze_single_file function with mocked dependencies."""
    print("Testing analyze_single_file function...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        results_dir = temp_path / "results"
        results_dir.mkdir()
        
        # Mock the js_file
        js_file = Path("test_file.js")
        
        # Mock logger
        logger = Mock(spec=Logger)
        
        # Mock config
        config = {
            'dirs': {
                'downloaded_files': str(temp_path / "downloaded_files"),
                'results': str(results_dir)
            },
            'tools': {
                'python_tools': {
                    'secretfinder': '/path/to/secretfinder.py',
                    'linkfinder': '/path/to/linkfinder.py'
                }
            },
            'timeouts': {
                'analysis': 30
            }
        }
        
        # Mock run_command to return success
        with patch('analysis.analyzer.run_command') as mock_run_command:
            mock_run_command.return_value = (0, "test output", "")
            
            # Test the function
            result = analyze_single_file(js_file, results_dir, config, logger)
            
            # Verify the function runs without errors
            assert result is None
            assert mock_run_command.called
            
            print("✓ analyze_single_file test passed")

def test_analysis_run_with_no_js_urls():
    """Test the analysis run function when no JS URLs are provided."""
    print("Testing analysis run with no JS URLs...")
    
    # Mock arguments
    args = Mock()
    
    # Mock config
    config = CONFIG.copy()
    
    # Mock logger
    logger = Mock(spec=Logger)
    
    # Mock workflow data with no JS URLs
    workflow_data = {
        'target': 'test.com',
        'target_output_dir': Path('/tmp/test'),
        'deduplicated_urls': ['https://test.com/style.css', 'https://test.com/image.png']
    }
    
    # Test the function
    result = analysis_run(args, config, logger, workflow_data)
    
    # Verify the result
    assert result == {"analysis_summary": {}}
    logger.warning.assert_called()
    
    print("✓ Analysis run with no JS URLs test passed")

def test_analysis_run_with_js_urls():
    """Test the analysis run function with JS URLs."""
    print("Testing analysis run with JS URLs...")
    
    # Mock arguments
    args = Mock()
    
    # Mock config
    config = CONFIG.copy()
    
    # Mock logger
    logger = Mock(spec=Logger)
    
    # Mock workflow data with JS URLs
    workflow_data = {
        'target': 'test.com',
        'target_output_dir': Path('/tmp/test'),
        'deduplicated_urls': [
            'https://test.com/script.js',
            'https://test.com/app.js',
            'https://test.com/style.css'
        ]
    }
    
    # Mock the analyze_single_file function
    with patch('analysis.analyzer.analyze_single_file') as mock_analyze:
        mock_analyze.return_value = None
        
        # Test the function
        result = analysis_run(args, config, logger, workflow_data)
        
        # Verify the result
        assert result == {"analysis_summary": {"status": "Completed"}}
        assert mock_analyze.called
        
        print("✓ Analysis run with JS URLs test passed")

def test_imports():
    """Test that all required imports work correctly."""
    print("Testing imports...")
    
    try:
        from analysis.analyzer import run, analyze_single_file
        from common.config import CONFIG
        from common.logger import Logger
        from common.utils import run_command, ensure_dir
        from common.finder import find_urls_with_extension
        print("✓ All imports successful")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Starting analysis module tests...\n")
    
    # Test imports first
    if not test_imports():
        print("Import tests failed. Exiting.")
        return
    
    # Run tests
    try:
        test_analyze_single_file()
        test_analysis_run_with_no_js_urls()
        test_analysis_run_with_js_urls()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 