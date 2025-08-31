import requests 
import os

def download_file(url: str, destination_path: str) -> str:
    """
    Download a file from a URL to a specified local path.
    Returns the absolute path to the downloaded file.
    """
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with open(destination_path, 'wb') as f:
        for chunk in response.itercontent(1 << 20):
            if chunk:
                f.write(chunk)
    return os.path.abspath(destination_path)

def delete_file(file_path: str):
    """
    Delete a file if it exists.
    """
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
    except Exception as e:
        raise RuntimeError(f"Failed to delete file {file_path}: {e}")