import subprocess
from pathlib import Path
from typing import Tuple

def run_command(cmd: list[str], timeout: int = 300, input: str = None) -> Tuple[int, str, str]:
    """
    Runs an external command safely, with a timeout.

    Args:
        cmd (list[str]): The command and its arguments as a list.
        timeout (int): The timeout in seconds.

    Returns:
        A tuple containing (return_code, stdout, stderr).
    """
    try:
        kwargs = {
            'capture_output': True,
            'input': input,
            'text': True,
            'timeout': timeout,
            'check': False  # We will check the returncode manually
        }
        if input is not None:
            kwargs['input'] = input
        result = subprocess.run(cmd, **kwargs)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", f"Command '{' '.join(cmd)}' timed out after {timeout} seconds"
    except FileNotFoundError:
        return -1, "", f"Command not found: '{cmd[0]}'. Please ensure it is installed and in your PATH."
    except Exception as e:
        return -1, "", f"An unexpected error occurred while running '{' '.join(cmd)}': {e}"

def ensure_dir(path: Path):
    """
    Ensures a directory exists, creating it if necessary.
    
    Args:
        path (Path): The directory path to check/create.
    """
    path.mkdir(parents=True, exist_ok=True)
