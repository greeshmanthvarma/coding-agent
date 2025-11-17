import { Button } from "./components/ui/button"
import githubIcon from "./assets/brand-github.svg"
import { InputGroup, InputGroupTextarea, InputGroupAddon, InputGroupButton } from "./components/ui/input-group"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "./components/ui/dropdown-menu"
import { PlusIcon, Loader2 } from "lucide-react"
import { ArrowUpIcon } from "lucide-react"
import { useState, useEffect } from "react"
import { SidebarComponent } from "./components/sidebarComponent"
import { SidebarProvider, SidebarInset } from "./components/ui/sidebar"
import { useWebsocket } from "./hooks/useWebsocket"

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
  const [agentResponse, setAgentResponse] = useState('')
  const [agentResponses, setAgentResponses] = useState([])
  const [chatHistory, setChatHistory] = useState([])

  const { sendMessage, lastMessage, isConnected, readyState } = useWebsocket(clonedSessionId, token)

  // Debug: Log button state
  useEffect(() => {
    console.log('Send button state:', {
      isAuthenticated,
      isConnected,
      hasMessage: !!message.trim(),
      readyState,
      clonedSessionId,
      disabled: !isAuthenticated || !isConnected || !message.trim()
    })
  }, [isAuthenticated, isConnected, message, readyState, clonedSessionId])

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
            
            if (userData.token) {
              setToken(userData.token)
            }
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
            
            if (userData.token) {
              setToken(userData.token)
            }
          } else {
            // Not authenticated, user needs to log in
            setIsAuthenticated(false)
            setUser(null)
            setToken(null)
          }
        }
      } catch (error) {
        setError(error.message)
        setIsAuthenticated(false)
        setUser(null)
        setToken(null)
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

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data)
        console.log('Received WebSocket message:', data)
        
        if (data.type === 'connected') {
          // Connection confirmed - do nothing, just log
          console.log('WebSocket connected:', data.message)
        } else if (data.type === 'agent_started') {
          // Agent started processing - show loading state
          setAgentResponse('Processing...')
          setAgentResponses([])
        } else if (data.status === 'completed') {
          // Agent finished successfully
          let fullResponse = ''
          if (data.agent_responses && data.agent_responses.length > 0) {
            // Use agent_responses array - join them for display
            fullResponse = data.agent_responses.join('\n\n')
            setAgentResponses(data.agent_responses)
            setAgentResponse(fullResponse)
          } else if (data.message) {
            // Fallback to message if no agent_responses
            fullResponse = data.message
            setAgentResponses([])
            setAgentResponse(data.message)
          } else {
            // No response content
            setAgentResponses([])
            setAgentResponse('')
          }
          // Add agent response to chat history
          if (fullResponse) {
            setChatHistory(prev => [...prev, { role: 'assistant', content: fullResponse }])
          }
        } else if (data.status === 'error') {
          // Agent error
          setError(data.message || 'An error occurred')
          if (data.agent_responses && data.agent_responses.length > 0) {
            setAgentResponses(data.agent_responses)
            setAgentResponse(data.agent_responses.join('\n\n'))
          }
        } else if (data.status === 'max_iterations_reached') {
          // Max iterations reached
          setError('Agent reached maximum iterations')
          if (data.agent_responses && data.agent_responses.length > 0) {
            setAgentResponses(data.agent_responses)
            setAgentResponse(data.agent_responses.join('\n\n'))
          }
        } else if (data.agent_responses && data.agent_responses.length > 0) {
          // Update with latest responses
          setAgentResponses(data.agent_responses)
          setAgentResponse(data.agent_responses.join('\n\n'))
        } else if (data.message) {
          // Generic message
          setAgentResponse(data.message)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
  }, [lastMessage])
  
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
  
  function onSendMessage() {
    console.log('onSendMessage called:', { 
      message: message.trim(), 
      isConnected, 
      clonedSessionId,
      readyState 
    })
    
    if (!message.trim()) {
      setError('Please enter a message')
      return
    }
    
    if (!isConnected) {
      setError('Not connected to agent. Please wait...')
      return
    }
    
    if (!clonedSessionId) {
      setError('No repository selected')
      return
    }

    try {
      const userMessage = message.trim()
      
      // Add user message to chat history
      setChatHistory(prev => [...prev, { role: 'user', content: userMessage }])
      
      // Clear previous response when sending a new message
      setAgentResponse('')
      setAgentResponses([])
      
      // Send message via WebSocket
      const messageToSend = JSON.stringify({ prompt: userMessage })
      console.log('Sending message:', messageToSend)
      sendMessage(messageToSend)
      setMessage('')
      setError(null)
    } catch (error) {
      console.error('Error sending message:', error)
      setError(`Failed to send message: ${error.message}`)
    }
  }

  return (
    <SidebarProvider>
      <SidebarComponent />
      <SidebarInset>
        <div className="dark min-h-screen bg-background text-foreground">
          <div className="container flex flex-col mx-auto px-4 py-6 h-screen">
            {/* User Login/Logout */}
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
        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
            {error}
          </div>
        )}
        {/* Clone Repository Dialog */}
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
        {/* Repository Cloned Successfully */}
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
                    // Just hide the modal, don't reset the session
                    setSelectedRepository(null)
                    setError(null)
                  }}
                >
                  ✕
                </Button>
              </div>
            </div>
          </div>
        )}
        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto mb-4 px-8">
          {agentResponse && (
            <div className="flex flex-col gap-4">
              <div className="bg-muted/50 rounded-lg p-4">
                <div className="text-sm font-medium mb-2">Agent Response:</div>
                <div className="text-sm whitespace-pre-wrap">
                  {agentResponse}
                </div>
              </div>
            </div>
          )}
        </div>
       {/* Chat Input Area */}
        <div className="flex mt-auto mb-8 w-full max-w-2xl mx-auto pl-8">
        <InputGroup>
        <InputGroupTextarea 
          placeholder="Ask, Search or Chat..." 
          className="overflow-y-auto max-h-24"
          value={message}
          onChange={(e)=>setMessage(e.target.value)}
          onKeyDown={(e)=>{
            if(e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              onSendMessage()
            }
          }}
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
            disabled={!isAuthenticated || !isConnected || !message.trim()}
            onClick={()=>onSendMessage()}
            title={`Send (Auth: ${isAuthenticated}, Connected: ${isConnected}, HasMessage: ${!!message.trim()}, ReadyState: ${readyState})`}
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

