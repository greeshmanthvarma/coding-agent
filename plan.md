# RepoRefine - AI-Powered Code Refinement Platform

## Overview

**RepoRefine** is an AI-powered platform that helps developers improve their code through intelligent automation. Users authenticate with GitHub, clone their repositories, and use AI-guided refinements to enhance their codebase. All changes are reviewed before committing back to GitHub.

## Human-in-the-Loop Confirmation System

**RepoRefine** includes a comprehensive human-in-the-loop confirmation system that allows users to review, approve, or reject every AI agent change before it's committed to their repository. This ensures safety, quality control, and user trust while maintaining the efficiency of AI automation.

### Enhanced Workflow

**Current Flow:**
```
User Prompt → Agent Execution → Auto Commit → Push
```

**Enhanced Flow with Human Confirmation:**
```
User Prompt → Agent Execution → Human Review → Confirm/Reject → Commit/Push
```

### Key Features

- **Review Every Change**: Users see exactly what the AI agent will do before it's committed
- **Granular Control**: Approve or reject individual changes
- **Modify Suggestions**: Edit agent suggestions before committing
- **Visual Diff Viewer**: Cursor-style red/green highlighting for clear change visualization
- **Review History**: Track all agent actions and user decisions
- **Safety First**: Prevent unwanted changes and maintain code quality

## Architecture Overview

Transform the existing CLI-based AI coding agent into a full-stack web application with:

- **Frontend**: Vite + React + JavaScript + TailwindCSS
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL + SQLAlchemy + Alembic
- **Containerization**: Docker + Docker Compose
- **AI Agent**: Refactored Gemini agent (existing code) exposed via API
- **GitHub Integration**: OAuth authentication + repository operations
- **Testing**: pytest (backend) + Vitest (frontend)
- **CI/CD**: GitHub Actions
- **Human-in-the-Loop**: Review and confirmation system for all AI changes

## Backend Implementation (FastAPI)

