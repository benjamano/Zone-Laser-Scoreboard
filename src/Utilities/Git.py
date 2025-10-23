import subprocess

def getCurrentCommit() -> str:
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        return commit

    except Exception as e:
        return ""
    return ""