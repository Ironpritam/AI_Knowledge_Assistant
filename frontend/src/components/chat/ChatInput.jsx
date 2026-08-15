import { useState } from "react";

function ChatInput({ onSend, disabled = false }) {
  const [value, setValue] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    const question = value.trim();

    if (!question || disabled) {
      return;
    }

    onSend(question);
    setValue("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  return (
    <form className="chat-input-area" onSubmit={handleSubmit}>
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask something about your documents..."
        disabled={disabled}
        rows={1}
      />

      <button
        type="submit"
        disabled={disabled || !value.trim()}
      >
        {disabled ? "Thinking..." : "Send"}
      </button>
    </form>
  );
}

export default ChatInput;