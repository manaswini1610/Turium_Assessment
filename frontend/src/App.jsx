import { useCallback, useEffect, useState } from 'react'
import IngestForm from './components/IngestForm.jsx'
import ItemsList from './components/ItemsList.jsx'
import QuestionForm from './components/QuestionForm.jsx'
import AnswerCard from './components/AnswerCard.jsx'
import { askQuestion, fetchItems } from './services/api.js'

function App() {
  const [items, setItems] = useState([])
  const [isLoadingItems, setIsLoadingItems] = useState(false)
  const [itemsError, setItemsError] = useState('')

  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [isAsking, setIsAsking] = useState(false)
  const [askError, setAskError] = useState('')

  const loadItems = useCallback(async () => {
    setIsLoadingItems(true)
    setItemsError('')
    try {
      const data = await fetchItems()
      setItems(data)
    } catch (error) {
      setItemsError(error.message)
    } finally {
      setIsLoadingItems(false)
    }
  }, [])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  async function handleAsk(question) {
    setIsAsking(true)
    setAskError('')
    setAnswer('')
    setSources([])
    try {
      const data = await askQuestion(question, 3)
      setAnswer(data.answer)
      setSources(data.sources)
    } catch (error) {
      setAskError(error.message)
    } finally {
      setIsAsking(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Knowledge Inbox</h1>
        <p>Save notes and webpages, then ask questions answered only from your saved content.</p>
      </header>

      <main className="app-main">
        <IngestForm onIngestSuccess={loadItems} />
        <ItemsList items={items} isLoading={isLoadingItems} errorMessage={itemsError} />
        <QuestionForm onAsk={handleAsk} isLoading={isAsking} />
        <AnswerCard answer={answer} sources={sources} errorMessage={askError} />
      </main>
    </div>
  )
}

export default App
