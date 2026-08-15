import { useRef, useState } from "react";

function DocumentUploader({ onUpload, disabled = false }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files) => {
    const file = files?.[0];

    if (!file) return;

    if (file.type !== "application/pdf") {
      alert("Please select a PDF file.");
      return;
    }

    onUpload(file);
  };

  const handleInputChange = (event) => {
    handleFiles(event.target.files);
    event.target.value = "";
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);

    if (!disabled) {
      handleFiles(event.dataTransfer.files);
    }
  };

  return (
    <div
      className={`upload-area ${isDragging ? "dragging" : ""} ${
        disabled ? "disabled" : ""
      }`}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => {
        if (!disabled) inputRef.current?.click();
      }}
    >
      <div className="upload-icon">↑</div>

      <strong>Upload PDF</strong>
      <span>Drag & drop or click to select</span>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleInputChange}
        hidden
        disabled={disabled}
      />
    </div>
  );
}

export default DocumentUploader;