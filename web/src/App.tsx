import { Routes, Route } from 'react-router-dom'
import { UploadPage } from './pages/UploadPage'
import { JobDetailPage } from './pages/JobDetailPage'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/job/:jobId" element={<JobDetailPage />} />
      </Routes>
    </div>
  )
}

export default App
