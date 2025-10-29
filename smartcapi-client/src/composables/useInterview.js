import { useInterviewStore } from '../store/interview';
import { useRecorder } from './useRecorder';
import { useWebSocket } from './useWebSocket';

export function useInterview() {
  const store = useInterviewStore();
  const wsUrl = "ws://localhost:8000/ws/interview"; // Ganti sesuai alamat backend
  const { connect, send, disconnect, connected } = useWebSocket(wsUrl, onWsMessage);
  const { isRecording, startRecording, stopRecording } = useRecorder(sendAudioChunk);

  function sendAudioChunk(blob) {
    blob.arrayBuffer().then(buffer => send(buffer));
  }

  function onWsMessage(data) {
    let msg = JSON.parse(data);
    if (msg.type === "transcript") {
      store.addTranscript(msg);
    } else if (msg.type === "questionnaire") {
      // Backend mengirim hasil ekstraksi kuesioner
      store.setQuestionnaire(msg.data);
    }
  }

  function startInterview() {
    connect();
    startRecording();
  }

  function stopInterview() {
    stopRecording();
    disconnect();
  }

  return { isRecording, connected, startInterview, stopInterview };
}