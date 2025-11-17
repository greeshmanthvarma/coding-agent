import os
import subprocess
from google.genai import types 

def run_command(working_directory: str, command: str, args=None):
    """
    Run a shell command in the working directory.
    Automatically uses a virtual environment for Python commands if needed.
    Returns stdout, stderr, and exit code.
    """
    abs_working_dir = os.path.abspath(working_directory)
    
    if not os.path.isdir(abs_working_dir):
        return {"error": f'Error: "{working_directory}" is not a valid directory'}
    
    # Check if this is a pip install command - use venv if needed
    venv_path = os.path.join(abs_working_dir, ".venv")
    use_venv = False
    
    if command in ["pip", "python3", "python"] and args:
        args_list = args if isinstance(args, list) else [args]
        # Check if it's an install command
        if any(arg in args_list for arg in ["install", "i"]):
            use_venv = True
            # Create venv if it doesn't exist
            if not os.path.exists(venv_path):
                try:
                    venv_output = subprocess.run(
                        ["python3", "-m", "venv", venv_path],
                        cwd=abs_working_dir,
                        timeout=30,
                        capture_output=True,
                        text=True
                    )
                    if venv_output.returncode != 0:
                        return {
                            "error": f"Failed to create virtual environment: {venv_output.stderr}",
                            "stdout": venv_output.stdout,
                            "stderr": venv_output.stderr
                        }
                except Exception as e:
                    return {"error": f"Error creating virtual environment: {e}"}
    
    # Build command list
    if use_venv and command in ["pip", "python3", "python"]:
        # Use venv's pip/python
        if command == "pip":
            if os.name == 'nt':  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip")
            else:  # Unix/Mac
                pip_path = os.path.join(venv_path, "bin", "pip")
            cmd_list = [pip_path]
            # Add args for pip
            if args:
                if isinstance(args, list):
                    cmd_list.extend(args)
                else:
                    cmd_list.append(args)
        else:  # python3 or python with -m pip
            if os.name == 'nt':
                python_path = os.path.join(venv_path, "Scripts", "python")
            else:
                python_path = os.path.join(venv_path, "bin", "python")
            cmd_list = [python_path, "-m", "pip"]
            # Add remaining args (skip -m pip if present)
            if args:
                args_list = args if isinstance(args, list) else [args]
                # Skip -m and pip if they're in args
                filtered_args = [a for a in args_list if a not in ["-m", "pip"]]
                cmd_list.extend(filtered_args)
    else:
        cmd_list = [command]
        if args is not None:
            # Handle both list and single string args
            if isinstance(args, list):
                cmd_list.extend(args)
            elif isinstance(args, str):
                cmd_list.append(args)
            else:
                return {"error": f"Invalid args type: {type(args)}. Expected list or string."}
    
    try:
        output = subprocess.run(
            cmd_list,
            cwd=abs_working_dir,
            timeout=60,
            capture_output=True,
            text=True
        )
        result = {
            "stdout": output.stdout,
            "stderr": output.stderr,
            "exit_code": output.returncode,
            "success": output.returncode == 0
        }
        # Add note about venv if used
        if use_venv:
            result["note"] = "Used virtual environment (.venv) for package installation"
        return result
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 60 seconds"}
    except FileNotFoundError:
        return {"error": f"Error: Command '{command}' not found. Make sure it's installed and in your system's PATH."}
    except Exception as e:
        return {"error": f"Error executing command: {e}"}


schema_run_command = types.FunctionDeclaration(
    name="run_command",
    description="Run a shell command in the working directory. Useful for running tests (pytest, npm test), installing dependencies (pip install, npm install), or any other shell commands. Returns stdout, stderr, exit code, and success status.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "command": types.Schema(
                type=types.Type.STRING,
                description="The command to run (e.g., 'pytest', 'pip', 'npm', 'python3', etc.)",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Optional list of arguments to pass to the command (e.g., ['install', '-r', 'requirements.txt'] for pip, or ['test_calculator.py'] for pytest)",
            ),
        },
        required=["command"],
    ),
)

