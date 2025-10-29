import { ref } from 'vue';

export function useWebSocket(url, onMessage) {
  const ws = ref(null);
  const connected = ref(false);

  function connect() {
    ws.value = new WebSocket(url);
    ws.value.binaryType = "arraybuffer";
    ws.value.onopen = () => { connected.value = true; };
    ws.value.onmessage = (event) => {
      onMessage(event.data);
    };
    ws.value.onclose = () => { connected.value = false; };
  }

  function send(data) {
    if (connected.value) ws.value.send(data);
  }

  function disconnect() {
    ws.value?.close();
  }

  return { connect, send, disconnect, connected };
}