import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.write_file import schema_write_file
from functions.run_python_file import schema_run_python_file
from call_function import call_function
from app.models import Session as SessionModel
from app.database import db_dependency
from fastapi import HTTPException
from datetime import datetime
from datetime import timezone
class GeminiAgentService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
    
    async def execute(self, prompt: str, session_id: str, db: db_dependency=None):
        
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        working_directory = session.clone_path
        if not os.path.exists(working_directory):
            raise HTTPException(status_code=404, detail="Cloned repository not found")

        yield {
            "type": "agent_started",
            "message": f"Starting agent execution: {prompt[:50]}...",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id
        }

        system_prompt = """
        You are a helpful AI coding agent.

        When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

        - List files and directories
        - Read the content of a file
        - Write to a file (create or update)
        - Run a python file with optional arguments

        When the user asks about the code project - they are referring to the
        working directory. So, you should typically start by looking at the 
        project's files, and figuring out how to run the project and how to run its tests,
        you'll always want to test the tests and the actual project to verify that behavior is as expected.

        All paths you provide should be relative to the working directory. 
        You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
        """
        
        messages = [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]

        available_functions = types.Tool(
            function_declarations=[
                schema_get_files_info,
                schema_get_file_content,
                schema_write_file,
                schema_run_python_file,
            ]
        )

        config = types.GenerateContentConfig(
            tools=[available_functions], system_instruction=system_prompt
        )

        max_iters = 20
        function_calls = []
        agent_responses = []

        try:
            for i in range(0, max_iters):
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash-001",
                    contents=messages,
                    config=config,
                )
                
                if response is None or response.usage_metadata is None:
                    yield {
                        "status": "error",
                        "message": "Response is malformed",
                        "function_calls": function_calls,
                        "agent_responses": agent_responses
                    }
                    return

                if response.candidates:
                    for candidate in response.candidates:
                        if candidate is None or candidate.content is None:
                            continue
                        messages.append(candidate.content)
                        agent_responses.append(candidate.content.text if candidate.content.text else str(candidate.content))
                
                if response.function_calls:
                    for function_call_part in response.function_calls:
                        function_calls.append({
                            "function_name": function_call_part.name,
                            "arguments": function_call_part.args
                        })
                        
                        result = call_function(function_call_part, working_directory)
                        messages.append(result)
                else:
                    yield {
                        "status": "completed",
                        "message": response.text if response.text else "Task completed",
                        "function_calls": function_calls,
                        "agent_responses": agent_responses,
                        "working_directory": working_directory
                    }
                    return 
            
            yield {
                "status": "max_iterations_reached",
                "message": "Agent reached maximum iterations",
                "function_calls": function_calls,
                "agent_responses": agent_responses,
                "working_directory": working_directory
            }
            
        except Exception as e:
            yield {
                "status": "error",
                "message": f"Agent execution failed: {str(e)}",
                "function_calls": function_calls,
                "agent_responses": agent_responses,
                "working_directory": working_directory
            }

