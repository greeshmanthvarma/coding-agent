import git
import os
def get_current_commit_hash(working_directory: str):
    """
    Get the current commit hash of the repository.
    """
    abs_working_dir= os.path.abspath(working_directory)
    if not os.path.isdir(abs_working_dir):
        return {"error": f"Working directory not found: {abs_working_dir}"}
    try:
        repo =git.Repo(abs_working_dir)
        commit=repo.head.commit
        return {"commit_hash": commit.hexsha}
    except Exception as e:
        return {"error": f"Error getting current commit hash: {str(e)}"}


def get_git_status(working_directory: str):
    """
    Get the current git status of the repository.
    """
    abs_working_dir= os.path.abspath(working_directory)
    if not os.path.isdir(abs_working_dir):
        return {"error": f"Working directory not found: {abs_working_dir}"}

    try:
        repo=git.Repo(abs_working_dir)
        diff= repo.index.diff(None)
        
        untracked=repo.untracked_files
        
        changes={
            "modified":[],
            "added":[],
            "deleted":[]
        }

        for diff_item in diff:
            diff_type=diff_item.change_type
            if diff_type=="M":
                changes["modified"].append(diff_item.a_path)
            elif diff_type=="A":
                changes["added"].append(diff_item.a_path)
            elif diff_type=="D":
                changes["deleted"].append(diff_item.a_path)
        
        for untracked_file in untracked:
            changes["added"].append(untracked_file)

        return changes

    except Exception as e:
        return {"error": f"Error getting git status: {str(e)}"}


def revert_to_checkpoint(working_directory: str, checkpoint_commit_hash: str):
    """
    Revert the repository to a checkpoint commit hash.
    """

    abs_working_dir= os.path.abspath(working_directory)
    if not os.path.isdir(abs_working_dir):
        return {"error": f"Working directory not found: {abs_working_dir}"}

    try:
        repo=git.Repo(abs_working_dir)

        repo.git.reset('--hard', checkpoint_commit_hash) 

        repo.git.clean('-fd') # Clean untracked files and directories

        return {"message": f"Reverted to checkpoint commit hash: {checkpoint_commit_hash}"}

    except Exception as e:
        return {"error": f"Error reverting to checkpoint commit hash: {str(e)}"}

def commit_changes(working_directory:str,commit_message:str,branch_name:str=None):
    """
    Commit changes to the repository with a branch name. If branch name is not provided, it will commit to the current branch.
    """
    abs_working_dir= os.path.abspath(working_directory)
    if not os.path.isdir(abs_working_dir):
        return {"error": f"Working directory not found: {abs_working_dir}"}

    try:
        repo=git.Repo(abs_working_dir)
        
        if branch_name:
            if branch_name not in [ref.name for ref in repo.heads]:
                repo.git.checkout('-b', branch_name)
            else:
                repo.git.checkout(branch_name)
       
       
        if not repo.is_dirty() and not repo.untracked_files:
            return {"error": "No changes to commit"}

        repo.git.add('-A')

        repo.index.commit(commit_message)
        commit=repo.head.commit
        
        return {"message":f"Committed changes with message: {commit_message} to branch: {repo.active_branch.name}",
        "commit_hash":commit.hexsha,
        "branch_name":repo.active_branch.name
        }
    except Exception as e:
        return {"error": f"Error committing changes: {str(e)}"}

def push_changes(working_directory:str, branch_name:str,github_token:str, repo_url:str):
    """
    Push Changes to the repository to the remote branch.
    """
    abs_working_dir= os.path.abspath(working_directory)
    if not os.path.isdir(abs_working_dir):
        return {"error": f"Working directory not found: {abs_working_dir}"}

    try:
        repo=git.Repo(abs_working_dir)

        
        repo_path = repo_url.replace('https://github.com/', '').replace('.git', '')
        authenticated_url=f"https://{github_token}@github.com/{repo_path}.git"
        
        try:
            origin=repo.remote('origin')
        except:
            origin=repo.create_remote('origin')
        
        origin.set_url(authenticated_url)

        origin.push(branch_name)
        
        return {"message":f"Pushed changes to branch: {branch_name} on repo: {repo_url}",
        "branch_name":branch_name,
        "repo_url":repo_url
        }

    except Exception as e:
        return {"error": f"Error pushing changes: {str(e)}"}