### 1. Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings (GitHub OAuth, secrets)
│   ├── models.py            # Pydantic models
│   ├── routers/
│   │   ├── auth.py          # GitHub OAuth endpoints
│   │   ├── repos.py         # Repository operations
│   │   └── agent.py         # AI agent execution
│   ├── services/
│   │   ├── github_service.py   # GitHub API integration
│   │   ├── agent_service.py    # Gemini agent wrapper
│   │   └── session_service.py  # Session management
│   └── utils/
│       ├── clone.py         # Git clone/operations
│       └── cleanup.py       # Temp directory cleanup
├── requirements.txt
└── .env.example
```

### 2. Key Backend Features

**GitHub OAuth Flow** (`routers/auth.py`):

- `/auth/github` - Redirect to GitHub OAuth
- `/auth/callback` - Handle OAuth callback, exchange code for token
- `/auth/user` - Get authenticated user info
- Store access tokens securely (encrypted session/JWT)

**Repository Operations** (`routers/repos.py`):

- `GET /repos` - List user's repositories
- `POST /repos/clone` - Clone repository to temp directory
- `GET /repos/{session_id}/files` - Browse cloned repo files
- `GET /repos/{session_id}/status` - Get git status of changes

**AI Agent Execution** (`routers/agent.py`):

- `POST /agent/execute` - Run agent with user prompt on cloned repo
- `GET /agent/status/{task_id}` - Check execution status (support long-running tasks)
- `WebSocket /agent/stream` - Real-time agent output streaming

**Human-in-the-Loop Review System** (`routers/agent.py`):

- `POST /agent/execute` - Enhanced with `auto_commit` parameter (default: false)
- `POST /agent/review/{review_id}` - Approve or reject changes
- `GET /agent/review/{review_id}` - Get review details and changes
- `POST /agent/review/{review_id}/modify` - Allow users to modify agent suggestions

**Commit & Push** (`routers/repos.py`):

- `POST /repos/{session_id}/commit` - Create commit with changes
- `POST /repos/{session_id}/push` - Push to new branch
- `POST /repos/{session_id}/cleanup` - Clean temp directory

### 3. Enhanced Agent Workflow with Human Confirmation

**New Agent Execution Endpoint:**
```python
@user_router.post("/agent/execute")
async def execute_agent(
    prompt: str, 
    session_id: str, 
    auto_commit: bool = False,
    current_user: UserModel = Depends(get_current_user),
    db: db_dependency = None
):
    """
    Execute AI agent with optional human review
    
    Parameters:
    - prompt: User's instruction for the AI agent
    - session_id: Cloned repository session
    - auto_commit: If True, auto-commit changes (bypass human review)
    """
    try:
        # Run agent and get changes
        agent_result = await agent_service.execute(prompt, session_id)
        
        if auto_commit:
            # Auto-commit mode (current behavior)
            return await commit_changes(session_id, agent_result)
        else:
            # Human review mode - return changes for review
            review_id = str(uuid.uuid4())
            
            # Store review in database
            review = ReviewModel(
                id=review_id,
                session_id=session_id,
                user_id=current_user.id,
                prompt=prompt,
                changes=agent_result,
                status="pending_review",
                created_at=datetime.now(timezone.utc)
            )
            db.add(review)
            db.commit()
            
            return {
                "status": "pending_review",
                "changes": agent_result,
                "session_id": session_id,
                "review_id": review_id,
                "message": "Changes ready for review. Use /agent/review/{review_id} to approve or reject."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@user_router.post("/agent/review/{review_id}")
async def review_changes(
    review_id: str, 
    action: str, 
    session_id: str,
    commit_message: str = None,
    branch_name: str = None,
    current_user: UserModel = Depends(get_current_user),
    db: db_dependency = None
):
    """
    Review and approve/reject agent changes
    
    Parameters:
    - review_id: Unique review identifier
    - action: "approve" or "reject"
    - session_id: Cloned repository session
    - commit_message: Custom commit message (optional)
    - branch_name: Custom branch name (optional)
    """
    try:
        review = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        if action == "approve":
            # Commit changes
            result = await commit_changes(
                session_id, 
                review.changes, 
                commit_message, 
                branch_name
            )
            review.status = "approved"
            review.approved_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "status": "approved",
                "message": "Changes approved and committed",
                "commit_result": result
            }
        elif action == "reject":
            # Reject changes
            review.status = "rejected"
            review.rejected_at = datetime.now(timezone.utc)
            db.commit()
            
            return {
                "status": "rejected",
                "message": "Changes rejected"
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")

@user_router.get("/agent/review/{review_id}")
async def get_review_details(
    review_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: db_dependency = None
):
    """Get detailed review information and changes"""
    try:
        review = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        return {
            "review_id": review.id,
            "session_id": review.session_id,
            "prompt": review.prompt,
            "changes": review.changes,
            "status": review.status,
            "created_at": review.created_at,
            "approved_at": review.approved_at,
            "rejected_at": review.rejected_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get review: {str(e)}")
```

### 4. Tool Enhancement Phase

**BEFORE** refactoring the agent, enhance the existing tools to be more powerful and versatile.

#### 4.1 Fix Existing Bugs

- Fix typo in `get_file_content.py` line 26: `[e]` → `{e}`
- Fix typo in `write_file.py` line 24: "Failes" → "Failed"

#### 4.2 Enhance `get_files_info`

Add new parameters:

- `recursive` (bool): Return full directory tree structure
- `exclude_patterns` (array): Skip patterns like `[".git", "node_modules", "__pycache__", "*.pyc"]`
- `file_types` (array): Filter by extensions like `[".py", ".js", ".tsx"]`
- `include_metadata` (bool): Add last modified time, permissions

Return structured JSON format instead of string:

```json
{
  "files": [
    {"path": "src/main.py", "size": 1024, "is_dir": false, "modified": "2025-10-23T10:30:00"}
  ],
  "total_files": 42,
  "total_size": 51200
}
```

#### 4.3 Enhance `get_file_content`

Add new parameters:

- `start_line` (int): Read from specific line
- `end_line` (int): Read until specific line
- `max_chars` (int): Configurable limit (override MAX_CHARS constant)

Improvements:

- Detect binary files (return metadata instead of crashing)
- Return encoding information
- Better error messages

#### 4.4 Enhance `write_file`

Add new parameters:

- `mode` (string): "write" (default) or "append"
- `create_backup` (bool): Backup existing file before overwriting

Return more info:

- Git diff preview of changes
- Success with before/after file sizes

#### 4.5 Expand `run_python_file` → `run_command`

Create new universal command tool:

**New tool: `run_command`**

- Execute any shell command safely (npm test, pytest, cargo build, make, etc.)
- Parameters:
        - `command` (string): Command to run
        - `args` (array): Command arguments
        - `timeout` (int): Configurable timeout (default 30s)
        - `env_vars` (dict): Additional environment variables
        - `shell` (bool): Whether to use shell execution

Keep `run_python_file` as a wrapper around `run_command` for backward compatibility.

Security: Maintain working directory sandboxing, add command whitelist/validation.

#### 4.6 New Tools to Add

**`search_in_files`**:

- Search for text/regex patterns across files
- Parameters: `query`, `file_pattern` (glob), `case_sensitive`, `max_results`
- Essential for "find all occurrences" tasks
- Return: `[{"file": "path", "line": 42, "content": "...", "match": "..."}]`

**`delete_file`**:

- Delete files or directories
- Parameters: `path`, `recursive` (for directories)
- Safety: Prevent deletion of sensitive files (.git, etc.)

**`git_operations`**:

- Expose git commands as structured tool
- Subcommands: `status`, `diff`, `log`, `add`, `reset`
- Return structured JSON output (not raw git text)
- Makes git operations explicit and trackable in UI

**`install_dependencies`**:

- Install project dependencies
- Auto-detect package manager (package.json → npm, requirements.txt → pip, etc.)
- Parameters: `package_manager` (optional override), `packages` (optional specific packages)
- Essential for setting up cloned projects

#### 4.7 Refactor Tool Structure

- Move from string responses to JSON responses throughout
- Create base `Tool` class with common functionality (path validation, error handling)
- Separate tool implementation from schema definition
- Add tool result metadata (execution time, status codes)

### 5. Agent Service Refactoring

Refactor existing `main.py` agent into reusable service (`services/agent_service.py`):

- Extract agent logic into class `GeminiAgentService`
- Make working directory configurable (use cloned repo path)
- Return structured responses instead of printing
- Support streaming responses for real-time updates
- Add session management to track multiple concurrent operations

**Key changes**:

- Convert `main()` function to `AgentService.execute(prompt, working_dir, session_id)`
- Capture function call results and agent responses in structured format
- Add WebSocket support for streaming agent thoughts/actions
- Use enhanced tool implementations with JSON responses

### 6. Session Management

Create session system for tracking cloned repos:

- Each clone gets unique `session_id`
- Store: repo URL, clone path, user token, timestamp
- Auto-cleanup sessions older than 1 hour
- Background task to monitor and clean temp directories

## Frontend Implementation (React)

### 1. Project Structure

```
frontend/
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── components/
│   │   ├── Auth/
│   │   │   ├── LoginButton.jsx
│   │   │   └── UserProfile.jsx
│   │   ├── Repos/
│   │   │   ├── RepoList.jsx
│   │   │   ├── RepoCard.jsx
│   │   │   └── CloneModal.jsx
│   │   ├── Agent/
│   │   │   ├── PromptInput.jsx
│   │   │   ├── AgentOutput.jsx
│   │   │   ├── FunctionCallLog.jsx
│   │   │   └── ReviewControls.jsx
│   │   ├── Files/
│   │   │   ├── FileExplorer.jsx
│   │   │   ├── FileViewer.jsx
│   │   │   └── DiffViewer.jsx
│   │   └── Commit/
│   │       ├── ReviewChanges.jsx
│   │       ├── CommitForm.jsx
│   │       └── PushOptions.jsx
│   ├── hooks/
│   │   ├── useAuth.js
│   │   ├── useAgent.js
│   │   ├── useWebSocket.js
│   │   └── useReview.js
│   ├── services/
│   │   └── api.js          # Axios/fetch API client
│   └── styles/
├── package.json
├── vite.config.js
└── .env.example
```

### 2. User Flow & Pages

**Page 1: Authentication**

- Show "Login with GitHub" button
- Redirect to backend OAuth endpoint
- After callback, store user token (in memory/session storage)
- Display user profile

**Page 2: Repository Selection**

- List user's GitHub repositories
- Search/filter functionality
- "Clone & Work" button for each repo
- Show loading state during clone operation

**Page 3: Agent Workspace (Enhanced with Review)**

- Left sidebar: File explorer showing cloned repo structure
- Center: Prompt input + agent output area with review controls
- Right sidebar: Function call log (showing agent actions)
- Real-time streaming of agent responses via WebSocket
- Display each function call (reading files, writing files, running tests)
- **NEW**: Review controls for each agent action

**Page 4: Review & Commit (Enhanced)**

- Show git diff of all changes
- Syntax-highlighted diff viewer with Cursor-style highlighting
- **NEW**: Individual change approval/rejection
- **NEW**: Modify agent suggestions before committing
- Commit message input
- Branch name input (default: `ai-agent-changes-{timestamp}`)
- "Commit & Push" button
- Success message with link to new branch on GitHub

### 3. Key Frontend Features

**Authentication Hook** (`useAuth.js`):

- Manage OAuth flow state
- Store/retrieve access token
- Provide user info and logout

**Agent Hook** (`useAgent.js`):

- Execute agent with prompt
- Handle WebSocket connection for real-time updates
- Parse and display function calls
- Track execution status
- **NEW**: Handle review workflow

**WebSocket Integration** (`useWebSocket.js`):

- Connect to backend WebSocket endpoint
- Handle agent streaming messages
- Display real-time progress

**Review Hook** (`useReview.js`):

- Manage review state and actions
- Handle approve/reject workflow
- Track review history

**UI/UX**:

- Modern, clean interface with Tailwind CSS
- Loading states and progress indicators
- Error handling with user-friendly messages
- Responsive design
- **NEW**: Cursor-style diff viewer with red/green highlighting

### 4. Enhanced Chat Interface with Review Controls

**AgentMessage.jsx - Enhanced with review controls:**
```jsx
function AgentMessage({ message }) {
  const [isReviewing, setIsReviewing] = useState(false);
  
  return (
    <div className="flex justify-start">
      <div className="bg-gray-100 p-3 rounded-lg max-w-3xl">
        <div className="font-medium text-gray-700 mb-2">AI Agent</div>
        <div>{message.content}</div>
        
        {message.changes && (
          <div className="mt-4">
            <div className="font-medium text-gray-700 mb-2">Changes Made:</div>
            <DiffViewer changes={message.changes} />
            
            <div className="mt-4 flex space-x-2">
              <button 
                onClick={() => handleApprove(message.review_id)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg"
              >
                ✅ Approve Changes
              </button>
              <button 
                onClick={() => handleReject(message.review_id)}
                className="bg-red-600 text-white px-4 py-2 rounded-lg"
              >
                ❌ Reject Changes
              </button>
              <button 
                onClick={() => setIsReviewing(!isReviewing)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg"
              >
                🔍 Review Details
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

**ReviewChanges.jsx - Enhanced with human confirmation:**
```jsx
function ReviewChanges({ sessionId, changes, reviewId }) {
  const [commitMessage, setCommitMessage] = useState('');
  const [branchName, setBranchName] = useState(`ai-agent-changes-${Date.now()}`);
  
  const handleApprove = async () => {
    await fetch(`/agent/review/${reviewId}`, {
      method: 'POST',
      body: JSON.stringify({ 
        action: 'approve',
        session_id: sessionId,
        commit_message: commitMessage,
        branch_name: branchName
      })
    });
  };
  
  const handleReject = async () => {
    await fetch(`/agent/review/${reviewId}`, {
      method: 'POST',
      body: JSON.stringify({ 
        action: 'reject',
        session_id: sessionId
      })
    });
  };
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Review AI Agent Changes</h1>
      
      {/* Diff Viewer with Cursor-style highlighting */}
      <DiffViewer changes={changes} />
      
      {/* Review Controls */}
      <div className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Commit Message
          </label>
          <input 
            value={commitMessage}
            onChange={(e) => setCommitMessage(e.target.value)}
            className="w-full p-3 border rounded-lg"
            placeholder="Describe the changes made by the AI agent..."
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Branch Name
          </label>
          <input 
            value={branchName}
            onChange={(e) => setBranchName(e.target.value)}
            className="w-full p-3 border rounded-lg"
            placeholder="ai-agent-changes-2025-10-25"
          />
        </div>
        
        <div className="flex space-x-4">
          <button 
            onClick={handleApprove}
            className="bg-green-600 text-white px-6 py-3 rounded-lg font-medium"
          >
            ✅ Approve & Commit Changes
          </button>
          <button 
            onClick={handleReject}
            className="bg-red-600 text-white px-6 py-3 rounded-lg font-medium"
          >
            ❌ Reject Changes
          </button>
        </div>
      </div>
    </div>
  );
}
```

## GitHub Integration Details

### OAuth Setup

1. Create GitHub OAuth App in GitHub Developer Settings
2. Set callback URL: `http://localhost:8000/auth/callback` (dev) / production URL
3. Store Client ID and Client Secret in backend `.env`

### GitHub API Operations (using PyGithub library)

- List repositories: `GET /user/repos`
- Clone: Use `GitPython` library
- Create branch: GitHub API
- Push changes: `GitPython`

## Security Considerations

- Store GitHub tokens encrypted (use `cryptography` library)
- Validate all file paths to prevent directory traversal
- Sandbox agent operations to cloned directory only
- Rate limiting on API endpoints
- CORS configuration for frontend-backend communication
- Cleanup temp directories to prevent disk space issues
- Token expiration handling with refresh mechanism

## Database Layer (PostgreSQL + SQLAlchemy)

### Database Schema

**Users Table**:

```python
- id (UUID, primary key)
- github_id (Integer, unique)
- username (String)
- avatar_url (String)
- access_token (String, encrypted)
- created_at (DateTime)
```

**Sessions Table**:

```python
- id (UUID, primary key)
- user_id (UUID, foreign key)
- repo_url (String)
- repo_name (String)
- clone_path (String)
- status (Enum: cloning, ready, executing, completed, error)
- created_at (DateTime)
- expires_at (DateTime)
```

**Agent Executions Table**:

```python
- id (UUID, primary key)
- session_id (UUID, foreign key)
- prompt (Text)
- function_calls (JSON)
- result (Text)
- status (Enum: pending, running, completed, failed)
- duration_seconds (Float)
- created_at (DateTime)
```

**Commits Table**:

```python
- id (UUID, primary key)
- session_id (UUID, foreign key)
- commit_message (Text)
- branch_name (String)
- commit_hash (String)
- files_changed (Integer)
- github_url (String)
- created_at (DateTime)
```

**NEW: Reviews Table**:

```python
- id (UUID, primary key)
- session_id (UUID, foreign key)
- user_id (UUID, foreign key)
- prompt (Text)
- changes (JSON)
- status (Enum: pending_review, approved, rejected)
- created_at (DateTime)
- approved_at (DateTime, nullable)
- rejected_at (DateTime, nullable)
```

### Setup Instructions

1. Install PostgreSQL locally or use Docker
2. Create database: `createdb aicodingagent_dev`
3. Use Alembic for migrations
4. Database URL in `.env`: `DATABASE_URL=postgresql://user:pass@localhost/aicodingagent_dev`

## Docker + Docker Compose Setup

### Services

```yaml
services:
  postgres:
 - PostgreSQL database
 - Volume for data persistence
  
  backend:
 - FastAPI application
 - Depends on postgres
 - Hot reload for development
  
  frontend:
 - Vite dev server
 - Proxies API calls to backend
```

### Development Workflow

```bash
docker-compose up -d          # Start all services
docker-compose logs -f backend # Watch backend logs
docker-compose exec backend pytest # Run tests
docker-compose down           # Stop all services
```

## Testing Strategy

### Backend Tests (pytest)

**Unit Tests**:

- Test each tool function (get_files_info, write_file, etc.)
- Test database models and queries
- Test utility functions

**Integration Tests**:

- Test API endpoints with test database
- Mock GitHub API calls
- Test OAuth flow (with mocked GitHub)
- Test agent execution flow
- **NEW**: Test review workflow

**Test Structure**:

```
backend/tests/
├── conftest.py           # Pytest fixtures
├── test_tools.py         # Tool function tests
├── test_auth.py          # OAuth flow tests
├── test_repos.py         # Repository operations
├── test_agent.py         # Agent execution tests
├── test_review.py        # Review workflow tests
└── test_database.py      # Database operations
```

### Frontend Tests (Vitest)

**Component Tests**:

- Test UI components in isolation
- Mock API calls
- Test user interactions
- **NEW**: Test review components

**Test Structure**:

```
frontend/src/
├── components/
│   └── __tests__/
│       ├── LoginButton.test.jsx
│       ├── RepoList.test.jsx
│       ├── PromptInput.test.jsx
│       └── ReviewControls.test.jsx
```

## CI/CD Pipeline (GitHub Actions)

### Workflows

**`.github/workflows/test.yml`**:

```yaml
on: [push, pull_request]

jobs:
  backend-tests:
 - Setup Python
 - Install dependencies
 - Run pytest
 - Upload coverage
  
  frontend-tests:
 - Setup Node.js
 - Install dependencies
 - Run Vitest
 - Run linting
  
  docker-build:
 - Build Docker images
 - Ensure builds succeed
```

**`.github/workflows/deploy.yml`** (optional):

- Deploy to staging on merge to main
- Deploy to production on release tag

## Dependencies

**Backend** (`requirements.txt`):

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
google-genai==1.12.1
PyGithub==2.1.1
GitPython==3.1.40
python-multipart==0.0.6
pydantic==2.5.0
cryptography==41.0.7
python-jose[cryptography]==3.3.0
websockets==12.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.26.0
```

**Frontend** (`package.json`):

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "eslint": "^8.55.0"
  }
}
```

## Development Setup

### Initial Setup (One-time)

1. **Clone and setup environment**:
```bash
cd aicodingagent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

2. **Create GitHub OAuth App**:

            - Go to GitHub Settings → Developer settings → OAuth Apps
            - New OAuth App
            - Homepage URL: `http://localhost:5173`
            - Callback URL: `http://localhost:8000/auth/callback`
            - Save Client ID and Client Secret

3. **Configure environment**:
```bash
# Backend .env
cp backend/.env.example backend/.env
# Add: GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, DATABASE_URL, SECRET_KEY

# Frontend .env
cp frontend/.env.example frontend/.env
# Add: VITE_API_URL=http://localhost:8000
```

4. **Start with Docker Compose**:
```bash
docker-compose up -d
# Access frontend: http://localhost:5173
# Access backend: http://localhost:8000
# Access API docs: http://localhost:8000/docs
```


### Daily Development

```bash
# Option 1: Use Docker Compose
docker-compose up

# Option 2: Run locally
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Terminal 3 - Database
docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
```

## Learning Resources & Tips

### FastAPI Basics

- FastAPI auto-generates API docs at `/docs`
- Use Pydantic models for request/response validation
- Async/await for database and external API calls
- Dependency injection for shared logic (auth, database sessions)

### GitHub OAuth Flow

1. User clicks "Login with GitHub"
2. Redirect to `https://github.com/login/oauth/authorize?client_id=...`
3. User authorizes, GitHub redirects to your callback
4. Exchange code for access token
5. Use token to call GitHub API

### Database with SQLAlchemy

- Define models as Python classes
- Use Alembic for schema migrations
- Session management via FastAPI dependencies
- Async queries for better performance

### Testing Best Practices

- Write tests as you build (not after!)
- Test one thing per test
- Use fixtures for common setup
- Mock external APIs (GitHub, Gemini)

## Project Phases (Recommended Order)

**Phase 1: Foundation (Week 1)**

1. Fix tool bugs
2. Setup project structure (backend + frontend)
3. Docker Compose configuration
4. Database setup with basic models

**Phase 2: Backend Core (Week 2)**

5. Enhanced tools implementation
6. FastAPI basic endpoints (health check, docs)
7. Database CRUD operations
8. Basic tests

**Phase 3: Authentication (Week 3)**

9. GitHub OAuth implementation
10. Token management
11. User authentication tests

**Phase 4: Repository Operations (Week 3-4)**

12. Clone repository logic
13. Session management
14. File browsing endpoints

**Phase 5: Agent Integration (Week 4-5)**

15. Refactor agent service
16. WebSocket streaming
17. Agent execution endpoints

**Phase 6: Human-in-the-Loop System (Week 5-6)**

18. **NEW**: Review workflow implementation
19. **NEW**: Review database models
20. **NEW**: Review API endpoints
21. **NEW**: Review frontend components

**Phase 7: Frontend (Week 6-7)**

22. React app structure
23. Authentication UI
24. Repository selection UI
25. Agent workspace UI with review controls
26. Review & commit UI with diff viewer

**Phase 8: Testing & Polish (Week 7-8)**

27. Comprehensive test coverage
28. CI/CD pipeline
29. Error handling
30. Documentation (README)

**Phase 9: Deployment (Week 8)**

31. Deploy to cloud platform
32. Production environment setup
33. Final testing

## Deployment Considerations

- **Backend**: Railway.app (free tier, supports PostgreSQL)
- **Frontend**: Vercel (free tier, perfect for React)
- **Database**: Railway PostgreSQL (included)
- Update GitHub OAuth callback to production URL
- Environment variables in deployment platforms
- CORS configuration for production frontend URL

### To-dos

- [ ] Create FastAPI backend structure with routers, services, and models
- [ ] Implement GitHub OAuth flow (redirect, callback, token storage)
- [ ] Refactor existing Gemini agent into reusable AgentService class
- [ ] Create repository clone, status, and cleanup endpoints
- [ ] Create agent execution endpoints with WebSocket streaming
- [ ] **NEW**: Implement human-in-the-loop review system
- [ ] **NEW**: Create review database models and endpoints
- [ ] **NEW**: Add review workflow to agent execution
- [ ] Create commit and push endpoints with branch creation
- [ ] Create Vite + React frontend with routing and component structure
- [ ] Build authentication UI with GitHub login and user profile
- [ ] Build repository list and clone UI
- [ ] Build agent workspace with prompt input, output display, and WebSocket streaming
- [ ] **NEW**: Build review controls and diff viewer
- [ ] Build review changes and commit UI with diff viewer
- [ ] Implement token encryption, path validation, and rate limiting
- [ ] Test complete flow: OAuth → Clone → Agent → Review → Commit
