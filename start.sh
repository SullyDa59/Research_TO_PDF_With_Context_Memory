#!/bin/bash
# Quick start script for Research to PDF Generator

echo "============================================================"
echo "Research to PDF Generator - Quick Start"
echo "============================================================"
echo ""

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY is not set"
    echo ""
    echo "Please set your OpenAI API key:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo ""
    echo "Get your API key at: https://platform.openai.com/api-keys"
    echo ""
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "✓ Dependencies ready"
echo ""

# Start the Flask app
echo "Starting Flask web UI on port 5001..."
echo ""
python3 research_ui_flask.py
