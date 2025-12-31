import os
import subprocess
import pytest

def test_no_tracked_sqlite_files():
    """Fail if any var/*.sqlite files are tracked by git (hygiene gate)."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run([
        "git", "ls-files", "--error-unmatch", "var/*.sqlite"
    ], cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # If any files are tracked, fail
    if result.returncode == 0 and result.stdout.strip():
        tracked = result.stdout.strip().splitlines()
        pytest.fail(f"Tracked sqlite files found: {tracked}. Please remove from git.")
