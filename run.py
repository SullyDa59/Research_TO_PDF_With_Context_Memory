#!/usr/bin/env python3
"""
Run script for AI Research Agent
Launch from project root directory
Now using FastAPI + uvicorn (migrated from Flask)
"""
import os
import sys
import socket

# Add src directory to Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_dir)

# Change to src directory for relative imports
os.chdir(src_dir)


def check_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


if __name__ == '__main__':
    import uvicorn

    PORT = 5001
    HOST = '0.0.0.0'

    print("\n" + "="*60)
    print("AI Research Agent")
    print("="*60)

    # Check if port is in use
    if check_port_in_use(PORT):
        print(f"\n⚠️  Port {PORT} is already in use!")
        print(f"   To free the port, run: lsof -i :{PORT}")
        print(f"   Then kill the process: kill <PID>")
        print("\nAlternatively, the server may already be running.")
        sys.exit(1)

    print(f"\nOpen your browser to: http://localhost:{PORT}")
    print(f"API documentation at: http://localhost:{PORT}/docs")
    print("\n")

    # Import FastAPI app and run with uvicorn
    from research_ui_fastapi import app

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=False,  # Disable reload in dev to avoid issues with Qdrant locks
        log_level="info"
    )
