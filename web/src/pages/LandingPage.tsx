import { Link } from 'react-router-dom'
import { Upload, Zap, Eye, Hand, FileText, ShieldCheck } from 'lucide-react'
import { Layout } from '../components/Layout'

export function LandingPage() {
  return (
    <Layout>
      <section style={{
        textAlign: 'center',
        padding: '4rem 2rem 3rem',
        maxWidth: 900,
        margin: '0 auto'
      }}>
        <h1 style={{
          fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
          lineHeight: 1.2,
          marginBottom: '1rem',
          color: 'white'
        }}>
          <span style={{ color: 'white' }}>DF-InfoUI: </span>
          <span className="gradient-text">An Adaptive Multi-LLM Agent</span>
          <span style={{ color: 'white' }}> for Detecting and Fixing Accessibility Issues </span>
          <span style={{ color: 'var(--text-muted)' }}>in Automotive Infotainment User Interfaces</span>
        </h1>
        <p style={{
          fontSize: '1.1rem',
          color: 'var(--text-muted)',
          marginBottom: '2rem',
          lineHeight: 1.6
        }}>
          Revolutionary adaptive AI system featuring one Brain Agent coordinating four specialized POUR Neuron Agents to ensure WCAG 2.2 compliance and enhance user experience in automotive interfaces.
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '3rem' }}>
          <Link to="/upload" className="btn-white">
            <Upload size={18} />
            Start Full Analysis
          </Link>
          <Link to="/upload" className="btn-secondary">
            <Zap size={18} />
            Try Quick Analysis (No Sign-up)
          </Link>
        </div>
        <div style={{
          display: 'flex',
          gap: '2rem',
          justifyContent: 'center',
          flexWrap: 'wrap',
          marginBottom: '4rem'
        }}>
          <div>
            <strong style={{ color: 'white', display: 'block', fontSize: '1.1rem' }}>WCAG 2.2</strong>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Compliance</span>
          </div>
          <div>
            <strong style={{ color: 'white', display: 'block', fontSize: '1.1rem' }}>5 Agents</strong>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>1 Brain + 4 POUR Neurons</span>
          </div>
          <div>
            <strong style={{ color: 'white', display: 'block', fontSize: '1.1rem' }}>Adaptive</strong>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Multi-LLM Agent</span>
          </div>
        </div>
      </section>

      <section id="features" style={{
        padding: '2rem',
        maxWidth: 1200,
        margin: '0 auto'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '1.5rem'
        }}>
          <FeatureCard
            icon={<Eye size={24} color="var(--pour-red)" />}
            title="Perceivable Analysis"
            description="Advanced visual accessibility detection using computer vision and color theory"
            detects="Image alt-text, contrast ratios, visual elements"
          />
          <FeatureCard
            icon={<Hand size={24} color="var(--pour-orange)" />}
            title="Operable Assessment"
            description="Comprehensive interaction and navigation pattern evaluation"
            detects="Keyboard navigation, focus management, timing"
          />
          <FeatureCard
            icon={<FileText size={24} color="var(--pour-blue)" />}
            title="Understandable Review"
            description="Content structure and clarity analysis for better comprehension"
            detects="Language clarity, consistent navigation, instructions"
          />
          <FeatureCard
            icon={<ShieldCheck size={24} color="var(--pour-green)" />}
            title="Robust Validation"
            description="Technical standards compliance and assistive technology support"
            detects="HTML validation, ARIA implementation, compatibility"
          />
        </div>
      </section>
    </Layout>
  )
}

function FeatureCard({
  icon,
  title,
  description,
  detects
}: {
  icon: React.ReactNode
  title: string
  description: string
  detects: string
}) {
  return (
    <div className="summary-card" style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1rem' }}>{icon}</div>
      <h3 style={{ color: 'white', marginBottom: '0.5rem', fontSize: '1.1rem' }}>{title}</h3>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem', lineHeight: 1.5 }}>
        {description}
      </p>
      <div style={{
        backgroundColor: 'var(--bg-elevated)',
        padding: '0.75rem',
        borderRadius: 8,
        fontSize: '0.85rem',
        color: 'var(--text-muted)'
      }}>
        <strong style={{ color: 'var(--text-muted)' }}>Detects:</strong> {detects}
      </div>
    </div>
  )
}
