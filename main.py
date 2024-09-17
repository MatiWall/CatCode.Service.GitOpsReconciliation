import logging
from multiprocessing.managers import Value

from reconsiliator.application.model import Application

logger = logging.getLogger(__name__)
import json
import time
import subprocess
from pathlib import Path
import requests
import git
import os
import yaml

from reconsiliator.io import directory_reader
from settings import config
from settings import BASE_DIR


# Clone the repository
def clone_repo(repo_url, clone_dir: Path):
    if not not clone_dir.exists():
        clone_dir.mkdir(parents=True, exist_ok=True)
    git.Repo.clone_from(repo_url, clone_dir)

def update_repo(clone_dir):
    subprocess.run(['git', 'pull'], cwd=clone_dir)

# Read files from the repository
def read_files(directory):
    objects = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = directory / file
            with file_path.open('r') as f:
                obj = yaml.safe_load(f)

            objects.append(obj)
    return objects


def insert_files_to_etcd(files):

    for file in files: # all logic is left for the CoreAI
        resp = requests.post(config.core_api, json=file)
        logger.info(str(resp.json()))



# Main function
def main(apps: list[Application]):


    for app in apps:

        CLONE_REPO = BASE_DIR/ f'clones/{app.metadata.name}'

        try:
            update_repo(CLONE_REPO)
        except:
            clone_repo(
                app.spec.source.urlPath,
                CLONE_REPO
            )
        files = read_files(CLONE_REPO/ app.spec.source.subPath)

        insert_files_to_etcd(files)

if __name__ == "__main__":
    apps = directory_reader(BASE_DIR / 'applications')
    apps = [Application(**app) for app in apps]
    while True:
        logger.debug('Checking for updates')
        main(apps)
        time.sleep(5*60)
