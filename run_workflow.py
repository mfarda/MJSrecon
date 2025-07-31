#!/usr/bin/env python3
"""
Main entry point for running MJSrecon workflows directly.
"""
import sys
import os

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.core import main

if __name__ == "__main__":
    main()
