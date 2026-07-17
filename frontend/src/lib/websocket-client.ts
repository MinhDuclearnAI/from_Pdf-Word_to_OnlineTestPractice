const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";

export const connectToJobWS = (
  jobId: string | number,
  onMessage: (data: { status: string; progress: number; message: string; result?: any }) => void,
  onError?: (error: Event) => void,
  onClose?: () => void
) => {
  const socket = new WebSocket(`${WS_URL}/jobs/${jobId}`);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error("Failed to parse WS data:", event.data);
    }
  };

  if (onError) {
    socket.onerror = (error) => {
      onError(error);
    };
  }

  socket.onclose = () => {
    if (onClose) onClose();
  };

  return () => {
    socket.close();
  };
};
