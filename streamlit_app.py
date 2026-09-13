"""
Streamlit entry point for Streamlit Cloud deployment.
This file ensures the app runs correctly on Streamlit Cloud.
"""

import os
import sys

# Add root directory to path for imports
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import and run the main app
from app.main import *
