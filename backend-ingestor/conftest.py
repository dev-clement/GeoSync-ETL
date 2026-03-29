"""
This file allows pytest to recognize the root directory
and add 'src' to the sys.path automatically
"""
import sys
import os
from pathlib import Path

# 1. Absolute path resolution
# This ensure that 'src' is always findable regardless of where pytest is called from
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# 2. Envisonment variable injection for tests
# We manually set a dummy URL if the environment variable is missing
# This prevent the Pydantic validationError during test collection
if not os.environ.get('STAC_API_URL'):
    os.environ['STAC_API_URL'] = 'https://planetarycomputer.microsoft.com/api/stac/v1' 