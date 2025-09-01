import requests
import gzip
import os

def download_file(url: str, destination_path: str) -> str:
    """
    Download a file from a URL to a specified local path.
    Returns the absolute path to the downloaded file.
    """
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with open(destination_path, 'wb') as f:
        f.write(response.content)
    return os.path.abspath(destination_path)

def delete_file(file_path: str, ignore_missing: bool = True) -> bool:
    """
    Delete a file if it exists.
    Returns True if the file was deleted, False if it did not exist and ignore_missing is True.
    Raises FileNotFoundError if the file does not exist and ignore_missing is False.
    """
    if not file_path:
        return False
    p = os.path.abspath(file_path)
    if os.path.exists(p):
        os.remove(p)
        return True
    if ignore_missing:
        return False
    raise FileNotFoundError(p)
    
def unzip_gz_file(source_path: str, destination_path: str) -> str:
    """
    Unzip a .gz file to a specified destination path.
    Returns the absolute path to the unzipped file.
    """
    with gzip.open(source_path, 'rb') as f_in:
        with open(destination_path, 'wb') as f_out:
            f_out.write(f_in.read())
    return os.path.abspath(destination_path)
