import { useEffect, useRef, useState } from "react";
import { ragApi } from "../../services/api";

import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

import "./ChatPanel.css";

function ChatPanel({
  selectedDocuments,
  allDocuments,
  models,
  selectedModel,
  onModelChange,
  collectionName,
}) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const chatContentRef = useRef(null);

  useEffect(() => {
    const container = chatContentRef.current;

    if (!container) {
      return;
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  // Conversation is intentionally local-state only for V1.
  // Reset when document scope changes.
  useEffect(() => {
    setMessages([]);
    setError("");
  }, [
    selectedDocuments.map((document) => document.id).join(","),
  ]);

  const handleSend = async (question) => {
    if (!question || loading) {
      return;
    }

    if (!selectedModel) {
      setError("No LLM model is currently available.");
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setError("");
    setLoading(true);

    try {
      const response = await ragApi.ask({
        question,
        collection_name: collectionName,
        document_ids:
          selectedDocuments.length > 0
            ? selectedDocuments.map(
                (document) => document.id
              )
            : null,
        model_id: selectedModel,
        top_k: 5,
      });

      const data = response.data;

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content:data.answer || "No answer was returned.",
        modelId: data.model_id,
        sources: data.sources || [],
        retryQuestion: question,
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to generate an answer. Please check document selection or health of the application."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = () => {
    if (loading || messages.length === 0) {
      return;
    }

    setMessages([]);
    setError("");
  };

  const inputPlaceholder =
    selectedDocuments.length === 0
      ? "Ask something about your knowledge base..."
      : selectedDocuments.length === 1
        ? `Ask something about ${selectedDocuments[0].original_filename}...`
        : `Ask something across ${selectedDocuments.length} documents...`;

  const emptyMessage =
    selectedDocuments.length === 0
      ? "Ask something about your knowledge base..."
      : selectedDocuments.length === 1
        ? `Ask something about ${selectedDocuments[0].original_filename}...`
        : `Ask something across ${selectedDocuments.length} documents...`;

  return (
    <section className="chat-panel">
      <div className="chat-header">
        <div>
          <h2>Chat</h2>

          <span>
            {selectedDocuments.length === 0
              ? `Using all ${allDocuments.length} documents`
              : selectedDocuments.length === 1
                ? `Using ${selectedDocuments[0].original_filename}`
                : `Using ${selectedDocuments.length} documents`}
          </span>
        </div>

        <div className="chat-header-actions">
          {messages.length > 0 && (
            <button
              type="button"
              className="clear-chat-button"
              onClick={handleClearChat}
              disabled={loading}
            >
              New chat
            </button>
          )}

          <select
            value={selectedModel}
            onChange={(event) =>
              onModelChange(event.target.value)
            }
            disabled={!models.length || loading}
            aria-label="Select language model"
          >
            {!models.length ? (
              <option value="">
                No models available
              </option>
            ) : (
              models.map((model) => (
                <option
                  key={model.id}
                  value={model.id}
                  disabled={!model.available}
                >
                  {model.label}
                  {!model.available
                    ? " (offline)"
                    : ""}
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      <div className="chat-content" ref={chatContentRef}>
        <MessageList
          messages={messages}
          loading={loading}
          emptyMessage={emptyMessage}
          // bottomRef={messagesEndRef}
          onRetry={handleSend}
        />
      </div>

      {error && (
        <div className="chat-error">
          <span>{error}</span>

          <button
            type="button"
            onClick={() => setError("")}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      <ChatInput
        onSend={handleSend}
        disabled={
          loading ||
          allDocuments.length === 0 ||
          !selectedModel
        }
        placeholder={inputPlaceholder}
      />
    </section>
  );
}

export default ChatPanel;
