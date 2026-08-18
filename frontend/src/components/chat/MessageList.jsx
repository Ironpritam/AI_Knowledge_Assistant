import { useEffect, useState } from "react";

import ReactMarkdown from "react-markdown";

function MessageList({
  messages,
  loading = false,
  emptyTitle = "Start a conversation",
  emptyMessage = "Ask a question about the documents in your knowledge base.",
  onRetry,
}) {
  const [copiedMessageId, setCopiedMessageId] = useState("");

  useEffect(() => {
    if (!copiedMessageId) {
      return;
    }

    const timeoutId = setTimeout(() => {
      setCopiedMessageId("");
    }, 1600);

    return () => clearTimeout(timeoutId);
  }, [copiedMessageId]);

  if (!messages.length && !loading) {
    return (
      <div className="chat-empty-state">
        <div className="chat-icon">✦</div>

        <h2>{emptyTitle}</h2>

        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message-row ${message.role}`}
        >
          <div className="message-bubble">
            <div className="message-role">
              {message.role === "user" ? "You" : "Assistant"}
            </div>

            <div className="message-content">
              {message.role === "assistant" ? (
                <ReactMarkdown >
                  {message.content}
                </ReactMarkdown>
              ) : (
                message.content
              )}
            </div>

            {message.role === "assistant" &&
              message.sources?.length > 0 && (
                <div className="message-sources">
                  <div className="sources-title">
                    Sources
                  </div>

                  <div className="sources-list">
                    {message.sources.map((source, index) => {
                      const filename =
                        source.source ||
                        source.filename ||
                        source.document ||
                        "Document";

                      const page = source.page;

                      return (
                        <div
                          className="source-item"
                          key={`${filename}-${page}-${index}`}
                        >
                          <span className="source-number">
                            {index + 1}
                          </span>

                          <div className="source-details">
                            <div className="source-filename">
                              {filename}
                            </div>

                            {page != null && (
                              <div className="source-page">
                                Page {page}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {message.role === "assistant" && (
                <div className="message-actions">
                  <button
                    type="button"
                    onClick={async () => {
                      await navigator.clipboard.writeText(
                        message.content
                      );
                      setCopiedMessageId(message.id);
                    }}
                    aria-label={copiedMessageId === message.id ? "Copied" : "Copy response"}
                    title="Copy answer"
                  >
                  {copiedMessageId === message.id ? (
                    <>
                      <span>✓</span>
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <span>📋</span>
                      <span>Copy</span>
                    </>
                  )}
                </button>

                  {message.retryQuestion && (
                    <button
                      type="button"
                      onClick={() => onRetry?.(message.retryQuestion)}
                      disabled={loading}
                      title="Ask again"
                    >
                      Retry
                    </button>
                  )}
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
              <span className="thinking-text">
                Thinking...
              </span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default MessageList;
