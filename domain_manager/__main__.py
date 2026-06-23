#!/usr/bin/env python3
"""
Domain Manager — Unified CLI for 20+ domain/DNS providers.

Open source: https://github.com/monah-studio/domain-manager
Install: pip install domain-manager
"""

import sys
import os

# Allow running as script from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain_manager.cli import main

if __name__ == "__main__":
    sys.exit(main())
