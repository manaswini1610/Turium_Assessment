import { useState } from 'react'

function QuestionForm({ onAsk, isLoading }) {
  const [question, setQuestion] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    if (!question.trim()) {
      return
    }
    onAsk(question.trim())
  }

  return (
    <section className="card">
      <h2>Ask Your Knowledge</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="e.g. How many paid leave days do employees receive?"
          rows={4}
          required
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
    </section>
  )
}

export default QuestionForm
