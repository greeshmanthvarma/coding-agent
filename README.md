# RepoRefine

**AI-Powered Code Refinement Platform**  
Real-time AI-assisted code editing, review, and GitHub integration.

---

## Highlights

- Real-time AI code refinement with Google Gemini 2.0 Flash API
- Secure GitHub OAuth authentication and JWT-based session management
- Clone, modify, and review repositories in isolated, session-based environments
- WebSocket streaming for interactive agent communication
- Git-based checkpoint system to approve/reject/revert changes
- Redis cache + PostgreSQL fallback for fast, reliable message persistence

---

## Overview

RepoRefine enables developers to safely interact with GitHub repositories using an AI agent. Users can:

- Clone repositories into isolated sessions
- Chat with the AI agent to request code changes
- Review and approve/reject changes before committing to GitHub

The platform ensures **full control, security, and auditability** while leveraging AI for iterative code improvement.

---

## Key Features

### Authentication & Authorization
- GitHub OAuth login
- JWT-based session management
- User-specific repo access and secure token handling

### Repository Management
- Clone public/private repos
- Session isolation with automatic cleanup
- Support for multiple concurrent sessions

### AI Agent Capabilities
- File operations: list, read, write, search
- Code analysis: extract functions/classes, overview files
- Code execution: Python/Node.js files, shell commands
- Multi-iteration processing (up to 20 iterations)
- Maintains context across agent conversations

### Review System
- Git-based change tracking
- Automatic checkpoint creation
- Approve, reject, or push changes to GitHub

### Real-time Communication
- WebSocket bidirectional streaming
- Automatic reconnection and state handling

---

## Tech Stack

**Backend:** FastAPI, Python 3.x, PostgreSQL (SQLAlchemy), Redis, Gemini 2.0 Flash API, JWT  
**Frontend:** React 19, Vite, Tailwind CSS, Radix UI, react-use-websocket  
**Infrastructure:** Uvicorn, Git

---

## Architecture Overview

```
User → Frontend (React) → WebSocket / REST → Backend (FastAPI) → Gemini Agent
                                                      ↓
                                            PostgreSQL + Redis
                                                      ↓
                                                   GitHub API
```

- AI agent executes function calls securely in isolated sessions
- Backend orchestrates cloning, modifications, reviews, and real-time streaming
- Redis provides fast message caching with PostgreSQL as persistent storage

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── routers/             # auth, agent, user endpoints
│   ├── services/            # agent orchestration, git operations
│   └── utils/               # file cleanup, git utilities
├── functions/               # Agent function definitions (7 functions)
└── requirements.txt          # Python dependencies

frontend/
├── src/
│   ├── components/          # UI, review, sidebar components
│   ├── hooks/              # WebSocket, mobile hooks
│   └── App.jsx             # Main application
└── package.json
```

---

## Setup

### Prerequisites
- Python 3.9+, Node.js 18+, PostgreSQL 12+, Redis 6+
- GitHub OAuth credentials

### Environment Variables

Create `.env` in `backend/`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/reforefine
REDIS_HOST=localhost
REDIS_PORT=6379
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
JWT_SECRET=your_jwt_secret_key
GEMINI_API_KEY=your_gemini_api_key
```

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
createdb reforefine
redis-server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Application available at `http://localhost:5174`

### GitHub OAuth Setup

1. GitHub Settings > Developer settings > OAuth Apps
2. Create new OAuth App
3. Set callback URL: `http://localhost:8000/auth/callback`
4. Add credentials to `.env`

---

## Skills Demonstrated

- **Full-Stack Development**: FastAPI, React, Tailwind CSS
- **AI Integration**: LLM orchestration, function calling, context-aware interactions
- **Infrastructure**: WebSockets, Redis, PostgreSQL
- **Security & Auth**: OAuth 2.0, JWT, session isolation
- **Version Control**: Git automation, checkpoint system
