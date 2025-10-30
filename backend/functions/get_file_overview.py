
import os
from google.genai import types 
import re

def get_file_overview(working_directory, file_path):
    abs_working_dir= os.path.abspath(working_directory)
    abs_file_path= os.path.abspath(os.path.join(working_directory, file_path))

    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working dir'

    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'

    functions =[]
    classes= []

    try:
        with open(abs_file_path,'r') as f:
            file_content=f.readlines()

        for i,line in enumerate(file_content):
            line=line.strip()

            if re.match(r'^\s*(def|function|func)\s+\w+',line):
                name=extract_name(line)
                if name:
                    functions.append({'name':name,'line':i+1})

            if re.match(r'^\s*(class|type)\s+\w+',line):
                name=extract_name(line)
                if name:
                    classes.append({'name':name,'line':i+1})

        return {
        'functions':functions,
        'classes':classes,
        'total_lines':len(file_content),
        }
    except Exception as e:
        return f"Exception parsing functions and classes from file: {file_path}: {e}"

def extract_name(line):
    match= re.search(r'^\s*(def|function|func|class|type\s+\w+)\s+(\w+)',line)
    if match:
        return match.group(2)
    else:
        return None

schema_get_file_overview = types.FunctionDeclaration(
    name="get_file_overview",
    description="Gets an overview of functions and classes in a file, constrained to the working directory.",
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
