"""Permite ejecutar el verificador como python -m src.cli."""

import sys
from src.cli.verify_independently import main

if __name__ == "__main__":
    sys.exit(main())
