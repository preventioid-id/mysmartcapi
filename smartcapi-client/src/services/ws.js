let ws
export function listenAIResult(cb) {
  ws = new WebSocket('ws://localhost:8000/ws/ai-result')
  ws.onmessage = evt => {
    const data = JSON.parse(evt.data)
    cb(data)
  }
}