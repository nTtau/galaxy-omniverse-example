import json
import os
import shutil
from typing import Dict, Any


def clear_directory(dir_path: str) -> None:
    """
    Creates directory and clears files if it already exists.
    Intended to be used for output directory
    :param dir_path:
    """
    print(f"Clearing {dir_path} directory.")
    # Check if the directory exists
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        # Remove the directory and all its content
        shutil.rmtree(dir_path)

    # Recreate the empty directory
    os.makedirs(dir_path)


def load_json(filename: str) -> Dict[str, Any]:
    """
    Load json file. Intended to be used for configuration and parameters.
    :param filename:
    :return: Loaded JSON
    """
    print(f'Loading json file {filename}')
    with open(filename, 'r') as file:
        return json.load(file)


def save_json(settings: Dict[str, Any], output_dir: str, filename: str) -> None:
    """
    Save configuration to JSON file.
    :param settings:
    :param output_dir:
    :param filename:
    :return:
    """
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    print(f'Saving json file {file_path}')
    with open(file_path, 'w') as file:
        json.dump(settings, file, indent=4)
