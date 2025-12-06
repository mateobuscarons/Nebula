import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';

function PathApprovalPage({ sessionState, onComplete, viewOnly = false }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [approveHovered, setApproveHovered] = useState(false);
  const [rejectHovered, setRejectHovered] = useState(false);
  const [adjustHovered, setAdjustHovered] = useState(false);
  const [showAdjustmentBox, setShowAdjustmentBox] = useState(false);
  const [adjustmentFeedback, setAdjustmentFeedback] = useState('');
  const [adjustmentLoading, setAdjustmentLoading] = useState(false);
  const navigate = useNavigate();
  const adjustmentBoxRef = useRef(null);

  // Helper function to format text with backtick code blocks
  const formatWithCode = (text) => {
    if (!text) return null;
    const parts = text.split(/(`[^`]+`)/);
    return parts.map((part, index) => {
      if (part.startsWith('`') && part.endsWith('`')) {
        const code = part.slice(1, -1);
        return (
          <code
            key={index}
            style={{
              display: 'inline',
              padding: '1px 5px',
              borderRadius: '4px',
              background: 'rgba(255,255,255,0.08)',
              color: 'rgba(255,255,255,0.85)',
              fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
              fontSize: '0.9em',
              fontWeight: 400
            }}
          >
            {code}
          </code>
        );
      }
      return part;
    });
  };

  // Helper function to render content as bullet points (handles both arrays and strings)
  const renderContent = (content) => {
    if (!content) return null;

    // If it's an array, render as bullet points
    if (Array.isArray(content)) {
      return (
        <ul style={{
          margin: 0,
          paddingLeft: '20px',
          listStyleType: 'none'
        }}>
          {content.map((item, index) => (
            <li
              key={index}
              style={{
                position: 'relative',
                paddingLeft: '0',
                marginBottom: '8px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px'
              }}
            >
              <span style={{
                display: 'inline-block',
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                marginTop: '8px',
                flexShrink: 0,
                boxShadow: '0 0 8px rgba(139,92,246,0.4)'
              }} />
              <span style={{ flex: 1 }}>
                {formatWithCode(item)}
              </span>
            </li>
          ))}
        </ul>
      );
    }

    // If it's a string, render with code formatting (backward compatibility)
    return formatWithCode(content);
  };

  const learningPath = sessionState?.learning_path;
  // Use 'curriculum' from the learning path format
  const modules = learningPath?.learning_path?.curriculum || [];

  // Expanded debug to see actual structure
  if (modules.length > 0) {
    console.log('DEBUG First Module Structure:', modules[0]);
  }
  console.log('DEBUG PathApprovalPage:', {
    sessionState,
    learningPath,
    modules,
    modulesLength: modules.length
  });
  const handleApprove = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.approvePath(learningPath);
      onComplete();
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleReject = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.reset();
      onComplete();
      navigate('/');
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to reset? This will delete all progress.')) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.reset();
      onComplete();
      navigate('/');
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleRequestAdjustment = () => {
    setShowAdjustmentBox(true);
    setError(null);

    // Scroll to the adjustment box after a short delay to allow it to render
    setTimeout(() => {
      if (adjustmentBoxRef.current) {
        adjustmentBoxRef.current.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }
    }, 100);
  };

  const handleSubmitAdjustment = async () => {
    if (!adjustmentFeedback.trim()) {
      setError('Please provide feedback on what you would like to adjust');
      return;
    }

    setAdjustmentLoading(true);
    setError(null);

    try {
      const result = await api.adjustPath(learningPath, adjustmentFeedback);

      // Update the session state with the new learning path
      sessionState.learning_path = result.learning_path;

      // Reset the adjustment UI
      setShowAdjustmentBox(false);
      setAdjustmentFeedback('');
      setAdjustmentLoading(false);

      // Trigger a re-render by calling onComplete
      onComplete();

    } catch (err) {
      setError(err.message);
      setAdjustmentLoading(false);
    }
  };

  const handleCancelAdjustment = () => {
    setShowAdjustmentBox(false);
    setAdjustmentFeedback('');
    setError(null);
  };


  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #050508 0%, #0a0a12 50%, #080810 100%)',
      color: '#ffffff',
      position: 'relative',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) scale(1); }
          50% { transform: translateY(-20px) scale(1.02); }
        }
        @keyframes drift {
          0%, 100% { transform: translate(0, 0); }
          25% { transform: translate(10px, -10px); }
          50% { transform: translate(-5px, 15px); }
          75% { transform: translate(-15px, -5px); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes orbit {
          0% { transform: translate(0, 0) rotate(0deg); }
          100% { transform: translate(0, 0) rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.1); }
        }
        .float-1 { animation: float 12s ease-in-out infinite; }
        .float-2 { animation: float 15s ease-in-out infinite 3s; }
        .float-3 { animation: drift 20s ease-in-out infinite; }
        .float-4 { animation: drift 18s ease-in-out infinite 5s; }
        .pulse-1 { animation: pulse 8s ease-in-out infinite; }
        .pulse-2 { animation: pulse 10s ease-in-out infinite; }
        .module-card {
          animation: fadeIn 0.6s ease forwards;
        }
        .module-card:nth-child(1) { animation-delay: 0.1s; opacity: 0; }
        .module-card:nth-child(2) { animation-delay: 0.2s; opacity: 0; }
        .module-card:nth-child(3) { animation-delay: 0.3s; opacity: 0; }
        .module-card:nth-child(4) { animation-delay: 0.4s; opacity: 0; }
        .module-card:nth-child(5) { animation-delay: 0.5s; opacity: 0; }
        .module-card:nth-child(n+6) { animation-delay: 0.6s; opacity: 0; }
      `}</style>

      {/* Animated mesh grid background */}
      <svg style={{
        position: 'fixed', inset: 0, width: '100%', height: '100%',
        opacity: 0.08, pointerEvents: 'none', zIndex: 1
      }}>
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(139,92,246,0.4)" strokeWidth="0.5" />
          </pattern>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: 'rgba(139,92,246,0)', stopOpacity: 0 }} />
            <stop offset="50%" style={{ stopColor: 'rgba(139,92,246,0.3)', stopOpacity: 1 }} />
            <stop offset="100%" style={{ stopColor: 'rgba(139,92,246,0)', stopOpacity: 0 }} />
          </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Neural network background */}
      <svg style={{
        position: 'fixed', inset: 0, width: '100%', height: '100%',
        pointerEvents: 'none', zIndex: 1, opacity: 0.75
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

        {/* Vertical connections */}
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

        {/* Neurons (nodes) */}
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
            {/* Glow */}
            <circle
              cx={neuron.x}
              cy={neuron.y}
              r="8"
              fill={`url(#${neuron.gradient})`}
              className="pulse-1"
              style={{ animationDelay: neuron.delay }}
            />
            {/* Core */}
            <circle
              cx={neuron.x}
              cy={neuron.y}
              r="2.5"
              fill="rgba(167,139,250,0.9)"
              className="pulse-2"
              style={{ animationDelay: neuron.delay }}
            />
          </g>
        ))}
      </svg>

      {/* Firing neurons - small fast particles */}
      {[...Array(8)].map((_, i) => (
        <div
          key={i}
          className="pulse-1"
          style={{
            position: 'fixed',
            top: `${20 + (i * 10)}%`,
            left: `${10 + (i * 11)}%`,
            width: '3px',
            height: '3px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(167,139,250,0.9) 0%, transparent 70%)',
            boxShadow: '0 0 12px rgba(167,139,250,0.6)',
            pointerEvents: 'none',
            zIndex: 1,
            animationDelay: `${i * 0.7}s`,
            animation: 'pulse 3s ease-in-out infinite'
          }}
        />
      ))}

      {/* Gradient blobs */}
      <div className="float-1" style={{
        position: 'fixed', top: '-15%', left: '-5%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.04) 50%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none'
      }} />
      <div className="float-2" style={{
        position: 'fixed', bottom: '-20%', right: '-5%',
        width: '550px', height: '550px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(79,70,229,0.1) 0%, rgba(67,56,202,0.03) 50%, transparent 70%)',
        filter: 'blur(80px)', pointerEvents: 'none'
      }} />
      <div className="float-3" style={{
        position: 'fixed', top: '30%', right: '5%',
        width: '350px', height: '350px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 60%)',
        filter: 'blur(50px)', pointerEvents: 'none'
      }} />
      <div className="float-4" style={{
        position: 'fixed', bottom: '20%', left: '10%',
        width: '300px', height: '300px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(168,85,247,0.08) 0%, transparent 60%)',
        filter: 'blur(50px)', pointerEvents: 'none'
      }} />

      {/* Vignette overlay */}
      <div style={{
        position: 'fixed', inset: 0,
        background: 'radial-gradient(ellipse at center, transparent 0%, rgba(5,5,8,0.4) 70%, rgba(5,5,8,0.8) 100%)',
        pointerEvents: 'none'
      }} />

      {/* Logo */}
      <div style={{
        position: 'fixed', top: '28px', left: '32px', zIndex: 50,
        display: 'flex', alignItems: 'center', gap: '10px'
      }}>
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
        <span style={{
          fontSize: '16px', fontWeight: 600, letterSpacing: '-0.02em',
          color: 'rgba(255,255,255,0.85)'
        }}>Nebula Learn</span>
      </div>

      {/* Main content */}
      <div style={{
        maxWidth: '1070px', margin: '0 auto', padding: '100px 24px 120px',
        position: 'relative', zIndex: 10, minHeight: '100vh'
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          {viewOnly && (
            <button
              onClick={() => navigate('/dashboard')}
              style={{
                position: 'absolute', top: '100px', left: '32px',
                background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '8px', padding: '10px 16px', color: 'rgba(255,255,255,0.7)',
                fontSize: '14px', cursor: 'pointer', transition: 'all 0.2s',
                display: 'flex', alignItems: 'center', gap: '6px'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.08)';
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                e.currentTarget.style.color = 'rgba(255,255,255,0.7)';
              }}
            >
              <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Dashboard
            </button>
          )}

          <h1 style={{
            fontSize: '48px', fontWeight: 700, letterSpacing: '-0.03em',
            marginBottom: '16px', lineHeight: 1.1
          }}>
            <span style={{
              display: 'inline-block',
              backgroundImage: 'linear-gradient(135deg, #e8e8e8 0%, #b4a0e5 50%, #8b8bda 100%)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              {viewOnly ? 'Your Learning Path' : 'Review Learning Path'}
            </span>
          </h1>
          <p style={{
            fontSize: '17px', color: 'rgba(255,255,255,0.45)',
            maxWidth: '600px', margin: '0 auto'
          }}>
            {modules.length} modules tailored for your Learning Journey
          </p>
        </div>

        {/* Modules list */}
        <div style={{
          display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '40px',
          position: 'relative', zIndex: 10
        }}>
          {modules.map((module) => (
            <div
              key={module.module_order}
              className="module-card"
              style={{
                position: 'relative', borderRadius: '16px', padding: '28px',
                background: 'linear-gradient(180deg, rgba(20,20,28,1) 0%, rgba(15,15,22,1) 100%)',
                border: '1px solid rgba(255,255,255,0.08)',
                boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                transition: 'all 0.3s ease'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.border = '1px solid rgba(139,92,246,0.3)';
                e.currentTarget.style.boxShadow = '0 12px 40px rgba(139,92,246,0.15)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.border = '1px solid rgba(255,255,255,0.08)';
                e.currentTarget.style.boxShadow = '0 8px 32px rgba(0,0,0,0.4)';
              }}
            >
              {/* Inner highlight */}
              <div style={{
                position: 'absolute', inset: 0, borderRadius: '16px',
                background: 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 40%)',
                pointerEvents: 'none'
              }} />

              <div style={{ position: 'relative' }}>
                {/* Module header */}
                <div style={{ marginBottom: '16px' }}>
                  <span style={{
                    display: 'inline-block', padding: '4px 12px', borderRadius: '20px',
                    background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)',
                    fontSize: '12px', fontWeight: 600, color: '#c4b5fd', marginBottom: '12px'
                  }}>
                    Module {module.module_order}
                  </span>
                  <h3 style={{
                    fontSize: '20px', fontWeight: 600, marginBottom: '8px',
                    color: '#ffffff', letterSpacing: '-0.01em'
                  }}>
                    {module.title}
                  </h3>
                  <p style={{
                    fontSize: '15px', color: 'rgba(255,255,255,0.5)',
                    lineHeight: 1.6
                  }}>
                    {module.competency_goal}
                  </p>
                </div>

                {/* Topics & Hands-on in columns */}
                <div style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px',
                  marginTop: '20px', paddingTop: '20px',
                  borderTop: '1px solid rgba(255,255,255,0.06)'
                }}>
                  <div>
                    <h4 style={{
                      fontSize: '13px', fontWeight: 600, color: 'rgba(255,255,255,0.5)',
                      textTransform: 'uppercase', letterSpacing: '0.05em',
                      marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px'
                    }}>
                      <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                      </svg>
                      Mental Map
                    </h4>
                    <div style={{
                      fontSize: '14px', color: 'rgba(255,255,255,0.7)',
                      lineHeight: 1.8
                    }}>
                      {renderContent(module.mental_map)}
                    </div>
                  </div>
                  <div>
                    <h4 style={{
                      fontSize: '13px', fontWeight: 600, color: 'rgba(255,255,255,0.5)',
                      textTransform: 'uppercase', letterSpacing: '0.05em',
                      marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px'
                    }}>
                      <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                      </svg>
                      Application
                    </h4>
                    <div style={{
                      fontSize: '14px', color: 'rgba(255,255,255,0.7)',
                      lineHeight: 1.8
                    }}>
                      {renderContent(module.application)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Error message */}
        {error && (
          <div style={{
            marginBottom: '24px', padding: '16px 20px', borderRadius: '12px',
            background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
            color: '#fca5a5', fontSize: '14px', textAlign: 'center'
          }}>
            {error}
          </div>
        )}

        {/* Adjustment Feedback Box */}
        {showAdjustmentBox && !viewOnly && (
          <div
            ref={adjustmentBoxRef}
            style={{
              marginBottom: '120px',
              padding: '28px',
              borderRadius: '16px',
              background: 'rgba(255,255,255,0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(139,92,246,0.3)',
              boxShadow: '0 12px 40px rgba(139,92,246,0.15)',
              animation: 'fadeIn 0.4s ease forwards',
              position: 'relative'
            }}>
            {/* Inner highlight */}
            <div style={{
              position: 'absolute', inset: 0, borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(139,92,246,0.08) 0%, transparent 40%)',
              pointerEvents: 'none'
            }} />

            <div style={{ position: 'relative' }}>
              {/* Header */}
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <svg style={{ width: '20px', height: '20px', color: '#a78bfa' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <h3 style={{
                    fontSize: '18px',
                    fontWeight: 600,
                    color: '#ffffff',
                    letterSpacing: '-0.01em',
                    margin: 0
                  }}>
                    Request Adjustments
                  </h3>
                </div>
                <p style={{
                  fontSize: '14px',
                  color: 'rgba(255,255,255,0.5)',
                  margin: 0,
                  lineHeight: 1.6
                }}>
                  Help us tailor your learning journey. Share what topics you'd like to adjust, add, or remove.
                </p>
              </div>

              {/* Textarea */}
              <textarea
                value={adjustmentFeedback}
                onChange={(e) => setAdjustmentFeedback(e.target.value)}
                placeholder="Share your thoughts on how we can better customize this learning path for you..."
                disabled={adjustmentLoading}
                style={{
                  width: '100%',
                  minHeight: '120px',
                  padding: '16px',
                  borderRadius: '12px',
                  background: 'rgba(10,10,15,0.6)',
                  backdropFilter: 'blur(10px)',
                  WebkitBackdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: '#ffffff',
                  fontSize: '15px',
                  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                  lineHeight: 1.6,
                  resize: 'vertical',
                  transition: 'all 0.3s ease',
                  outline: 'none',
                  marginBottom: '16px'
                }}
                onFocus={(e) => {
                  e.target.style.border = '1px solid rgba(139,92,246,0.5)';
                  e.target.style.boxShadow = '0 0 0 3px rgba(139,92,246,0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.border = '1px solid rgba(255,255,255,0.1)';
                  e.target.style.boxShadow = 'none';
                }}
              />

              {/* Action buttons */}
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  onClick={handleCancelAdjustment}
                  disabled={adjustmentLoading}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '10px',
                    fontWeight: 500,
                    fontSize: '14px',
                    border: '1px solid rgba(255,255,255,0.15)',
                    cursor: adjustmentLoading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    background: 'rgba(10,10,15,0.8)',
                    backdropFilter: 'blur(12px)',
                    WebkitBackdropFilter: 'blur(12px)',
                    color: 'rgba(255,255,255,0.7)',
                    opacity: adjustmentLoading ? 0.5 : 1
                  }}
                  onMouseOver={(e) => {
                    if (!adjustmentLoading) {
                      e.target.style.background = 'rgba(15,15,20,0.95)';
                      e.target.style.color = '#ffffff';
                    }
                  }}
                  onMouseOut={(e) => {
                    e.target.style.background = 'rgba(10,10,15,0.8)';
                    e.target.style.color = 'rgba(255,255,255,0.7)';
                  }}
                >
                  Cancel
                </button>

                <button
                  onClick={handleSubmitAdjustment}
                  disabled={adjustmentLoading || !adjustmentFeedback.trim()}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '10px',
                    fontWeight: 500,
                    fontSize: '14px',
                    border: 'none',
                    cursor: (adjustmentLoading || !adjustmentFeedback.trim()) ? 'not-allowed' : 'pointer',
                    transition: 'all 0.3s ease',
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
                    color: '#ffffff',
                    boxShadow: '0 4px 20px rgba(139,92,246,0.3)',
                    opacity: (adjustmentLoading || !adjustmentFeedback.trim()) ? 0.5 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                  onMouseOver={(e) => {
                    if (!adjustmentLoading && adjustmentFeedback.trim()) {
                      e.target.style.transform = 'translateY(-2px)';
                      e.target.style.boxShadow = '0 8px 30px rgba(139,92,246,0.5)';
                    }
                  }}
                  onMouseOut={(e) => {
                    e.target.style.transform = 'translateY(0)';
                    e.target.style.boxShadow = '0 4px 20px rgba(139,92,246,0.3)';
                  }}
                >
                  {adjustmentLoading ? (
                    <>
                      <svg style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} fill="none" viewBox="0 0 24 24">
                        <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Regenerating...
                    </>
                  ) : (
                    <>
                      <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Regenerate Path
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}


        {/* Action buttons */}
        <div style={{
          position: 'fixed', bottom: '32px', left: '50%',
          transform: 'translateX(-50%)',
          maxWidth: '1070px', width: '100%',
          display: 'flex', gap: '16px', justifyContent: 'center',
          zIndex: 100, padding: '0 24px',
          pointerEvents: 'none'
        }}>
          {!viewOnly ? (
            <>
              <button
                onClick={handleApprove}
                disabled={loading}
                onMouseEnter={() => setApproveHovered(true)}
                onMouseLeave={() => setApproveHovered(false)}
                style={{
                  padding: '16px 32px', borderRadius: '12px',
                  fontWeight: 500, fontSize: '16px', color: '#ffffff',
                  border: 'none', cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease', opacity: loading ? 0.5 : 1,
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
                  boxShadow: approveHovered && !loading ? '0 20px 50px rgba(139,92,246,0.6), 0 0 0 1px rgba(139,92,246,0.2)' : '0 8px 30px rgba(139,92,246,0.4), 0 0 0 1px rgba(139,92,246,0.15)',
                  transform: approveHovered && !loading ? 'scale(1.02) translateY(-2px)' : 'scale(1)',
                  display: 'flex', alignItems: 'center', gap: '10px',
                  pointerEvents: 'auto'
                }}
              >
                {loading ? (
                  <>
                    <svg style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} fill="none" viewBox="0 0 24 24">
                      <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Generating Challenges...
                  </>
                ) : (
                  <>
                    <span>Approve & Start Learning</span>
                    <svg
                      style={{
                        width: '20px', height: '20px', transition: 'transform 0.3s ease',
                        transform: approveHovered ? 'translateX(4px)' : 'translateX(0)'
                      }}
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </button>

              <button
                onClick={handleRequestAdjustment}
                disabled={loading || showAdjustmentBox}
                onMouseEnter={() => setAdjustHovered(true)}
                onMouseLeave={() => setAdjustHovered(false)}
                style={{
                  padding: '16px 32px', borderRadius: '12px',
                  fontWeight: 500, fontSize: '16px',
                  border: '1px solid rgba(255,255,255,0.15)',
                  cursor: (loading || showAdjustmentBox) ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease',
                  opacity: (loading || showAdjustmentBox) ? 0.5 : 1,
                  background: adjustHovered && !loading && !showAdjustmentBox
                    ? 'rgba(75,85,99,0.9)'
                    : 'rgba(55,65,81,0.85)',
                  color: '#ffffff',
                  transform: adjustHovered && !loading && !showAdjustmentBox
                    ? 'scale(1.02) translateY(-2px)'
                    : 'scale(1)',
                  boxShadow: adjustHovered && !loading && !showAdjustmentBox
                    ? '0 12px 30px rgba(0,0,0,0.4)'
                    : '0 4px 20px rgba(0,0,0,0.3)',
                  pointerEvents: 'auto',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}
              >
                <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Customize Path
              </button>

              <button
                onClick={handleReject}
                disabled={loading}
                onMouseEnter={() => setRejectHovered(true)}
                onMouseLeave={() => setRejectHovered(false)}
                style={{
                  padding: '16px 32px', borderRadius: '12px',
                  fontWeight: 500, fontSize: '16px',
                  border: '1px solid rgba(255,255,255,0.15)',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  transition: 'all 0.3s ease', opacity: loading ? 0.5 : 1,
                  background: rejectHovered && !loading ? 'rgba(15,15,20,0.95)' : 'rgba(10,10,15,0.9)',
                  backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)',
                  color: rejectHovered && !loading ? '#fca5a5' : 'rgba(255,255,255,0.7)',
                  transform: rejectHovered && !loading ? 'scale(1.02) translateY(-2px)' : 'scale(1)',
                  boxShadow: rejectHovered && !loading ? '0 12px 30px rgba(0,0,0,0.4)' : '0 4px 20px rgba(0,0,0,0.3)',
                  pointerEvents: 'auto'
                }}
              >
                Reject & Start Over
              </button>
            </>
          ) : (
            <button
              onClick={handleReset}
              disabled={loading}
              style={{
                padding: '16px 32px', borderRadius: '12px',
                fontWeight: 500, fontSize: '16px', color: '#fca5a5',
                border: '1px solid rgba(239,68,68,0.5)',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease', opacity: loading ? 0.5 : 1,
                background: 'rgba(239,68,68,0.25)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                boxShadow: '0 4px 20px rgba(239,68,68,0.2)',
                display: 'flex', alignItems: 'center', gap: '10px', margin: '0 auto',
                pointerEvents: 'auto'
              }}
            >
              {loading ? 'Resetting...' : 'Reset System & Start Over'}
            </button>
          )}
        </div>
      </div>
    </div >
  );
}

export default PathApprovalPage;
