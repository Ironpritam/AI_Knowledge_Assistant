function HealthIndicator({ health }) {
  const status = health?.status || "offline";
  const components = health?.components || {};

  const statusLabel = {
    healthy: "System healthy",
    degraded: "System degraded",
    unhealthy: "System unhealthy",
    offline: "Backend offline",
  }[status] || "Unknown status";

  const componentLabels = {
    database: "Database",
    vector_store: "Vector store",
    embedding_service: "Embedding service",
    llm_provider: "LLM provider",
  };

  return (
    <div className="health-wrapper">
      <button
        type="button"
        className="health-indicator"
        title="View system health"
      >
        <span className={`status-dot ${status}`} />
        <span>{statusLabel}</span>
      </button>

      <div className="health-popover">
        <div className="health-popover-header">
          <strong>System health</strong>
          <span className={`health-badge ${status}`}>
            {status}
          </span>
        </div>

        <div className="health-components">
          {Object.entries(componentLabels).map(
            ([key, label]) => {
              const component = components[key];
              const componentStatus =
                component?.status || "unknown";

              return (
                <div
                  key={key}
                  className="health-component"
                >
                  <div>
                    <span
                      className={`status-dot ${componentStatus}`}
                    />
                    <span>{label}</span>
                  </div>

                  <span className="health-component-status">
                    {componentStatus}
                  </span>
                </div>
              );
            }
          )}
        </div>
      </div>
    </div>
  );
}

export default HealthIndicator;