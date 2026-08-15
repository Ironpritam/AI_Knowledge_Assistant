function DocumentCard({ document, selected, onSelect, onDelete }) {
  const status = document.status;

  return (
    <div
      className={`document-card ${selected ? "selected" : ""}`}
      onClick={() => onSelect(document)}
    >
      <div className="document-card-header">
        <div className="document-icon">PDF</div>

        <button
          className="delete-button"
          onClick={(event) => {
            event.stopPropagation();
            onDelete(document);
          }}
          title="Delete document"
        >
          ×
        </button>
      </div>

      <div className="document-name" title={document.original_filename}>
        {document.original_filename}
      </div>

      <div className="document-meta">
        <span>{document.page_count ?? 0} pages</span>
        <span>•</span>
        <span>{document.chunk_count ?? 0} chunks</span>
      </div>

      <div className={`document-status ${status}`}>
        <span className="status-indicator" />
        {status}
      </div>
    </div>
  );
}

export default DocumentCard;