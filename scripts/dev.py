"""Run the local workbench on Windows or Linux with the active Python environment."""
from pathlib import Path
import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
