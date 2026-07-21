import { useState } from 'react'

function App() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState('')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    // Sample proxy call to the backend - this will proxy through vite to /api/your-endpoint
    // setResponse('Loading...')
    // const res = await fetch('/api/query', { method: 'POST', body: JSON.stringify({ query }) })
    // const data = await res.json()
    // setResponse(data.message)
    setResponse(`Mock response for: ${query}`)
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Trace RAG Pipeline</h1>
      
      <form onSubmit={handleSearch}>
        <input 
          type="text" 
          value={query} 
          onChange={(e) => setQuery(e.target.value)} 
          placeholder="Ask something..."
          style={{ padding: '0.5rem', width: '300px' }}
        />
        <button type="submit" style={{ padding: '0.5rem 1rem', marginLeft: '0.5rem' }}>Send</button>
      </form>

      {response && (
        <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}>
          <strong>Response:</strong>
          <p>{response}</p>
        </div>
      )}
    </div>
  )
}

export default App
