import os
from google.genai import types 
import re


def search_in_file(working_directory,file_path,pattern,context_lines=0,case_sensitive=True,max_results=200):
    abs_working_dir= os.path.abspath(working_directory)
    abs_file_path= os.path.abspath(os.path.join(working_directory, file_path))

    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working dir'

    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'

    try:
        with open(abs_file_path,'r') as f:
            file_content=f.readlines()
        
        results=[]
        for i,line in enumerate(file_content):
            line=line.strip()
            if not case_sensitive:
                line=line.lower()
                
            match= re.search(pattern, line)
            if match:
                results.append({'line':i+1,'content':line,'match':match.group(0)})
                if context_lines > 0: #context_line is the number of lines of context to include before and after the match. 
                    start_line=max(0,i-context_lines) #if the context lines are less than 0, set it to 0. 
                    end_line=min(i+context_lines,len(file_content)-1) #if the context lines are greater than the number of lines in the file, set it to the number of lines in the file
                    results.append({'context':file_content[start_line:end_line]}) 
                if len(results) >= max_results:
                    break
        return results
    except Exception as e:
        return f"Exception searching in file: {file_path} for pattern: {pattern}: {e}"

schema_search_in_file = types.FunctionDeclaration(
    name="search_in_file",
    description="Searches for a pattern in a file, constrained to the working directory. Returns a list of lines that match the pattern.",  
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={    
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file from the working directory.",
            ),
            "pattern": types.Schema(
                type=types.Type.STRING,
                description="The pattern to search for in the file.",
            ),  
            "context_lines": types.Schema(
                type=types.Type.INTEGER,
                description="The number of lines of context to include before and after the match.",
            ),
            "case_sensitive": types.Schema(
                type=types.Type.BOOLEAN,
                description="Whether the search should be case sensitive.",
            ),
            "max_results": types.Schema(
                type=types.Type.INTEGER,
                description="The maximum number of results to return.",
            ),
        },
    ),
)