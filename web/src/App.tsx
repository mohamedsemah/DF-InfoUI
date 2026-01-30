import { Routes, Route } from 'react-router-dom'
import { LandingPage } from './pages/LandingPage'
import { UploadPage } from './pages/UploadPage'
import { JobDetailPage } from './pages/JobDetailPage'
import { ReportPage } from './pages/ReportPage'

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/job/:jobId" element={<JobDetailPage />} />
        <Route path="/job/:jobId/report" element={<ReportPage />} />
      </Routes>
    </div>
  )
}

export default App
