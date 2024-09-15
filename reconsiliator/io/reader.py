from pathlib import Path
import yaml

def directory_reader(path: Path):

    apps = []
    for file_path in path.iterdir():

        with file_path.open('r') as f:
           app = yaml.safe_load(f)

        apps.append(app)

    return apps
