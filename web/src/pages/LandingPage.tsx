import { Link } from 'react-router-dom'
import { Upload, Zap, Eye, Hand, FileText, ShieldCheck } from 'lucide-react'
import { Layout } from '../components/Layout'

export function LandingPage() {
  return (
    <Layout>
      <section
        className="hero-premium"
        style={{
          textAlign: 'center',
          padding: '5rem 2rem 4rem',
          maxWidth: 920,
          margin: '0 auto',
        }}
      >
        <p
          style={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--accent-blue)',
            marginBottom: '1.25rem',
          }}
        >
          Accessibility Intelligence
        </p>
        <h1
          style={{
            fontSize: 'clamp(2rem, 5vw, 3rem)',
            lineHeight: 1.15,
            marginBottom: '1.5rem',
            color: 'var(--text-primary)',
            letterSpacing: '-0.03em',
            fontWeight: 700,
          }}
        >
          <span style={{ color: 'var(--text-primary)' }}>DF-InfoUI: </span>
          <span className="gradient-text">An Adaptive Multi-LLM Agent</span>
          <span style={{ color: 'var(--text-primary)' }}> for Detecting and Fixing Accessibility Issues </span>
          <span style={{ color: 'var(--text-muted)' }}>in Automotive Infotainment User Interfaces</span>
        </h1>
        <p
          style={{
            fontSize: '1.125rem',
            color: 'var(--text-secondary)',
            marginBottom: '2.5rem',
            lineHeight: 1.7,
            maxWidth: 640,
            margin: '0 auto 2.5rem',
          }}
        >
          Revolutionary adaptive AI system featuring one Brain Agent coordinating four specialized POUR Neuron Agents to ensure WCAG 2.2 compliance and enhance user experience in automotive interfaces.
        </p>
        <div
          style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap',
            marginBottom: '4rem',
          }}
        >
          <Link to="/upload" className="btn-white">
            <Upload size={20} strokeWidth={2} />
            Start Full Analysis
          </Link>
          <Link to="/upload" className="btn-secondary">
            <Zap size={20} strokeWidth={2} />
            Try Quick Analysis (No Sign-up)
          </Link>
        </div>
        <div
          style={{
            display: 'flex',
            gap: '3rem',
            justifyContent: 'center',
            flexWrap: 'wrap',
            marginBottom: '4rem',
          }}
        >
          <StatPill label="WCAG 2.2" sub="Compliance" />
          <StatPill label="5 Agents" sub="1 Brain + 4 POUR Neurons" />
          <StatPill label="Adaptive" sub="Multi-LLM Agent" />
        </div>
      </section>

      <section
        id="features"
        style={{
          padding: '3rem 2rem 5rem',
          maxWidth: 1280,
          margin: '0 auto',
        }}
      >
        <p
          style={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            marginBottom: '0.75rem',
            textAlign: 'center',
          }}
        >
          POUR Framework
        </p>
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 3vw, 2rem)',
            fontWeight: 700,
            color: 'var(--text-primary)',
            textAlign: 'center',
            marginBottom: '2.5rem',
            letterSpacing: '-0.02em',
          }}
        >
          Four pillars of accessibility analysis
        </h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem',
          }}
        >
          <FeatureCard
            icon={<Eye size={28} color="var(--pour-red)" strokeWidth={1.75} />}
            title="Perceivable Analysis"
            description="Advanced visual accessibility detection using computer vision and color theory"
            detects="Image alt-text, contrast ratios, visual elements"
          />
          <FeatureCard
            icon={<Hand size={28} color="var(--pour-orange)" strokeWidth={1.75} />}
            title="Operable Assessment"
            description="Comprehensive interaction and navigation pattern evaluation"
            detects="Keyboard navigation, focus management, timing"
          />
          <FeatureCard
            icon={<FileText size={28} color="var(--pour-blue)" strokeWidth={1.75} />}
            title="Understandable Review"
            description="Content structure and clarity analysis for better comprehension"
            detects="Language clarity, consistent navigation, instructions"
          />
          <FeatureCard
            icon={<ShieldCheck size={28} color="var(--pour-green)" strokeWidth={1.75} />}
            title="Robust Validation"
            description="Technical standards compliance and assistive technology support"
            detects="HTML validation, ARIA implementation, compatibility"
          />
        </div>
      </section>
    </Layout>
  )
}

function StatPill({ label, sub }: { label: string; sub: string }) {
  return (
    <div
      style={{
        padding: '1rem 1.5rem',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 12,
        minWidth: 140,
        transition: 'border-color 0.25s ease, box-shadow 0.25s ease',
      }}
      className="card-premium"
    >
      <strong
        style={{
          color: 'var(--text-primary)',
          display: 'block',
          fontSize: '1.125rem',
          fontWeight: 600,
          letterSpacing: '-0.02em',
        }}
      >
        {label}
      </strong>
      <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', fontWeight: 500 }}>{sub}</span>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
  detects,
}: {
  icon: React.ReactNode
  title: string
  description: string
  detects: string
}) {
  return (
    <div className="card-premium" style={{ padding: '1.75rem' }}>
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 12,
          background: 'var(--bg-elevated)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1.25rem',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {icon}
      </div>
      <h3
        style={{
          color: 'var(--text-primary)',
          marginBottom: '0.5rem',
          fontSize: '1.125rem',
          fontWeight: 600,
          letterSpacing: '-0.02em',
        }}
      >
        {title}
      </h3>
      <p
        style={{
          color: 'var(--text-secondary)',
          fontSize: '0.9375rem',
          marginBottom: '1.25rem',
          lineHeight: 1.6,
        }}
      >
        {description}
      </p>
      <div
        style={{
          backgroundColor: 'var(--bg-elevated)',
          padding: '1rem 1.25rem',
          borderRadius: 10,
          fontSize: '0.8125rem',
          color: 'var(--text-muted)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <strong style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Detects:</strong> {detects}
      </div>
    </div>
  )
}
