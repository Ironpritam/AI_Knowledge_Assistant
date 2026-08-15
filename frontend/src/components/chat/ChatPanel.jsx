import { useEffect, useRef, useState } from "react";
import { ragApi } from "../../services/api";

import "./ChatPanel.css";

function ChatPanel({
  selectedDocument,
  models,
  selectedModel,
  onModelChange,
  collectionName,
}) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  // Reset the local conversation when the document scope changes.
  // useEffect(() => {
  //   setMessages([]);
  //   setError("");
  // }, [selectedDocument?.id]);

  const handleSubmit = async (event) => {
    event?.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    if (!selectedModel) {
      setError("No LLM model is currently available.");
      return;
    }

    if (!selectedDocument) {
      setError("Select a document before asking a question.");
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const response = await ragApi.ask({
        question: trimmedQuestion,
        collection_name: collectionName,
        document_id: selectedDocument.id,
        model_id: selectedModel,
        top_k: 5,
      });

      const data = response.data;

      const assistantMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.answer || "No answer was returned.",
        modelId: data.model_id,
        sources: data.sources || [],
      };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to generate an answer."
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  const selectedModelInfo = models.find(
    (model) => model.id === selectedModel
  );

  return (
    <section className="chat-panel">
      <div className="chat-header">
        <div>
          <h2>Chat</h2>

          <span>
            {selectedDocument
              ? `Using ${selectedDocument.original_filename}`
              : "Select a document to start"}
          </span>
        </div>

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
                {!model.available ? " (offline)" : ""}
              </option>
            ))
          )}
        </select>
      </div>

      <div className="chat-content">
        {!messages.length && !loading ? (
          <div className="chat-empty-state">
            <div className="chat-icon">✦</div>

            <h2>Start a conversation</h2>

            <p>
              {selectedDocument
                ? `Ask something about ${selectedDocument.original_filename}.`
                : "Upload and select a document to begin."}
            </p>

            {selectedModelInfo && (
              <small>
                Using {selectedModelInfo.label}
              </small>
            )}
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message-row ${message.role}`}
              >
                <div className="message-bubble">
                  <div className="message-role">
                    {message.role === "user"
                      ? "You"
                      : "Assistant"}
                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>

                  {message.role === "assistant" &&
                    message.sources?.length > 0 && (
                      <div className="message-sources">
                        <div className="sources-title">
                          Sources
                        </div>

                        <div className="sources-list">
                          {message.sources.map(
                            (source, index) => {
                              const filename =
                                source.source ||
                                source.filename ||
                                source.document ||
                                "Document";

                              return (
                                <div
                                  className="source-item"
                                  key={`${filename}-${source.page}-${index}`}
                                >
                                  <span className="source-number">
                                    {index + 1}
                                  </span>

                                  <span>
                                    {filename}
                                    {source.page != null
                                      ? ` · Page ${source.page}`
                                      : ""}
                                  </span>
                                </div>
                              );
                            }
                          )}
                        </div>
                      </div>
                    )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="message-bubble thinking">
                  <div className="message-role">
                    Assistant
                  </div>

                  <div className="thinking-indicator">
                    <span />
                    <span />
                    <span />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {error && (
        <div className="chat-error">
          <span>{error}</span>

          <button
            type="button"
            onClick={() => setError("")}
          >
            ×
          </button>
        </div>
      )}

      <form
        className="chat-input-area"
        onSubmit={handleSubmit}
      >
        <textarea
          ref={inputRef}
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder={
            selectedDocument
              ? `Ask something about ${selectedDocument.original_filename}...`
              : "Select a document first..."
          }
          disabled={!selectedDocument || loading}
          rows={1}
        />

        <button
          type="submit"
          disabled={
            !selectedDocument ||
            !selectedModel ||
            !question.trim() ||
            loading
          }
        >
          {loading ? "Thinking..." : "Send"}
        </button>
      </form>
    </section>
  );
}

export default ChatPanel;