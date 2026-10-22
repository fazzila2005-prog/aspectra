import os
import sys
from pathlib import Path

# The app opens files like "data/reviews.csv", so always run the tests from the project folder
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
