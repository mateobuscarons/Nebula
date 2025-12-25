import { useAuth } from '../contexts/AuthContext';
import './LandingPage.css';

export default function LandingPage() {
  const { signInWithGoogle } = useAuth();

  const handleSignIn = async () => {
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error('Sign in error:', error);
    }
  };

  return (
    <div className="landing-page">
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.1); }
        }
        .pulse-1 { animation: pulse 8s ease-in-out infinite; }
        .pulse-2 { animation: pulse 10s ease-in-out infinite; }
      `}</style>

      {/* Neural network background */}
      <svg style={{
        position: 'fixed', inset: 0, width: '100%', height: '100%',
        pointerEvents: 'none', zIndex: 1, opacity: 0.6
      }}>
        <defs>
          <radialGradient id="neuronGlow">
            <stop offset="0%" style={{ stopColor: 'rgba(139,92,246,0.8)', stopOpacity: 1 }} />
            <stop offset="50%" style={{ stopColor: 'rgba(139,92,246,0.3)', stopOpacity: 0.5 }} />
            <stop offset="100%" style={{ stopColor: 'rgba(139,92,246,0)', stopOpacity: 0 }} />
          </radialGradient>
          <radialGradient id="neuronGlow2">
            <stop offset="0%" style={{ stopColor: 'rgba(99,102,241,0.8)', stopOpacity: 1 }} />
            <stop offset="50%" style={{ stopColor: 'rgba(99,102,241,0.3)', stopOpacity: 0.5 }} />
            <stop offset="100%" style={{ stopColor: 'rgba(99,102,241,0)', stopOpacity: 0 }} />
          </radialGradient>
          <linearGradient id="synapseGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: 'rgba(139,92,246,0)', stopOpacity: 0 }} />
            <stop offset="50%" style={{ stopColor: 'rgba(139,92,246,0.4)', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: 'rgba(139,92,246,0)', stopOpacity: 0 }} />
          </linearGradient>
        </defs>

        {/* Synaptic connections */}
        <g className="pulse-1">
          <line x1="5%" y1="15%" x2="18%" y2="8%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="18%" y1="8%" x2="32%" y2="12%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
          <line x1="32%" y1="12%" x2="48%" y2="18%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="48%" y1="18%" x2="65%" y2="10%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
          <line x1="65%" y1="10%" x2="82%" y2="16%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="82%" y1="16%" x2="92%" y2="25%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
        </g>

        <g className="pulse-2">
          <line x1="12%" y1="75%" x2="28%" y2="82%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
          <line x1="28%" y1="82%" x2="46%" y2="78%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="46%" y1="78%" x2="63%" y2="85%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
          <line x1="63%" y1="85%" x2="80%" y2="80%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="80%" y1="80%" x2="94%" y2="88%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
        </g>

        <g className="pulse-1" style={{ animationDelay: '1s' }}>
          <line x1="8%" y1="45%" x2="25%" y2="52%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
          <line x1="25%" y1="52%" x2="45%" y2="48%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="45%" y1="48%" x2="62%" y2="55%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
          <line x1="62%" y1="55%" x2="78%" y2="50%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.6" />
          <line x1="78%" y1="50%" x2="90%" y2="58%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.5" />
        </g>

        <g className="pulse-2" style={{ animationDelay: '2s' }}>
          <line x1="18%" y1="8%" x2="8%" y2="45%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="32%" y1="12%" x2="25%" y2="52%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="48%" y1="18%" x2="45%" y2="48%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="65%" y1="10%" x2="62%" y2="55%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="82%" y1="16%" x2="78%" y2="50%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
        </g>

        <g className="pulse-1" style={{ animationDelay: '3s' }}>
          <line x1="25%" y1="52%" x2="28%" y2="82%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="45%" y1="48%" x2="46%" y2="78%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="62%" y1="55%" x2="63%" y2="85%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
          <line x1="78%" y1="50%" x2="80%" y2="80%" stroke="url(#synapseGradient)" strokeWidth="1" opacity="0.4" />
        </g>

        {/* Neurons */}
        {[
          { x: '5%', y: '15%', delay: '0s', gradient: 'neuronGlow' },
          { x: '18%', y: '8%', delay: '0.5s', gradient: 'neuronGlow2' },
          { x: '32%', y: '12%', delay: '1s', gradient: 'neuronGlow' },
          { x: '48%', y: '18%', delay: '1.5s', gradient: 'neuronGlow2' },
          { x: '65%', y: '10%', delay: '2s', gradient: 'neuronGlow' },
          { x: '82%', y: '16%', delay: '2.5s', gradient: 'neuronGlow2' },
          { x: '92%', y: '25%', delay: '3s', gradient: 'neuronGlow' },
          { x: '8%', y: '45%', delay: '0.8s', gradient: 'neuronGlow2' },
          { x: '25%', y: '52%', delay: '1.3s', gradient: 'neuronGlow' },
          { x: '45%', y: '48%', delay: '1.8s', gradient: 'neuronGlow2' },
          { x: '62%', y: '55%', delay: '2.3s', gradient: 'neuronGlow' },
          { x: '78%', y: '50%', delay: '2.8s', gradient: 'neuronGlow2' },
          { x: '90%', y: '58%', delay: '3.3s', gradient: 'neuronGlow' },
          { x: '12%', y: '75%', delay: '1.2s', gradient: 'neuronGlow' },
          { x: '28%', y: '82%', delay: '1.7s', gradient: 'neuronGlow2' },
          { x: '46%', y: '78%', delay: '2.2s', gradient: 'neuronGlow' },
          { x: '63%', y: '85%', delay: '2.7s', gradient: 'neuronGlow2' },
          { x: '80%', y: '80%', delay: '3.2s', gradient: 'neuronGlow' },
          { x: '94%', y: '88%', delay: '3.7s', gradient: 'neuronGlow2' }
        ].map((neuron, i) => (
          <g key={i}>
            <circle
              cx={neuron.x}
              cy={neuron.y}
              r="8"
              fill={`url(#${neuron.gradient})`}
              className="pulse-1"
              style={{ animationDelay: neuron.delay }}
            />
            <circle
              cx={neuron.x}
              cy={neuron.y}
              r="2"
              fill="rgba(255,255,255,0.9)"
              className="pulse-2"
              style={{ animationDelay: neuron.delay }}
            />
          </g>
        ))}
      </svg>

      <header className="landing-header">
        <div style={{
          width: '36px', height: '36px', borderRadius: '10px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
          boxShadow: '0 4px 20px rgba(139,92,246,0.3)'
        }}>
          <svg style={{ width: '18px', height: '18px', color: 'white' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path d="M12 14l9-5-9-5-9 5 9 5z" />
            <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
          </svg>
        </div>
        <h1>Nebula Learn</h1>
      </header>

      <main className="landing-main">
        {/* Section 1: The Hook */}
        <section className="hero-section">
          <h2>
            <span className="hero-line">Stop collecting knowledge.</span>
            <span className="hero-line">Start building mastery.</span>
          </h2>
          <p className="subtitle">
            Most platforms optimize for your time spent. We optimize for your talent gained.
            Define your goal, and we'll design a high-precision path to get you there.
          </p>
          <button onClick={handleSignIn} className="cta-button">
            Sign in with Google
          </button>
        </section>

        {/* Section 2: The Tailored Process */}
        <section className="features-section">
          <h3>A curriculum designed for a profile of one: Yours.</h3>
          <p className="section-intro">
            We don't believe in generic levels. We believe in specific outcomes.
            Our system listens to where you are and maps exactly what you need to move forward.
          </p>

          <div className="features-grid">
            <div className="feature">
              <h4>1. Build Your Profile</h4>
              <p>
                We analyze your profile and your objective to identify the unique "skill-gaps"
                between you and your goal. We don't just find what you're missing; we find what
                you need to win.
              </p>
            </div>

            <div className="feature">
              <h4>2. Claim Your Tools</h4>
              <p>
                Get a completely tailored roadmap equipped with the mental models and frameworks
                required for your specific mission. Nothing extra, nothing repeated—just pure capability.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: The Problem & Solution */}
        <section className="problem-solution-section">
          <h3>The "Confidence Trap" of modern learning.</h3>
          <p className="section-intro">
            Today's tools make learning feel easy, but easy learning doesn't stick. If you've ever
            finished a course and still felt "unready" to do the work—it's because the system failed you.
          </p>

          <div className="two-col">
            <div className="col">
              <h4>The Problem</h4>
              <p>
                Traditional platforms are built for consumption. They give you the answers too quickly,
                creating "cognitive debt"—you feel confident until it's time to perform.
              </p>
            </div>

            <div className="col">
              <h4>The Solution</h4>
              <p>
                Focusing on real-world objectives and providing the exact tools you need, we turn
                information into instinct. You won't just "know" the subject; you'll own the skill.
              </p>
            </div>
          </div>

          <button onClick={handleSignIn} className="cta-button">
            Start your mastery path
          </button>
        </section>
      </main>

      <footer className="landing-footer">
        <p>© 2025 Nebula. All rights reserved.</p>
      </footer>
    </div>
  );
}
