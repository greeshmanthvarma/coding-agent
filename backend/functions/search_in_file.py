import os
from google.genai import types 
import re


def search_in_file(working_directory,file_path,pattern,context_lines=0,case_sensitive=True,max_results=200):
    abs_working_dir= os.path.abspath(working_directory)
    abs_file_path= os.path.abspath(os.path.join(working_directory, file_path))

    if not abs_file_path.startswith(abs_working_dir):
        return {"error": f'"{file_path}" is not in the working dir'}

    if not os.path.isfile(abs_file_path):
        return {"error": f'"{file_path}" is not a file'}

    # Validate pattern
    if not pattern:
        return {"error": "Pattern cannot be empty"}

    try:
        # Compile regex pattern with appropriate flags
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags) #since we are using the regex pattern to search for in the file multiple times, we compile it once and use it multiple times.
        except re.error as e:
            return {"error": f"Invalid regex pattern: {pattern}: {e}"}

        with open(abs_file_path, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.readlines()
        
        matches = []
        for i, line in enumerate(file_content):
            # Keep original line for display, search on it
            match = regex.search(line)
            if match:
                # Get match positions
                start_index, end_index = match.span() #span() returns a tuple of the start and end indices of the match.
                
                # Collect context (before and after, excluding match line)
                context_before = []
                context_after = []
                if context_lines > 0:
                    # Lines before the match (excluding match line)
                    start_ctx = max(0, i - context_lines)
                    context_before = [line.rstrip() for line in file_content[start_ctx:i]] #rstrip() removes trailing whitespace from the line.
                    
                    # Lines after the match (excluding match line)
                    end_ctx = min(len(file_content), i + 1 + context_lines)
                    context_after = [line.rstrip() for line in file_content[i + 1:end_ctx]]
                
                matches.append({
                    'line_number': i + 1,
                    'content': line.rstrip(),  
                    'match': match.group(0),
                    'start_index': start_index,
                    'end_index': end_index,
                    'context': {
                        'before': context_before,
                        'after': context_after
                    }
                })
                
                # Only count matches, not context
                if len(matches) >= max_results:
                    break
        
        return {
            'matches': matches,
            'total_matches': len(matches),
            'truncated': len(matches) >= max_results
        }
    except Exception as e:
        return {"error": f"Exception searching in file: {file_path} for pattern: {pattern}: {e}"}

schema_search_in_file = types.FunctionDeclaration(
    name="search_in_file",
    description="Searches for a regex pattern in a file, constrained to the working directory. Returns matches with line numbers, positions, and optional context.",  
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={    
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file from the working directory.",
            ),
            "pattern": types.Schema(
                type=types.Type.STRING,
                description="The regex pattern to search for in the file.",
            ),  
            "context_lines": types.Schema(
                type=types.Type.INTEGER,
                description="The number of lines of context to include before and after each match. Default: 0.",
                default=0
            ),
            "case_sensitive": types.Schema(
                type=types.Type.BOOLEAN,
                description="Whether the search should be case sensitive. Default: true.",
                default=True
            ),
            "max_results": types.Schema(
                type=types.Type.INTEGER,
                description="The maximum number of matches to return. Default: 200.",
                default=200
            ),
        },
    ),
)