// composables/useWebSocket.js
import { ref } from "vue"
export function useWebSocket(server, seller_id) {
  const messagekey = ref('')
  const messagevalue = ref('')
  const progress = ref(0)
  let websocket
  function connectWebSocket() {
    if (process.client) {
      websocket = new WebSocket(`ws://${server}/ws/${seller_id}`)
      websocket.onopen = () => {
        console.log('Connected to WebSocket')
      }
      websocket.onmessage = function(event) {
        console.log('Received message:', event.data)
        const message = event.data
        if (message.startsWith("Progress")) {
          messagekey.value = message.split(":")[0]
          messagevalue.value = message.split(":")[1]
          progress.value = parseInt(messagevalue.value)
          localStorage.setItem(`${messagekey.value}`, progress.value)
          if (progress.value === 100) {
            localStorage.removeItem(`${messagekey.value}`)
            console.log('Progress completed, localStorage item removed.')
          }
        }
      }
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      websocket.onclose = () => {
        console.log('WebSocket connection closed. Reconnecting...')
        setTimeout(connectWebSocket, 1000)
      }
    }
  }
  function closeWebSocket() {
    if (websocket) {
      websocket.close()
      console.log('WebSocket connection closed manually.')
    }
  }
  return {
    connectWebSocket,
    closeWebSocket,
    progress,
  }
}