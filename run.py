#!/usr/bin/env python3
"""
Run script for AI Research Agent
Launch from project root directory
"""
import os
import sys

# Add src directory to Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

# Change to src directory for relative imports
os.chdir(src_dir)

# Import and run the Flask app
from research_ui_flask import app

if __name__ == '__main__':
    print("\n" + "="*60)
    print("AI Research Agent")
    print("="*60)
    print("\nOpen your browser to: http://localhost:5001\n")

    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
