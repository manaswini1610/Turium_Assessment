import { useState } from 'react'
import { ingestNote, ingestUrl } from '../services/api.js'

const SOURCE_TYPES = {
  NOTE: 'note',
  URL: 'url',
}

function IngestForm({ onIngestSuccess }) {
  const [sourceType, setSourceType] = useState(SOURCE_TYPES.NOTE)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [url, setUrl] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  function resetForm() {
    setTitle('')
    setContent('')
    setUrl('')
  }

  function handleTabChange(nextSourceType) {
    setSourceType(nextSourceType)
    setSuccessMessage('')
    setErrorMessage('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSuccessMessage('')
    setErrorMessage('')
    setIsSubmitting(true)

    try {
      let result
      if (sourceType === SOURCE_TYPES.NOTE) {
        result = await ingestNote(title.trim(), content.trim())
      } else {
        result = await ingestUrl(url.trim())
      }
      setSuccessMessage(`Saved "${result.title}" (${result.chunk_count} chunk${result.chunk_count === 1 ? '' : 's'}).`)
      resetForm()
      onIngestSuccess()
    } catch (error) {
      setErrorMessage(error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h2>Add Knowledge</h2>
      <div className="tabs">
        <button
          type="button"
          className={sourceType === SOURCE_TYPES.NOTE ? 'tab active' : 'tab'}
          onClick={() => handleTabChange(SOURCE_TYPES.NOTE)}
        >
          Note
        </button>
        <button
          type="button"
          className={sourceType === SOURCE_TYPES.URL ? 'tab active' : 'tab'}
          onClick={() => handleTabChange(SOURCE_TYPES.URL)}
        >
          URL
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {sourceType === SOURCE_TYPES.NOTE ? (
          <>
            <label htmlFor="note-title">Title</label>
            <input
              id="note-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Leave Policy"
              required
            />
            <label htmlFor="note-content">Content</label>
            <textarea
              id="note-content"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Paste or type the note content here"
              rows={6}
              required
            />
          </>
        ) : (
          <>
            <label htmlFor="note-url">Webpage URL</label>
            <input
              id="note-url"
              type="text"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://example.com/article"
              required
            />
          </>
        )}

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save Knowledge'}
        </button>
      </form>

      {successMessage && <p className="message success">{successMessage}</p>}
      {errorMessage && <p className="message error">{errorMessage}</p>}
    </section>
  )
}

export default IngestForm
