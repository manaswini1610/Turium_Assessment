import SourceCard from './SourceCard.jsx'

function AnswerCard({ answer, sources, errorMessage }) {
  if (errorMessage) {
    return (
      <section className="card">
        <p className="message error">{errorMessage}</p>
      </section>
    )
  }

  if (!answer) {
    return null
  }

  return (
    <section className="card">
      <h3>Answer</h3>
      <p className="answer-text">{answer}</p>

      {sources.length > 0 && (
        <div className="sources">
          <h4>Sources</h4>
          {sources.map((source, index) => (
            <SourceCard key={`${source.item_id}-${index}`} source={source} />
          ))}
        </div>
      )}
    </section>
  )
}

export default AnswerCard
