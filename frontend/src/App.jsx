import { Button } from "./components/ui/button"
import githubIcon from "./assets/brand-github.svg"
import { InputGroup, InputGroupTextarea, InputGroupAddon, InputGroupButton, InputGroupText } from "./components/ui/input-group"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "./components/ui/dropdown-menu"
import { PlusIcon, LogOutIcon } from "lucide-react"
import { ArrowUpIcon } from "lucide-react"
import { useState, useEffect } from "react"
import { AppSidebar } from "./components/app-sidebar"
export default function App() {

  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)
  const [error, setError] = useState(null)
  const [token, setToken] = useState(null)
  const [repositories, setRepositories] = useState([])
  const [showRepositories, setShowRepositories] = useState(false)
  const [selectedRepository, setSelectedRepository] = useState(null)
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

  async function onSelectRepository(repository) {
    try {
      const response = await fetch('/api/user/repos/clone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: repository.id,
          name: repository.name,
          full_name: repository.full_name,
          private: repository.private
        }),
        credentials: 'include'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to clone repository')
      }
      
      const data = await response.json()
      console.log(data)
      setShowRepositories(false) 
      setSelectedRepository(repository)
    } catch (error) {
      setError(error.message)
    }
  }

  return (
    <div className="dark min-h-screen bg-background text-foreground">
      <div className="container flex flex-col mx-auto px-4 py-8">
        
        <div className="flex justify-between items-center">
          <h1 className="text-4xl text-foreground mb-4">
            <span className="italic tracking-tightest">Repo</span><span className="font-bold tracking-tightest">Refine</span>  
          </h1>
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
       
        <div className="flex justify-end mt-8 flex-1">
        <InputGroup>
        <InputGroupTextarea placeholder="Ask, Search or Chat..." />
        <InputGroupAddon align="block-end" className="flex justify-between items-center gap-2">
          {
          selectedRepository ? 
          <div className="flex items-center gap-2">
            <span>{selectedRepository.name}</span>
            <Button variant="outline" className="rounded-full" size="icon-lg" onClick={()=>setSelectedRepository(null)}>
              Close
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
          >
            <ArrowUpIcon />
            <span className="sr-only">Send</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
        </div>
      </div>
    </div>
  )
}

