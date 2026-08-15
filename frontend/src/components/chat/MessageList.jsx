function MessageList({ messages }) {
  if (messages.length === 0) {
    return (
      <div className="chat-empty-state">
        <div className="chat-icon">✦</div>

        <h2>Start a conversation</h2>

        <p>
          Ask a question about the documents in your
          knowledge base.
        </p>
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
            <div className="message-content">
              {message.content}
            </div>

            {message.sources?.length > 0 && (
              <div className="message-sources">
                <div className="sources-title">
                  Sources
                </div>

                {message.sources.map((source, index) => (
                  <div
                    key={`${source.source}-${source.page}-${index}`}
                    className="source-item"
                  >
                    <span>
                      {source.source}
                    </span>

                    {source.page !== undefined && (
                      <span>
                        · Page {source.page}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default MessageList;