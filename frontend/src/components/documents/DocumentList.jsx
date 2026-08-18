import DocumentCard from "./DocumentCard";

function DocumentList({
  documents,
  selectedDocumentIds,
  onSelect,
  onSelectAll,
  onClearSelection,
  onDelete,
}) {
  if (!documents.length) {
    return (
      <div className="empty-state">
        <p>No documents yet</p>
        <span>
          Upload a document or code/text file to start building your knowledge base.
        </span>
      </div>
    );
  }

  const allSelected =
    selectedDocumentIds.length === documents.length;

  const someSelected =
    selectedDocumentIds.length > 0 &&
    selectedDocumentIds.length < documents.length;

  return (
    <>
      <div className="document-selection-toolbar">
        <label>
          <input
            type="checkbox"
            checked={allSelected}
            ref={(input) => {
              if (input) {
                input.indeterminate = someSelected;
              }
            }}
            onChange={() => {
              if (allSelected) {
                onClearSelection();
              } else {
                onSelectAll();
              }
            }}
          />

          <span>
            {allSelected
              ? "All documents"
              : selectedDocumentIds.length
                ? `${selectedDocumentIds.length} selected`
                : "All documents"}
          </span>
        </label>

        {selectedDocumentIds.length > 0 && (
          <button
            type="button"
            onClick={onClearSelection}
          >
            Clear
          </button>
        )}
      </div>

      <div className="document-list">
        {documents.map((document) => (
          <DocumentCard
            key={document.id}
            document={document}
            selected={selectedDocumentIds.includes(
              document.id
            )}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        ))}
      </div>
    </>
  );
}

export default DocumentList;