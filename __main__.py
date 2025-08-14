#!/usr/bin/env python
"""
Enable running cubic_inspect as a module:
python -m cubic_inspect --surface "..." --F0 "..." ...
"""

from .cubic_cli import main

if __name__ == "__main__":
    main()