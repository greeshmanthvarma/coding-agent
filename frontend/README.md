# RepoRefine Frontend

Frontend application for RepoRefine - AI-Powered Code Refinement Platform.

## Tech Stack

- **Vite** - Fast build tool and dev server
- **React 19** - UI library
- **Tailwind CSS** - Utility-first CSS framework

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5174`

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Tailwind CSS imports
├── public/              # Static assets
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
├── tailwind.config.js  # Tailwind CSS configuration
└── postcss.config.js   # PostCSS configuration
```

## API Proxy

The Vite dev server is configured to proxy API requests:
- Frontend: `http://localhost:5174`
- Backend: `http://localhost:8000`
- Proxy: `/api/*` → `http://localhost:8000/*`

Example: `fetch('/api/auth/github')` → `http://localhost:8000/auth/github`

## Build

```bash
npm run build
```

## Preview Production Build

```bash
npm run preview
```
