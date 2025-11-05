import os
import subprocess
from google.genai import types 

def run_python_file(working_directory:str, file_path:str):
    abs_working_dir= os.path.abspath(working_directory)
    abs_file_path= os.path.abspath(os.path.join(working_directory, file_path))

    if not abs_file_path.startswith(abs_working_dir):
        return {"error": f'Error: "{file_path}" is not in the working dir'}

    if not os.path.isfile(abs_file_path):
        return {"error": f'Error: "{file_path}" is not a file'}

    if file_path.endswith(".py"):
        language_type="python3"
       
    elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        language_type="node"
    else:
        return {"error": f'Error: "{file_path}" is not a supported file type'}

    try:
        output=subprocess.run([language_type, file_path], cwd=abs_working_dir, timeout=30, capture_output=True, check=True, text=True)
        result={"stdout":output.stdout,"stderr":output.stderr}
        return result
    except subprocess.CalledProcessError as e:
        return {"error": f"Command failed with exit code {e.returncode}", "stderr": e.stderr}
    except FileNotFoundError:
        return {"error": f"Error: {language_type} executable not found. Make sure {language_type} is installed and in your system's PATH."}
    except Exception as e:
        return {"error": f"Error executing {language_type} file: {e}"}


schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Runs a file with the python3 or node interpreter depending on the file extension.Returns the stdout and stderr of the command.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file to run, relative to the working directory.",
            ),
        },
    ),
)