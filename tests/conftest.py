import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

pytest_plugins = ("pytest_homeassistant_custom_component",)
