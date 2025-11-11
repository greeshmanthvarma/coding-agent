import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.write_file import schema_write_file
from functions.run_program_file import schema_run_program_file
from functions.get_file_overview import schema_get_file_overview
from functions.search_in_file import schema_search_in_file
from app.services.call_function import call_function
from app.models import Session as SessionModel
from app.models import Message as MessageModel
from app.database import db_dependency
from fastapi import HTTPException
from datetime import datetime
from datetime import timezone
from app.database import redis_dependency
from redis.commands.search.query import Query
import redis
from sqlalchemy.orm import Session
import json
import uuid
from redis.commands.json.path import Path
from app.utils.git_utils import get_current_commit_hash, get_git_status, revert_to_checkpoint, commit_changes, push_changes
from app.models import Review as ReviewModel

class GeminiAgentService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)

    def _load_raw_messages(self, session_id: str, redis_client: redis.Redis, db: Session):
        """
        Internal helper: Load raw messages from cache or DB (cache-first).
        Returns list of dicts with 'role', 'content', 'sequence', 'created_at'.
        """
        # Try Redis cache first
        try:
            query = Query(f"@session_id:{{{session_id}}}").sort_by("sequence", asc=True)
            search_result = redis_client.ft("idx:messages").search(query)
            
            if search_result and search_result.docs:
                messages = []
                for doc in search_result.docs:
                    message_data = json.loads(doc.json) if hasattr(doc, 'json') else doc
                    messages.append({
                        "role": message_data.get("sender", "user"),
                        "content": message_data.get("message", ""),
                        "sequence": message_data.get("sequence", 0),
                        "created_at": None 
                    })
                return messages
        except Exception:
            pass
        
        # Fallback to PostgreSQL
        try:
            db_messages = db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).order_by(MessageModel.sequence.asc()).all()
            
            messages = []
            for db_message in db_messages:
                messages.append({
                    "role": db_message.sender,
                    "content": db_message.message,
                    "sequence": db_message.sequence,
                    "created_at": db_message.created_at.isoformat() if db_message.created_at else None
                })
            return messages
        except Exception:
            return []

    def load_messages(self, session_id: str, redis_client: redis.Redis, db: Session):
        """
        Load previous messages from Redis cache first, if not found, load from PostgreSQL.
        Returns list of Gemini types.Content objects (for agent execution).
        """
        raw_messages = self._load_raw_messages(session_id, redis_client, db)
        
        gemini_messages = []
        for msg in raw_messages:
            gemini_messages.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part(text=msg["content"])]
                )
            )
        return gemini_messages
    
    def get_messages_for_api(self, session_id: str, redis_client: redis.Redis, db: Session):
        """
        Get messages in frontend-friendly format (cache-first, then DB).
        Returns list of dicts with 'role', 'content', 'sequence', 'created_at'.
        """
        return self._load_raw_messages(session_id, redis_client, db)

    def _get_next_sequence(self, session_id: str, redis_client: redis.Redis, db: Session):
        """Get the next sequence number for a session from Redis or DB."""
        try:
            query = Query(f"@session_id:{{{session_id}}}").sort_by("sequence", desc=True).limit(1)
            search_result = redis_client.ft("idx:messages").search(query)
            if search_result and search_result.docs:
                message_data = json.loads(search_result.docs[0].json) if hasattr(search_result.docs[0], 'json') else search_result.docs[0]
                return message_data.get("sequence", -1) + 1
        except Exception:
            pass
    
        try:
            last_message = db.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).order_by(MessageModel.sequence.desc()).first()
            if last_message:
                return last_message.sequence + 1
        except Exception:
            pass
        
        return 0  

    def save_message_cache(self, message: types.Content, session_id: str, sequence: int, redis_client: redis.Redis):
        """Save a message to the Redis cache."""
        try:
            message_id = str(uuid.uuid4())
            redis_client.json().set(
                f"message:{message_id}",
                Path.root_path(),
                {
                    "message": message.parts[0].text,
                    "sender": message.role,
                    "session_id": session_id,
                    "sequence": sequence
                }
            )
        except Exception:
            pass
       
    def save_message_db(self, message: types.Content, session_id: str, sequence: int, db: Session):
        """Save a message to the database."""
        try:
            
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                return 
            
            message_id = str(uuid.uuid4())
            db_message = MessageModel(
                id=message_id,
                message=message.parts[0].text,
                sender=message.role,
                session_id=session_id,
                user_id=session.user_id,  
                sequence=sequence
            )
            db.add(db_message)
            db.commit()
        except Exception:
            db.rollback()
            pass
   
    async def execute(self, prompt: str, session_id: str, db: db_dependency=None, redis: redis_dependency=None):
        
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        working_directory = session.clone_path
        if not os.path.exists(working_directory):
            raise HTTPException(status_code=404, detail="Cloned repository not found")

        checkpoint =get_current_commit_hash(working_directory)
        if "error" in checkpoint:
            yield{
                "type" : "error",
                "message": f"Error getting current commit hash: {checkpoint.get('error')}"
            }
            return
        
        checkpoint_commit_hash=checkpoint.get("commit_hash")

        review_id = str(uuid.uuid4())
        review= ReviewModel(
            id=review_id,
            session_id=session_id,
            user_id=session.user_id,
            prompt=prompt,
            changes="",
            checkpoint_commit_hash=checkpoint_commit_hash,
            status="pending_review",
            created_at=datetime.now(timezone.utc),
            approved_at = None,
            rejected_at = None,
            commit_message=None,
            branch_name=None
        )
        db.add(review)
        db.commit()

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
        
       
        previous_messages = self.load_messages(session_id, redis, db)
        
        user_message = types.Content(role="user", parts=[types.Part(text=prompt)])
        messages = previous_messages + [user_message]
       
      
        user_sequence = self._get_next_sequence(session_id, redis, db)
        self.save_message_cache(user_message, session_id, user_sequence, redis)
        self.save_message_db(user_message, session_id, user_sequence, db)
       
        available_functions = types.Tool(
            function_declarations=[
                schema_get_files_info,
                schema_get_file_content,
                schema_write_file,
                schema_run_program_file,
                schema_get_file_overview,
                schema_search_in_file,
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
                    changes=get_git_status(working_directory)

                    if changes and "error" not in changes:
                        changes_json=json.dumps(changes)
                    else:
                        changes_json = json.dumps({"error": changes.get("error", "Unknown error")}) if changes else None

                    review.changes=changes_json
                    db.commit()

                    agent_response_text = response.text if response.text else "Task completed"
                    agent_message = types.Content(role="model", parts=[types.Part(text=agent_response_text)])
                    
                    yield {
                        "status": "completed",
                        "message": agent_response_text,
                        "function_calls": function_calls,
                        "agent_responses": agent_responses,
                        "working_directory": working_directory,
                        "review_id": review_id
                    }
                    agent_sequence = user_sequence + 1
                    self.save_message_cache(agent_message, session_id, agent_sequence, redis)
                    self.save_message_db(agent_message, session_id, agent_sequence, db)
                    
                    return 
            
            yield {
                "status": "max_iterations_reached",
                "message": "Agent reached maximum iterations",
                "function_calls": function_calls,
                "agent_responses": agent_responses,
                "working_directory": working_directory,
                "review_id": review_id
            }
            
        except Exception as e:
            yield {
                "status": "error",
                "message": f"Agent execution failed: {str(e)}",
                "function_calls": function_calls,
                "agent_responses": agent_responses,
                "working_directory": working_directory,
                "review_id": review_id
            }

