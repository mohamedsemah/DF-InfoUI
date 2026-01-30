import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, Cpu, AlertCircle } from 'lucide-react'
import { uploadFile } from '../services/api'
import { Layout } from '../components/Layout'

export function UploadPage() {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const onDrop = async (acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return
    setIsUploading(true)
    setError(null)
    try {
      const response = await uploadFile(acceptedFiles)
      navigate(`/job/${response.job_id}`)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err && typeof (err as { response?: { data?: { detail?: string } } }).response?.data?.detail === 'string'
        ? (err as { response: { data: { detail: string } } }).response.data.detail
        : 'Upload failed. Please try again.'
      setError(message)
      console.error('Upload error:', err)
    } finally {
      setIsUploading(false)
    }
  }

  const acceptedTypes = {
    'application/zip': ['.zip'],
    'text/html': ['.html', '.htm'],
    'text/css': ['.css'],
    'application/javascript': ['.js', '.jsx', '.mjs', '.cjs'],
    'application/typescript': ['.ts', '.tsx'],
    'text/x-java-source': ['.java'],
    'text/x-kotlin-source': ['.kt', '.kts'],
    'application/xml': ['.xml'],
    'text/xml': ['.xml'],
    'image/png': ['.png'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/gif': ['.gif'],
    'image/svg+xml': ['.svg'],
    'image/webp': ['.webp'],
    'image/x-icon': ['.ico'],
    'image/bmp': ['.bmp'],
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes,
    multiple: true,
    disabled: isUploading,
  })

  return (
    <Layout showBack backLabel="Back to Home" backTo="/">
      <div className="container" style={{ textAlign: 'center', paddingTop: '2.5rem' }}>
        <p
          style={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--accent-blue)',
            marginBottom: '0.75rem',
          }}
        >
          Upload & Analyze
        </p>
        <h1
          style={{
            marginBottom: '1rem',
            fontSize: 'clamp(1.75rem, 3.5vw, 2.25rem)',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)',
          }}
        >
          <span style={{ color: 'var(--text-primary)' }}>Upload Your </span>
          <span className="gradient-text">Interface Files</span>
          <span style={{ color: 'var(--text-primary)' }}> for </span>
          <span className="gradient-text">Accessibility Analysis</span>
        </h1>
        <p
          style={{
            color: 'var(--text-secondary)',
            marginBottom: '2.5rem',
            maxWidth: 560,
            margin: '0 auto 2.5rem',
            fontSize: '1rem',
            lineHeight: 1.65,
          }}
        >
          Drag and drop a ZIP or individual files. We'll analyze them using our AI-powered accessibility detection system.
        </p>

        <div
          {...getRootProps()}
          className={`upload-area ${isDragActive ? 'dragover' : ''}`}
          style={{
            opacity: isUploading ? 0.6 : 1,
            cursor: isUploading ? 'not-allowed' : 'pointer',
            maxWidth: 560,
            margin: '0 auto 1.5rem',
          }}
        >
          <input {...getInputProps()} />
          <div style={{ marginBottom: '1.25rem' }}>
            <Upload size={52} color="var(--text-muted)" strokeWidth={1.5} />
          </div>
          <p style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '1.125rem', fontWeight: 600 }}>
            Drag & drop files here
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem' }}>
            or <span style={{ color: 'var(--accent-blue)', cursor: 'pointer', fontWeight: 500 }}>browse files</span>
          </p>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem', letterSpacing: '0.01em' }}>
          ZIP or individual files: HTML, CSS, JS, JSX, TS, TSX, Java, Kotlin, XML, images (PNG, JPG, SVG, etc.)
        </p>

        {error && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.625rem',
              color: 'var(--pour-red)',
              backgroundColor: 'var(--pour-red-bg)',
              padding: '1rem 1.25rem',
              borderRadius: 12,
              marginBottom: '1.5rem',
              maxWidth: 480,
              margin: '0 auto 1.5rem',
              border: '1px solid rgba(248, 113, 113, 0.2)',
            }}
          >
            <AlertCircle size={20} strokeWidth={2} />
            <span style={{ fontWeight: 500 }}>{error}</span>
          </div>
        )}

        <p style={{ color: 'var(--text-faint)', fontSize: '0.8125rem', marginBottom: '3rem' }}>
          Upload a ZIP or select multiple supported files to start analysis.
        </p>

        <div className="card-premium" style={{ maxWidth: 560, margin: '0 auto', padding: '2.25rem', textAlign: 'center' }}>
          <div
            style={{
              width: 64,
              height: 64,
              margin: '0 auto 1.25rem',
              borderRadius: '50%',
              background: 'var(--gradient-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 24px rgba(79, 140, 255, 0.35)',
            }}
          >
            <Cpu size={32} color="white" strokeWidth={2} />
          </div>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '1.25rem', fontWeight: 600, letterSpacing: '-0.02em' }}>
            Brain Agent Coordination
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9375rem', marginBottom: '1.5rem', lineHeight: 1.6 }}>
            Our central Brain Agent coordinates four specialized Neuron Agents, each focused on a specific aspect of the POUR accessibility framework.
          </p>
          <div style={{ display: 'flex', gap: '1.25rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            {[
              { color: 'var(--pour-red)', label: 'Perceivable' },
              { color: 'var(--pour-orange)', label: 'Operable' },
              { color: 'var(--pour-blue)', label: 'Understandable' },
              { color: 'var(--pour-green)', label: 'Robust' },
            ].map(({ color, label }) => (
              <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: color }} />
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  )
}
