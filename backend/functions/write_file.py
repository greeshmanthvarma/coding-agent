import os
from google.genai import types 

def write_file(working_directory, file_path,content,append=False):
    abs_working_dir= os.path.abspath(working_directory)
    abs_file_path= os.path.abspath(os.path.join(working_directory, file_path))

    if not abs_file_path.startswith(abs_working_dir):
        return {"error": f'Error: "{file_path}" is not in the working dir'}

    parent_dir = os.path.dirname(abs_file_path)
    
    if not os.path.isdir(parent_dir): #if the dir doesn't exist, create it
        try:
            os.makedirs(parent_dir) #creates a dir and all its parents
        except Exception as e:
            return {"error": f"Could not create parent dirs: {parent_dir}= {e}"}
    try:
        with open(abs_file_path, 'a' if append else 'w',encoding='utf-8',errors='replace') as f:
            if append:
                f.write(content + "\n")
            else:
                f.write(content)

        return {"message": f'Successfully wrote to "{file_path}" ({len(content)}) characters'}
    except Exception as e:
        return {"error": f"Failed to write to file: {file_path}, {e}"}

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes content to a file. By default (append=False), overwrites the entire file. If append=True, appends content to the end of the file. Creates the file and required parent directories if they don't exist. All operations are constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to write, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The contents to write to the file as a string",
            ),
            "append": types.Schema(
                type=types.Type.BOOLEAN,
                description="Whether to append to the file if it already exists. Default: false.",
                default=False,
            ),
        },
    ),
)
