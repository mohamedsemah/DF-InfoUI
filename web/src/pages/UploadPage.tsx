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
    const file = acceptedFiles[0]
    if (!file) return

    if (!file.name.endsWith('.zip')) {
      setError('Please upload a ZIP file containing your UI files.')
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
    <Layout showBack backLabel="Back to Home" backTo="/">
      <div className="container" style={{ textAlign: 'center', paddingTop: '2rem' }}>
        <h1 style={{ marginBottom: '0.75rem', fontSize: 'clamp(1.5rem, 3vw, 2rem)' }}>
          <span style={{ color: 'white' }}>Upload Your </span>
          <span style={{ color: 'var(--accent-purple)' }}>Interface Files</span>
          <span style={{ color: 'white' }}> for </span>
          <span style={{ color: 'var(--accent-blue)' }}>Accessibility Analysis</span>
        </h1>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', maxWidth: 560, margin: '0 auto 2rem' }}>
          Drag and drop your UI files or click to browse. We'll analyze them using our AI-powered accessibility detection system.
        </p>

        <div
          {...getRootProps()}
          className={`upload-area ${isDragActive ? 'dragover' : ''}`}
          style={{
            opacity: isUploading ? 0.6 : 1,
            cursor: isUploading ? 'not-allowed' : 'pointer',
            maxWidth: 560,
            margin: '0 auto 1.5rem'
          }}
        >
          <input {...getInputProps()} />
          <div style={{ marginBottom: '1rem' }}>
            <Upload size={48} color="var(--text-muted)" />
          </div>
          <p style={{ color: 'white', marginBottom: '0.5rem', fontSize: '1.1rem' }}>Drag & drop files here</p>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            or <span style={{ color: 'var(--accent-blue)', cursor: 'pointer', textDecoration: 'underline' }}>browse files</span>
          </p>
        </div>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Supported formats: HTML, CSS, JS, JAVA, KT, XML, Images (pack in ZIP)
        </p>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            color: '#f87171',
            backgroundColor: 'rgba(220, 38, 38, 0.15)',
            padding: '1rem',
            borderRadius: 8,
            marginBottom: '1.5rem',
            maxWidth: 480,
            margin: '0 auto 1.5rem'
          }}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '3rem' }}>
          Upload a ZIP containing your project files to start analysis.
        </p>

        {/* Brain Agent Coordination */}
        <div style={{
          maxWidth: 560,
          margin: '0 auto',
          padding: '2rem',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 12,
          textAlign: 'center'
        }}>
          <div style={{
            width: 56,
            height: 56,
            margin: '0 auto 1rem',
            borderRadius: '50%',
            background: 'var(--gradient-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Cpu size={28} color="white" />
          </div>
          <h3 style={{ color: 'white', marginBottom: '0.5rem', fontSize: '1.15rem' }}>Brain Agent Coordination</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem', lineHeight: 1.5 }}>
            Our central Brain Agent coordinates four specialized Neuron Agents, each focused on a specific aspect of the POUR accessibility framework.
          </p>
          <div style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--pour-red)' }} /> Perceivable
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--pour-orange)' }} /> Operable
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--pour-blue)' }} /> Understandable
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: 'var(--pour-green)' }} /> Robust
            </span>
          </div>
        </div>
      </div>
    </Layout>
  )
}
