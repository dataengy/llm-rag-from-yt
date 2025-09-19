#!/usr/bin/env python3
"""
Dagster development server runner.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Start Dagster development server."""
    # Set up paths
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    
    # Set environment variables
    os.environ["DAGSTER_HOME"] = str(project_root / "data" / "dagster")
    
    # Add src to Python path
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = f"{src_path}:{os.environ['PYTHONPATH']}"
    else:
        os.environ["PYTHONPATH"] = str(src_path)
    
    # Create Dagster home directory
    dagster_home = Path(os.environ["DAGSTER_HOME"])
    dagster_home.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Dagster development server...")
    print(f"DAGSTER_HOME: {os.environ['DAGSTER_HOME']}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print("Web UI will be available at: http://localhost:3000")
    
    try:
        # Start Dagster dev server
        cmd = [
            sys.executable, "-m", "dagster", "dev",
            "-f", "llm_rag_yt/dagster/definitions.py",
            "--port", "3000",
            "--host", "localhost"
        ]
        
        subprocess.run(cmd, cwd=src_path, check=True)
        
    except KeyboardInterrupt:
        print("\nDagster server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Dagster server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()