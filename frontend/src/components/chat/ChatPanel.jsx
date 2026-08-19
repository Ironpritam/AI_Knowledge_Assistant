import { useCallback, useEffect, useRef, useState } from "react";
import { chatApi,ragApi } from "../../services/api";

import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

import "./ChatPanel.css";

const getErrorMessage = (err, fallback) =>
  err.response?.data?.error?.message ||
  err.response?.data?.detail ||
  fallback;

function ChatPanel({
  selectedDocuments,
  allDocuments,
  models,
  selectedModel,
  onModelChange,
  collectionName,
}) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const chatContentRef = useRef(null);
  const initializedRef = useRef(false);

  const refreshSessions = useCallback(async () => {
    const response = await chatApi.listSessions();
    setSessions(response.data.items);
    return response.data.items;
  }, []);

  const activateSession = useCallback(async (nextSessionId) => {
    const response = await chatApi.getSession(nextSessionId);
    const session = response.data;

    setSessionId(session.id);
    setMessages(session.messages || []);
    localStorage.setItem("activeChatSessionId", session.id);
  }, []);

  const createAndActivateSession = useCallback(async () => {
    const response = await chatApi.createSession();
    const session = response.data;

    setSessionId(session.id);
    setMessages([]);
    localStorage.setItem("activeChatSessionId", session.id);
    await refreshSessions();
    return session;
  }, [refreshSessions]);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }
    initializedRef.current = true;

    const initializeSession = async () => {
      try {
        setError("");
        await refreshSessions();

        const storedSessionId = localStorage.getItem(
          "activeChatSessionId"
        );

        if (storedSessionId) {
          try {
            const response =
              await chatApi.getSession(storedSessionId);

            const session = response.data;

            setSessionId(session.id);
            setMessages(session.messages || []);

            return;
          } catch (err) {
            console.warn(
              "Stored chat session could not be restored. Creating a new session.",
              err
            );

            localStorage.removeItem("activeChatSessionId");
          }
        }

        await createAndActivateSession();
      } catch (err) {
        console.error(
          "Failed to initialize chat session:",
          err
        );

        setError(
          getErrorMessage(err, "Unable to initialize chat session.")
        );
      }
    };

    initializeSession();
  }, [createAndActivateSession, refreshSessions]);

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


  const handleSend = async (question) => {
    if (!question || loading) {
      return;
    }

    if (!sessionId) {
      setError("Chat session is still initializing. Please try again.");
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
          : [],
        model_id: selectedModel,
        top_k: 5,
        session_id: sessionId,
        client_request_id: crypto.randomUUID(),
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
      await refreshSessions();
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Unable to generate an answer. Please check document selection or health of the application."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (loading) {
      return;
    }

    try {
      setError("");

      await createAndActivateSession();
    } catch (err) {
      console.error(
        "Failed to create new chat session:",
        err
      );

      setError(
        getErrorMessage(err, "Unable to start a new chat.")
      );
    }
  };

  const handleSessionChange = async (event) => {
    const nextSessionId = event.target.value;
    if (!nextSessionId || nextSessionId === sessionId || loading) {
      return;
    }

    try {
      setError("");
      await activateSession(nextSessionId);
    } catch (err) {
      setError(getErrorMessage(err, "Unable to open this chat."));
      await refreshSessions();
    }
  };

  const handleDeleteSession = async () => {
    if (!sessionId || loading) {
      return;
    }

    try {
      setError("");
      await chatApi.deleteSession(sessionId);
      const remainingSessions = await refreshSessions();
      const nextSession = remainingSessions[0];

      if (nextSession) {
        await activateSession(nextSession.id);
      } else {
        await createAndActivateSession();
      }
    } catch (err) {
      setError(getErrorMessage(err, "Unable to delete this chat."));
    }
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
          <label className="session-picker">
            <span className="sr-only">Select chat</span>
            <select
              value={sessionId || ""}
              onChange={handleSessionChange}
              disabled={!sessions.length || loading}
              aria-label="Select chat"
            >
              {sessions.map((session) => (
                <option key={session.id} value={session.id}>
                  {session.title || "New chat"}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className="clear-chat-button"
            onClick={handleClearChat}
            disabled={loading}
          >
            New chat
          </button>

          <button
            type="button"
            className="delete-chat-button"
            onClick={handleDeleteSession}
            disabled={!sessionId || loading}
          >
            Delete
          </button>

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
