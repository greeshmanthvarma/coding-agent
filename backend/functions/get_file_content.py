import os
from google.genai import types 
from config import MAX_CHARS


def get_file_content(working_directory, file_path, start_line=0,end_line=None,search_text=None):
    abs_working_dir= os.path.abspath(working_directory)
    abs_file_path= os.path.abspath(os.path.join(working_directory, file_path))

    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working dir'

    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'
    try:
        with open(abs_file_path,'r') as f:
            file_content=f.readlines()
            if start_line > 0:
                file_content=file_content[start_line:]
            if end_line is not None:
                file_content=file_content[:end_line]
            file_content_string="\n".join(file_content)
            return file_content_string
        
    except Exception as e:
        return f"Exception reading lines {start_line} to {end_line} from file: {file_path}: {e}"
        
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Gets the contents of the given file as a string, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file from the working directory.",
            ),
        },
    ),
)