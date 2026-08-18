// function DocumentCard({
//   document,
//   selected,
//   onSelect,
//   onDelete,
// }) {
//   const status = document.status;

//   return (
//     <div
//       className={`document-card ${selected ? "selected" : ""}`}
//       onClick={() => onSelect(document)}
//     >
//       <div className="document-card-header">
//         <div className="document-icon">
//           {document.original_filename?.split(".").pop()?.toUpperCase() || "FILE"}
//         </div>

//         <div className="document-selection">
//           <input
//             type="checkbox"
//             checked={selected}
//             onChange={() => onSelect(document)}
//             onClick={(event) => event.stopPropagation()}
//             aria-label={`Select ${document.original_filename}`}
//           />
//         </div>

//         <button
//           className="delete-button"
//           onClick={(event) => {
//             event.stopPropagation();
//             onDelete(document);
//           }}
//           title="Delete document"
//         >
//           ×
//         </button>
//       </div>

//       <div
//         className="document-name"
//         title={document.original_filename}
//       >
//         {document.original_filename}
//       </div>

//       <div className="document-meta">
//         <span>{document.page_count ?? 0} pages</span>
//         <span>•</span>
//         <span>{document.chunk_count ?? 0} chunks</span>
//       </div>

//       <div className={`document-status ${status}`}>
//         <span className="status-indicator" />
//         {status}
//       </div>
//     </div>
//   );
// }

// export default DocumentCard;

function DocumentCard({
  document,
  selected,
  onSelect,
  onDelete,
}) {
  const status = document.status || "unknown";

  const statusLabel = {
    processed: "Processed",
    processing: "Processing",
    pending: "Pending",
    failed: "Failed",
  }[status] || status;

  return (
    <div
      className={`document-card ${selected ? "selected" : ""}`}
      onClick={() => onSelect(document)}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(document);
        }
      }}
    >
      <div className="document-card-header">
        <div className="document-icon">PDF</div>

        <div className="document-card-actions">
          <span
            className={`selection-indicator ${
              selected ? "checked" : ""
            }`}
            aria-hidden="true"
          >
            {selected ? "✓" : ""}
          </span>

          <button
            type="button"
            className="delete-button"
            onClick={(event) => {
              event.stopPropagation();
              onDelete(document);
            }}
            title={`Delete ${document.original_filename}`}
            aria-label={`Delete ${document.original_filename}`}
          >
            ×
          </button>
        </div>
      </div>

      <div
        className="document-name"
        title={document.original_filename}
      >
        {document.original_filename}
      </div>

      <div className="document-meta">
        <span>{document.page_count ?? 0} pages</span>
        <span>•</span>
        <span>{document.chunk_count ?? 0} chunks</span>
      </div>

      <div className={`document-status ${status}`}>
        <span className="status-indicator" />
        {statusLabel}
      </div>
    </div>
  );
}

export default DocumentCard;