from google.genai import types
from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_file import write_file
from functions.run_program_file import run_program_file
from functions.get_file_overview import get_file_overview
from functions.search_in_file import search_in_file
from functions.run_command import run_command


def call_function(function_call_part, working_directory):
    """
    Call a function and return a properly formatted function response.
    The response must match the function call structure exactly.
    """
    result = None

    if function_call_part.name == "get_files_info":
        result = get_files_info(working_directory, **function_call_part.args)
    elif function_call_part.name == "get_file_content":
        result = get_file_content(working_directory, **function_call_part.args)
    elif function_call_part.name == "write_file":
        result = write_file(working_directory, **function_call_part.args)
    elif function_call_part.name == "run_program_file":
        result = run_program_file(working_directory, **function_call_part.args)
    elif function_call_part.name == "get_file_overview":
        result = get_file_overview(working_directory, **function_call_part.args)
    elif function_call_part.name == "search_in_file":
        result = search_in_file(working_directory, **function_call_part.args)
    elif function_call_part.name == "run_command":
        result = run_command(working_directory, **function_call_part.args)

    # Create function response part - must match the function call part structure
    # Check if function_call_part has an id attribute (for matching)
    function_response_kwargs = {
        "name": function_call_part.name,
        "response": {"result": result} if result is not None else {"error": f"Unknown function: {function_call_part.name}"}
    }
    
    # If function_call_part has an id, include it in the response
    if hasattr(function_call_part, 'id') and function_call_part.id:
        function_response_kwargs["id"] = function_call_part.id

    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(**function_response_kwargs)
        ],
    )
