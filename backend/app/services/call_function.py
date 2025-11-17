from google.genai import types
from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_file import write_file
from functions.run_program_file import run_program_file
from functions.get_file_overview import get_file_overview
from functions.search_in_file import search_in_file
from functions.run_command import run_command


def call_function(function_call_part, working_directory):

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

    if result is None:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        ) 

    return types.Content(
    role="tool",
    parts=[
        types.Part.from_function_response(
            name=function_call_part.name,
            response={"result": result},
        )
    ],
    )
