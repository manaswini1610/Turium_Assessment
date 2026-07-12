function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString()
}

function ItemsList({ items, isLoading, errorMessage }) {
  return (
    <section className="card">
      <h2>Saved Items</h2>

      {isLoading && <p>Loading saved items...</p>}
      {errorMessage && <p className="message error">{errorMessage}</p>}

      {!isLoading && !errorMessage && items.length === 0 && (
        <p className="empty-state">
          No knowledge saved yet. Add a note or a webpage URL above to get started.
        </p>
      )}

      {!isLoading && items.length > 0 && (
        <ul className="items-list">
          {items.map((item) => (
            <li key={item.id} className="item-card">
              <div className="item-header">
                <h3>{item.title}</h3>
                <span className={`badge ${item.source_type}`}>{item.source_type}</span>
              </div>
              {item.source_url && (
                <a href={item.source_url} target="_blank" rel="noopener noreferrer">
                  {item.source_url}
                </a>
              )}
              <p className="preview">{item.content_preview}</p>
              <p className="timestamp">{formatDate(item.created_at)}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default ItemsList
