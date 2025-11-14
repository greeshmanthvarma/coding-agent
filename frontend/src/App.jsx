import { Button } from "./components/ui/button"
import githubIcon from "./assets/brand-github.svg"
import { InputGroup, InputGroupTextarea, InputGroupAddon, InputGroupButton, InputGroupText } from "./components/ui/input-group"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "./components/ui/dropdown-menu"
import { PlusIcon, LogOutIcon, Loader2 } from "lucide-react"
import { ArrowUpIcon } from "lucide-react"
import { useState, useEffect, useRef } from "react"
import { SidebarComponent } from "./components/sidebarComponent"
import { SidebarProvider, SidebarInset } from "./components/ui/sidebar"


export default function App() {

  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [error, setError] = useState(null)
  const [token, setToken] = useState(null)
  const [repositories, setRepositories] = useState([])
  const [showRepositories, setShowRepositories] = useState(false)
  const [selectedRepository, setSelectedRepository] = useState(null)
  const [isCloning, setIsCloning] = useState(false)
  const [clonedSessionId, setClonedSessionId] = useState(null)
  const [message, setMessage] = useState('')
  const [websocket, setWebsocket] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [agentResponse, setAgentResponse] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const urlParams = new URLSearchParams(window.location.search)
        const success = urlParams.get('success')
        
        if (success === 'true') {
          // Clean up URL i.e., remove ?success=true from address bar)
          window.history.replaceState({}, document.title, window.location.pathname)
          
          // Verify authentication by calling /api/auth/me
          const response = await fetch('/api/auth/me', {
            credentials: 'include' 
          })
          
          if (response.ok) {
            const userData = await response.json()
            setIsAuthenticated(true)
            setUser(userData)
            setError(null)
          } else {
            throw new Error('Authentication failed')
          }
        } else {
          // Check if already authenticated on initial load
          const response = await fetch('/api/auth/me', {
            credentials: 'include'
          })
          
          if (response.ok) {
            const userData = await response.json()
            setIsAuthenticated(true)
            setUser(userData)
            setError(null)
          } else {
            // Not authenticated, user needs to log in
            setIsAuthenticated(false)
            setUser(null)
          }
        }
      } catch (error) {
        setError(error.message)
        setIsAuthenticated(false)
        setUser(null)
      }
    }
    const getRepositories = async () => {
      try {
        const response = await fetch('/api/user/repos', {
          credentials: 'include'
        })
        
        if (response.ok) {
          const data = await response.json()
          setRepositories(data.repos || [])
        } else {
          setRepositories([])
        }
      } catch (error) {
        setRepositories([])
      }
    }
    
    checkAuth()
    getRepositories()
  }, [])

  function onLogin() {
    window.location.href = "/api/auth/github"
  }

  function onAddRepository() {
    setShowRepositories(!showRepositories)
  }

  function onSelectRepository(repository) {
    
    setSelectedRepository(repository)
    setError(null)
  }

  async function onCloneRepository() {
    if (!selectedRepository) return
    
    setIsCloning(true)
    setError(null)
    
    try {
      const response = await fetch('/api/user/repos/clone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: selectedRepository.id,
          name: selectedRepository.name,
          full_name: selectedRepository.full_name,
          private: selectedRepository.private
        }),
        credentials: 'include'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to clone repository')
      }
      
      const data = await response.json()
      setClonedSessionId(data.session_id)
      setShowRepositories(false)
      
    } catch (error) {
      setError(error.message)
    } finally {
      setIsCloning(false)
    }
  }
  

  return (
    <SidebarProvider>
      <SidebarComponent />
      <SidebarInset>
        <div className="dark min-h-screen bg-background text-foreground">
          <div className="container flex flex-col mx-auto px-4 py-6 h-screen">
            <div className="flex justify-end items-center">
          {
            isAuthenticated ? 
            <Button className="rounded-full">
            <img src={user.avatar_url} alt="User" className="w-4 h-4" />{user.username}
            </Button>
            : 
            <Button className="rounded-full" onClick={()=>onLogin()}>
            <img src={githubIcon} alt="GitHub" className="w-4 h-4" />Login with GitHub
            </Button>
          }
        </div>
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
            {error}
          </div>
        )}

        {selectedRepository && !clonedSessionId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="relative z-50 w-full max-w-md mx-4 p-6 bg-card border border-border rounded-lg shadow-lg">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold mb-2">{selectedRepository.name}</h2>
                  <p className="text-muted-foreground text-sm">{selectedRepository.full_name}</p>
                  <p className="text-muted-foreground text-xs mt-1">
                    {selectedRepository.private ? '🔒 Private' : '🌐 Public'} Repository
                  </p>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon-xs"
                  onClick={() => {
                    setSelectedRepository(null)
                    setError(null)
                  }}
                >
                  ✕
                </Button>
              </div>
              <div className="flex gap-3 mt-4">
                <Button 
                  onClick={onCloneRepository}
                  disabled={isCloning}
                  className="flex-1"
                >
                  {isCloning ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Cloning...
                    </>
                  ) : (
                    'Clone Repository'
                  )}
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => {
                    setSelectedRepository(null)
                    setError(null)
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {selectedRepository && clonedSessionId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="relative z-50 w-full max-w-md mx-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-green-400 font-medium">✓ Repository cloned successfully!</p>
                  <p className="text-green-400/70 text-sm mt-1">
                    {selectedRepository.name} is ready to use. Session ID: {clonedSessionId}
                  </p>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon-xs"
                  onClick={() => {
                    setSelectedRepository(null)
                    setClonedSessionId(null)
                    setError(null)
                  }}
                >
                  ✕
                </Button>
              </div>
            </div>
          </div>
        )}
       
        <div className="flex mt-auto mb-8 w-full max-w-2xl mx-auto pl-8">
        <InputGroup>
        <InputGroupTextarea 
          placeholder="Ask, Search or Chat..." 
          className="overflow-y-auto max-h-24"
        />
        <InputGroupAddon align="block-end" className="flex justify-between items-center gap-2">
          {
          selectedRepository && clonedSessionId ? 
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{selectedRepository.name}</span>
            <Button variant="outline" className="rounded-full" size="icon-xs" onClick={()=>{
              setSelectedRepository(null)
              setClonedSessionId(null)
            }}>
              ✕
            </Button>
          </div> : 
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <InputGroupButton
                  variant="outline"
                  className="rounded-full"
                  size="icon-lg"
                  disabled={!isAuthenticated}
                >
                  <PlusIcon /> 
                  <span>Add Repository</span>
                </InputGroupButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {
                  repositories.map((repository) => (
                    <DropdownMenuItem key={repository.id} onClick={()=>onSelectRepository(repository)}>
                      {repository.name}
                    </DropdownMenuItem>
                  ))
                }
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
         }
          <InputGroupButton
            variant="default"
            className="rounded-full"
            size="icon-xs"
            disabled={!isAuthenticated}
            onClick={()=>onSendMessage()}
          >
            <ArrowUpIcon />
            <span className="sr-only">Send</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
        </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}

