import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1",
});

export const summarizeVideo = async (url) => {
  const response = await api.post("/summarize", { url });
  return response.data;
};

export const sendChatMessage = async (videoId, question, history) => {
  const response = await api.post("/chat", {
    video_id: videoId,
    question: question,
    history: history,
  });
  return response.data;
};
