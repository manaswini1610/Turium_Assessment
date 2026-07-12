function SourceCard({ source }) {
  return (
    <div className="source-card">
      <div className="source-header">
        <strong>{source.title}</strong>
        <span className={`badge ${source.source_type}`}>{source.source_type}</span>
      </div>
      {source.source_url && (
        <a href={source.source_url} target="_blank" rel="noopener noreferrer">
          {source.source_url}
        </a>
      )}
      <p className="snippet">{source.snippet}</p>
      <p className="similarity">Similarity score: {source.similarity_score.toFixed(2)}</p>
    </div>
  )
}

export default SourceCard
