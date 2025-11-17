import { useMemo } from "react"
import useWebSocket from "react-use-websocket"

export function useWebsocket(sessionId, token) {
    // Memoize the URL to prevent unnecessary reconnections
    const socketUrl = useMemo(() => {
        if(!sessionId) {
            return null
        }
        // Connect directly to backend (bypass Vite proxy for WebSocket)
        // WebSocket connections work better when connecting directly
        const wsProtocol = 'ws:'
        const wsHost = 'localhost:8000' // Direct backend connection
        
        // Token can be in query param (for explicit auth) or cookie (sent automatically)
        if (token) {
            return `${wsProtocol}//${wsHost}/agent/stream/${sessionId}?token=${token}`
        }
        // If no token provided, rely on cookie (browser sends it automatically)
        return `${wsProtocol}//${wsHost}/agent/stream/${sessionId}`
    }, [sessionId, token]) // Only recalculate when sessionId or token changes
    
    const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl, {
        onOpen: (event) => {
            console.log('WebSocket connection opened:', event)
        },
        onError: (event) => {
            console.error('WebSocket error:', event)
        },
        shouldReconnect: () => true,
        reconnectInterval: 3000,
        reconnectAttempts: 5,
    })

    return {
        sendMessage,
        lastMessage,
        readyState,
        isConnected: readyState === 1,
    }
}