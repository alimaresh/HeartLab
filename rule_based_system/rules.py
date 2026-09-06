"""Knowledge base entry point. The active engine is implemented in plain Python."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heart_app.rules import RULES, Rule, infer
