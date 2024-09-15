import logging

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
        os.makedirs(clone_dir)
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

def get_existing_resource(key):
    command = ['etcdctl', 'get', key]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        raise ValueError(f'Failed to retrieve resource for key')

def insert_files_to_etcd(files):

    for file in files:
        apigroup = file['apiVersion'].split('/')[0]
        resource_group = file['spec']['group']
        singular = file['spec']['names']['singular']

        key = f'resource/registry/{apigroup}/resourcedefinition/{resource_group}/{singular}'
        path = f'{config.core_api}/{key}'

        resp = requests.get(path)
        if resp.status_code == 200:
            response = resp.json()
            resource_exists = response.get('exists')
            if resource_exists:
                current_state = resp.json()['value']
                current_state = json.loads(current_state)

                if file == current_state:
                    logger.debug(f'State of object {key} did not change, continuing.')
                    continue

            logger.info(f'Resource changed: {key}')
            resp = requests.post(path, json=file)
            if resp.status_code == 200:
                logger.info(f'Successfully updated resource at {key}')
            else:
                logger.error(f'Failed to update resource at {key}')
        else:
            logger.error(f'Failed to read current state of resource {key}')


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
