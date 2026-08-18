import { useRef, useState } from "react";

function DocumentUploader({ onUpload, disabled = false }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState("");

  const acceptedTypes = [
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".txt",
    ".md",
    ".csv",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".rs",
    ".go",
    ".kt",
    ".swift",
    ".php",
    ".rb",
    ".cs",
    ".scala",
    ".sh",
    ".bash",
    ".json",
    ".html",
    ".htm",
    ".css",
    ".sql",
    ".xml",
    ".yaml",
    ".yml",
    ".log",
  ];

  const acceptedExtensions = acceptedTypes.join(",");

  const handleFiles = (files) => {
    const file = files?.[0];

    if (!file) return;

    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;

    if (!acceptedTypes.includes(extension)) {
      setValidationError(
        "Unsupported file type. Please select a supported document or text file."
      );
      return;
    }

    setValidationError("");
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
    <div className="document-uploader">
      <div
        className={`upload-area ${isDragging ? "dragging" : ""} ${
          disabled ? "disabled" : ""
        }`}
        onDragOver={(event) => {
          event.preventDefault();

          if (!disabled) {
            setIsDragging(true);
          }
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => {
          if (!disabled) {
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(event) => {
          if (
            !disabled &&
            (event.key === "Enter" || event.key === " ")
          ) {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
      >
        <div className="upload-icon">
          {disabled ? "…" : "↑"}
        </div>

        <strong>
          {disabled ? "Processing document..." : "Upload document"}
        </strong>

        <span>
          {disabled
            ? "Please wait while the document is being indexed"
            : "Drag & drop or click to select"}
        </span>

        {!disabled && (
          <small>
            PDF, Office, text, data, and source-code files supported
          </small>
        )}

        <input
          ref={inputRef}
          type="file"
          accept={acceptedExtensions}
          onChange={handleInputChange}
          hidden
          disabled={disabled}
        />
      </div>

      {validationError && (
        <div className="upload-validation-error">
          <span>{validationError}</span>

          <button
            type="button"
            onClick={() => setValidationError("")}
            aria-label="Dismiss upload error"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default DocumentUploader;