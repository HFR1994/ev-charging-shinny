import os.path
from pathlib import Path

app_dir = Path(__file__).parent
assets_dir = app_dir / "assets"
print(assets_dir / "styles.css")