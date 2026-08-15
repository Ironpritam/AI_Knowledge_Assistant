import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
    timeout: 120000,
});

export const documentApi = {
    list: () => api.get("/documents"),
    get: (documentId) => api.get(`/documents/${documentId}`),
    upload: (file, collectionName) => {
        const formData = new FormData();
        formData.append("file", file);

        return api.post("/documents/upload", formData, {
            params: { collection_name: collectionName },
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });
    },
    remove: (documentId) => api.delete(`/documents/${documentId}`),
};

export const ragApi = {
    ask: (payload) => api.post("/rag/ask", payload),
};

export const modelApi = {
    list: () => api.get("/llm/models"),
};

export const healthApi = {
    check: () => api.get("/health/"),
};

// export const ragApi = {
//   ask: (payload) =>
//     api.post("/rag/ask", payload),
// };

export default api;

