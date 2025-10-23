import os
import tempfile
import git

def run_local_py():
    temp_dir= tempfile.mkdtemp(prefix="cloned_repo",dir="calculator")
    git.Repo.clone_from("https://github.com/greeshmanthvarma/coding-agent.git", temp_dir)

    print(f"Cloned calculator to {temp_dir}")

    return temp_dir


run_local_py()