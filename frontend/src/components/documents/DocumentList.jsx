import DocumentCard from "./DocumentCard";

function DocumentList({
  documents,
  selectedDocument,
  onSelect,
  onDelete,
}) {
  if (!documents.length) {
    return (
      <div className="empty-state">
        <p>No documents yet</p>
        <span>
          Upload a PDF to start building your knowledge base.
        </span>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((document) => (
        <DocumentCard
          key={document.id}
          document={document}
          selected={selectedDocument?.id === document.id}
          onSelect={onSelect}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

export default DocumentList;