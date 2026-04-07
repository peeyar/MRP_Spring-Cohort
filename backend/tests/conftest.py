"""Add backend directory to sys.path so modules can be imported without package prefix."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
