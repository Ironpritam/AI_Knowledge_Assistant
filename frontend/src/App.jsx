import { useCallback, useEffect, useState } from "react";

import "./App.css";
import {
  documentApi,
  healthApi,
  modelApi,
} from "./services/api";

import HealthIndicator from "./components/common/HealthIndicator";
import DocumentList from "./components/documents/DocumentList";
import DocumentUploader from "./components/documents/DocumentUploader";
import ChatPanel from "./components/chat/ChatPanel";


const COLLECTION_NAME =
  import.meta.env.VITE_RAG_COLLECTION_NAME || "test_ingestion_bge";

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const selectedDocuments = documents.filter((document) =>
    selectedDocumentIds.includes(document.id)
  );

  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");

  const [systemHealth, setSystemHealth] = useState({
    status: "offline",
    components: {},
  });
  
  const [uploading, setUploading] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(true);

  const [error, setError] = useState("");

  const loadDocuments = useCallback(async () => {
    try {
      setLoadingDocuments(true);
      const response = await documentApi.list();
      setDocuments(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load documents."
      );
    } finally {
      setLoadingDocuments(false);
    }
  }, []);

  const loadModels = useCallback(async () => {
    try {
      const response = await modelApi.list();

      const availableModels = response.data.models.filter(
        (model) => model.enabled
      );

      setModels(availableModels);

      const defaultModel =
        response.data.default_model_id ||
        availableModels.find((model) => model.default)?.id ||
        availableModels[0]?.id ||
        "";

      setSelectedModel(defaultModel);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load available models."
      );
    }
  }, []);

const checkHealth = useCallback(async () => {
  try {
    const response = await healthApi.check();

    setSystemHealth({
      status: response.data.status,
      components: response.data.components || {},
    });

  } catch (err) {
    // Backend responded with a health status such as "unhealthy"
    // but used HTTP 503.
    if (err.response?.data?.status) {
      setSystemHealth({
        status: err.response.data.status,
        components: err.response.data.components || {},
      });
      return;
    }

    // No HTTP response means the backend is unreachable.
    setSystemHealth({
      status: "offline",
      components: {},
    });
  }
}, []);

useEffect(() => {
  const initializeApp = async () => {
    await Promise.allSettled([
      loadDocuments(),
      loadModels(),
      checkHealth(),
    ]);
  };

  initializeApp();
}, [loadDocuments, loadModels, checkHealth]);


  const handleDocumentSelect = (document) => {
    setSelectedDocumentIds((current) => {
      if (current.includes(document.id)) {
        return current.filter((id) => id !== document.id);
      }

      return [...current, document.id];
    });
  };

  const handleSelectAllDocuments = () => {
    setSelectedDocumentIds(
      documents.map((document) => document.id)
    );
  };

  const handleClearDocumentSelection = () => {
    setSelectedDocumentIds([]);
  };

  const handleUpload = async (file) => {
    try {
      setUploading(true);
      setError("");

      await documentApi.upload(
        file,
        COLLECTION_NAME
      );

      await loadDocuments();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Document upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (document) => {
    const confirmed = window.confirm(
      `Delete "${document.original_filename}"?`
    );

    if (!confirmed) return;

    try {
      setError("");

      await documentApi.remove(document.id);

      await loadDocuments();
      setSelectedDocumentIds((current) =>
        current.filter((id) => id !== document.id)
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to delete the document."
      );
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>AI Knowledge Assistant</h1>
          <p>Ask questions about your documents</p>
        </div>
        <HealthIndicator health={systemHealth} />
      </header>

      {error && (
        <div className="app-error">
          <span>{error}</span>

          <button onClick={() => setError("")}>
            ×
          </button>
        </div>
      )}

      <main className="app-main">
        <aside className="sidebar">
          <div className="section-header">
            <div>
              <h2>Knowledge Base</h2>
              <span>
                {documents.length} document
                {documents.length !== 1 ? "s" : ""}
              </span>
            </div>
          </div>

          <DocumentUploader
            onUpload={handleUpload}
            disabled={uploading}
          />

          <div className="document-list-container">
            {loadingDocuments ? (
              <div className="empty-state">
                <p>Loading documents...</p>
              </div>
            ) : (
                <DocumentList
                  documents={documents}
                  selectedDocumentIds={selectedDocumentIds}
                  onSelect={handleDocumentSelect}
                  onSelectAll={handleSelectAllDocuments}
                  onClearSelection={handleClearDocumentSelection}
                  onDelete={handleDelete}
                />
            )}
          </div>
        </aside>

        <ChatPanel
          selectedDocuments={selectedDocuments}
          allDocuments={documents}
          models={models}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          collectionName={COLLECTION_NAME}
        />
      </main>
    </div>
  );
}

export default App;