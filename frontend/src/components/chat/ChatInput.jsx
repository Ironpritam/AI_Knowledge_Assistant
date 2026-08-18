import React, { useEffect, useRef } from "react";

function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask something about your documents...",
}) {
  const [value, setValue] = React.useState("");
  const textareaRef = useRef(null);

  const resizeTextarea = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  };

  useEffect(() => {
    resizeTextarea();
  }, [value]);

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
        ref={textareaRef}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        aria-label="Ask a question"
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