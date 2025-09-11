import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, File, AlertCircle } from 'lucide-react'
import { uploadFile } from '../services/api'

export function UploadPage() {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const onDrop = async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (!file.name.endsWith('.zip')) {
      setError('Please upload a ZIP file')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const response = await uploadFile(file)
      navigate(`/job/${response.job_id}`)
    } catch (err) {
      setError('Upload failed. Please try again.')
      console.error('Upload error:', err)
    } finally {
      setIsUploading(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/zip': ['.zip']
    },
    multiple: false,
    disabled: isUploading
  })

  return (
    <div className="container">
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1>DF-InfoUI</h1>
        <p style={{ fontSize: '1.2rem', color: '#666', marginBottom: '2rem' }}>
          Adaptive Multi-Agent Accessibility Evaluator & Fixer for Automotive Infotainment UI
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`upload-area ${isDragActive ? 'dragover' : ''}`}
        style={{
          opacity: isUploading ? 0.6 : 1,
          cursor: isUploading ? 'not-allowed' : 'pointer'
        }}
      >
        <input {...getInputProps()} />
        
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>
          {isUploading ? <File /> : <Upload />}
        </div>
        
        {isUploading ? (
          <div>
            <h3>Uploading and processing...</h3>
            <p>Please wait while we analyze your files</p>
          </div>
        ) : isDragActive ? (
          <div>
            <h3>Drop the ZIP file here</h3>
            <p>Release to upload</p>
          </div>
        ) : (
          <div>
            <h3>Drag & drop your ZIP file here</h3>
            <p>or click to select a file</p>
            <p style={{ fontSize: '0.9rem', color: '#666', marginTop: '1rem' }}>
              Supported files: HTML, JS, JSX, TS, TSX, CSS
            </p>
          </div>
        )}
      </div>

      {error && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: '#d32f2f',
          backgroundColor: '#ffebee',
          padding: '1rem',
          borderRadius: '8px',
          marginTop: '1rem'
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      <div style={{ marginTop: '3rem', textAlign: 'center' }}>
        <h3>How it works</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '2rem',
          marginTop: '2rem'
        }}>
          <div>
            <h4>1. Upload</h4>
            <p>Upload your ZIP file containing HTML, JS, JSX, TS, TSX, and CSS files</p>
          </div>
          <div>
            <h4>2. Analyze</h4>
            <p>Our AI agents analyze your code for accessibility issues using WCAG 2.1 guidelines</p>
          </div>
          <div>
            <h4>3. Fix</h4>
            <p>Automated fixes are applied to resolve accessibility issues</p>
          </div>
          <div>
            <h4>4. Validate</h4>
            <p>Fixes are validated using eslint and axe-core to ensure compliance</p>
          </div>
        </div>
      </div>
    </div>
  )
}
