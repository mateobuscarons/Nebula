import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

function SetupPage({ onComplete }) {
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const [userContext, setUserContext] = useState('');
  const [learningGoal, setLearningGoal] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contextFocused, setContextFocused] = useState(false);
  const [objectiveFocused, setObjectiveFocused] = useState(false);
  const [buttonHovered, setButtonHovered] = useState(false);

  const contextRef = useRef(null);
  const objectiveRef = useRef(null);

  const handleLogout = async () => {
    await signOut();
    navigate('/');
  };

  const examples = [
    {
      id: 1,
      title: "Kubernetes Deployment",
      subtitle: "Docker to production K8s",
      baseline: "I am a Senior Backend Developer (Node.js/Go) comfortable with Linux command line. I use Docker daily: I can write multi-stage Dockerfiles, optimize image sizes, and use docker-compose for local development. However, I have zero experience with orchestration. Concepts like 'Pods,' 'Ingress,' or 'Helm charts' are abstract to me.",
      objective: "My company is migrating our monolithic app to microservices on a cloud provider. I need to deploy three dockerized microservices (Frontend, API, Database) into a live Kubernetes cluster with secure communication, public Ingress, and Rolling Updates without downtime."
    },
    {
      id: 2,
      title: "Machine Learning Fundamentals",
      subtitle: "Python basics to ML models",
      baseline: "I'm a data analyst proficient in Python and pandas. I can clean data, create visualizations, and write SQL queries. I understand basic statistics but have never built a machine learning model. Terms like 'gradient descent' and 'neural networks' are unfamiliar.",
      objective: "I want to build a customer churn prediction model for my company. The goal is to take historical customer data, train a classification model, evaluate its performance, and deploy it as an API endpoint our marketing team can query."
    }
  ];

  // Auto-expand textareas
  useEffect(() => {
    const adjustHeight = (element) => {
      if (element) {
        element.style.height = 'auto';
        element.style.height = Math.max(element.scrollHeight, 38) + 'px';
      }
    };
    adjustHeight(contextRef.current);
    adjustHeight(objectiveRef.current);
  }, [userContext, learningGoal]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.setup(learningGoal, userContext);
      onComplete();
      // Navigate to path approval page after successful setup
      navigate('/approve');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadExample = (example) => {
    setUserContext(example.baseline);
    setLearningGoal(example.objective);
  };

  const inputStyle = (focused) => ({
    width: '100%',
    borderRadius: '12px',
    padding: '10px 14px',
    color: 'rgba(255,255,255,0.95)',
    fontSize: '15px',
    outline: 'none',
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    background: focused ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.03)',
    border: focused ? '1.5px solid rgba(139,92,246,0.6)' : '1px solid rgba(255,255,255,0.1)',
    boxShadow: focused ? '0 0 0 4px rgba(139,92,246,0.12), 0 4px 12px rgba(0,0,0,0.1)' : '0 2px 4px rgba(0,0,0,0.05)',
    boxSizing: 'border-box',
    fontFamily: 'inherit',
    lineHeight: 1.6,
    fontWeight: 400,
    resize: 'none',
    overflow: 'hidden',
    minHeight: '38px'
  });

  const labelContainerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '12px',
    gap: '12px'
  };

  const labelTitleWrapperStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  };

  const getLabelTitleStyle = (gradient) => ({
    fontSize: '15px',
    fontWeight: 600,
    backgroundImage: gradient,
    WebkitBackgroundClip: 'text',
    backgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: '-0.02em'
  });

  const labelDescStyle = {
    fontSize: '12px',
    fontWeight: 400,
    color: 'rgba(255,255,255,0.45)',
    letterSpacing: '-0.01em'
  };

  const getIconStyle = (bgGradient, shadowColor) => ({
    width: '18px',
    height: '18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '8px',
    background: bgGradient,
    padding: '4px',
    boxShadow: `0 0 8px ${shadowColor}, 0 2px 6px rgba(0,0,0,0.15)`
  });

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #050508 0%, #0a0a12 50%, #080810 100%)',
      color: '#ffffff',
      overflow: 'hidden',
      position: 'relative',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
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
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.1); }
        }
        @keyframes iconGlow {
          0%, 100% { filter: brightness(1); }
          50% { filter: brightness(1.05); }
        }
        .float-1 { animation: float 12s ease-in-out infinite; }
        .float-2 { animation: float 15s ease-in-out infinite 3s; }
        .float-3 { animation: drift 20s ease-in-out infinite; }
        .float-4 { animation: drift 18s ease-in-out infinite 5s; }
        .pulse-1 { animation: pulse 8s ease-in-out infinite; }
        .pulse-2 { animation: pulse 10s ease-in-out infinite; }
        .icon-glow { animation: iconGlow 3s ease-in-out infinite; }
        input::placeholder, textarea::placeholder { color: rgba(255,255,255,0.3) !important; }
      `}</style>

      {/* Animated mesh grid background */}
      <svg style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
        opacity: 0.08, pointerEvents: 'none', zIndex: 1
      }}>
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(139,92,246,0.4)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Neural network background */}
      <svg style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
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
              r="2.5"
              fill="rgba(167,139,250,0.9)"
              className="pulse-2"
              style={{ animationDelay: neuron.delay }}
            />
          </g>
        ))}
      </svg>

      {/* Firing neurons */}
      {[...Array(8)].map((_, i) => (
        <div
          key={i}
          className="pulse-1"
          style={{
            position: 'absolute',
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
        position: 'absolute', top: '-15%', left: '-5%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.04) 50%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none'
      }} />
      <div className="float-2" style={{
        position: 'absolute', bottom: '-20%', right: '-5%',
        width: '550px', height: '550px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(79,70,229,0.1) 0%, rgba(67,56,202,0.03) 50%, transparent 70%)',
        filter: 'blur(80px)', pointerEvents: 'none'
      }} />
      <div className="float-3" style={{
        position: 'absolute', top: '30%', right: '5%',
        width: '350px', height: '350px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,182,212,0.08) 0%, transparent 60%)',
        filter: 'blur(50px)', pointerEvents: 'none'
      }} />
      <div className="float-4" style={{
        position: 'absolute', bottom: '20%', left: '10%',
        width: '300px', height: '300px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(168,85,247,0.08) 0%, transparent 60%)',
        filter: 'blur(50px)', pointerEvents: 'none'
      }} />

      {/* Vignette overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse at center, transparent 0%, rgba(5,5,8,0.4) 70%, rgba(5,5,8,0.8) 100%)',
        pointerEvents: 'none'
      }} />

      {/* Main content */}
      <div style={{
        position: 'relative', zIndex: 10, width: '100%', maxWidth: '720px',
        margin: '0 auto', padding: '64px 24px'
      }}>
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

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          style={{
            position: 'fixed', top: '28px', right: '32px', zIndex: 50,
            padding: '8px 16px',
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            color: 'rgba(255,255,255,0.7)',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'rgba(255,255,255,0.1)';
            e.target.style.color = 'rgba(255,255,255,0.9)';
            e.target.style.borderColor = 'rgba(255,255,255,0.2)';
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'rgba(255,255,255,0.06)';
            e.target.style.color = 'rgba(255,255,255,0.7)';
            e.target.style.borderColor = 'rgba(255,255,255,0.1)';
          }}
        >
          <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          Logout
        </button>

        {/* Hero heading */}
        <div style={{ textAlign: 'center', marginBottom: '48px', marginTop: '20px' }}>
          <h1 style={{
            fontSize: '56px', fontWeight: 700, letterSpacing: '-0.03em',
            marginBottom: '20px', lineHeight: 1.1
          }}>
            <span style={{
              display: 'inline-block',
              backgroundImage: 'linear-gradient(135deg, #e8e8e8 0%, #b4a0e5 50%, #8b8bda 100%)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>Become the Expert.</span>
          </h1>
          <p style={{
            fontSize: '18px', maxWidth: '480px', margin: '0 auto',
            lineHeight: 1.7,
            letterSpacing: '-0.01em',
            fontWeight: 400
          }}>
            <span style={{ color: 'rgba(255,255,255,0.5)' }}>Turn your objectives into </span>
            <span style={{
              backgroundImage: 'linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 500
            }}>real-world capability</span>
            <span style={{ color: 'rgba(255,255,255,0.5)' }}>.</span>
          </p>
        </div>

        {/* Glass card */}
        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <div style={{ position: 'relative' }}>
            {/* Card glow */}
            <div style={{
              position: 'absolute', inset: '-4px', borderRadius: '20px',
              background: 'linear-gradient(135deg, rgba(139,92,246,0.4) 0%, rgba(99,102,241,0.3) 100%)',
              filter: 'blur(24px)',
              opacity: (contextFocused || objectiveFocused) ? 0.35 : 0,
              transition: 'opacity 0.7s ease', pointerEvents: 'none'
            }} />

            {/* Card */}
            <div style={{
              position: 'relative', borderRadius: '16px', padding: '32px',
              background: 'rgba(255,255,255,0.03)',
              backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
            }}>
              {/* Inner highlight */}
              <div style={{
                position: 'absolute', inset: 0, borderRadius: '16px',
                background: 'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 40%)',
                pointerEvents: 'none'
              }} />

              <div style={{ position: 'relative' }}>
                {/* Baseline/Context input */}
                <div style={{ marginBottom: '18px' }}>
                  <div style={labelContainerStyle}>
                    <div style={labelTitleWrapperStyle}>
                      <div className="icon-glow" style={getIconStyle('linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)', 'rgba(139,92,246,0.25)')}>
                        <svg style={{ width: '14px', height: '14px', color: '#ffffff' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                      <span style={getLabelTitleStyle('linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #6366f1 100%)')}>Background</span>
                    </div>
                    <span style={labelDescStyle}>Your current knowledge and experience</span>
                  </div>
                  <textarea
                    ref={contextRef}
                    value={userContext}
                    onChange={(e) => setUserContext(e.target.value)}
                    placeholder="e.g., I'm a software engineer with 5 years of Python experience..."
                    onFocus={() => setContextFocused(true)}
                    onBlur={() => setContextFocused(false)}
                    disabled={loading}
                    style={inputStyle(contextFocused)}
                  />
                </div>

                {/* Objective input */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={labelContainerStyle}>
                    <div style={labelTitleWrapperStyle}>
                      <div className="icon-glow" style={getIconStyle('linear-gradient(135deg, #06b6d4 0%, #2563eb 100%)', 'rgba(6,182,212,0.25)')}>
                        <svg style={{ width: '14px', height: '14px', color: '#ffffff' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                      </div>
                      <span style={getLabelTitleStyle('linear-gradient(135deg, #22d3ee 0%, #3b82f6 50%, #2563eb 100%)')}>Objective</span>
                    </div>
                    <span style={labelDescStyle}>What you want to accomplish</span>
                  </div>
                  <textarea
                    ref={objectiveRef}
                    value={learningGoal}
                    onChange={(e) => setLearningGoal(e.target.value)}
                    placeholder="e.g., Build and deploy a full-stack web application..."
                    onFocus={() => setObjectiveFocused(true)}
                    onBlur={() => setObjectiveFocused(false)}
                    disabled={loading}
                    required
                    style={inputStyle(objectiveFocused)}
                  />
                </div>

                {/* Error message */}
                {error && (
                  <div style={{
                    marginBottom: '20px', padding: '12px 14px', borderRadius: '10px',
                    background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
                    color: 'rgba(255,150,150,0.9)', fontSize: '13px', fontWeight: 500
                  }}>
                    {error}
                  </div>
                )}

                {/* Generate button */}
                <button
                  type="submit"
                  disabled={loading || !learningGoal}
                  onMouseEnter={() => setButtonHovered(true)}
                  onMouseLeave={() => setButtonHovered(false)}
                  style={{
                    position: 'relative', width: '100%', overflow: 'hidden',
                    borderRadius: '12px', padding: '16px 24px',
                    fontWeight: 500, fontSize: '16px', color: '#ffffff',
                    border: 'none', transition: 'all 0.3s ease',
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
                    transform: buttonHovered && !loading && learningGoal ? 'scale(1.02)' : 'scale(1)',
                    boxShadow: buttonHovered && !loading && learningGoal ? '0 20px 40px -10px rgba(139,92,246,0.5)' : '0 4px 20px rgba(139,92,246,0.25)',
                    opacity: (!learningGoal || loading) ? 0.4 : 1,
                    cursor: (!learningGoal || loading) ? 'not-allowed' : 'pointer'
                  }}
                >
                  <span style={{
                    position: 'relative', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', gap: '12px'
                  }}>
                    {loading ? (
                      <>
                        <svg style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} fill="none" viewBox="0 0 24 24">
                          <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Generating Learning Path...</span>
                      </>
                    ) : (
                      <>
                        <span>Generate Learning Path</span>
                        <svg
                          style={{
                            width: '20px', height: '20px', transition: 'transform 0.3s ease',
                            transform: buttonHovered ? 'translateX(4px)' : 'translateX(0)'
                          }}
                          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </>
                    )}
                  </span>
                </button>
              </div>
            </div>
          </div>
        </form>

        {/* Examples section - moved below */}
        <div style={{ marginTop: '24px' }}>
          <p style={{
            fontSize: '12px', color: 'rgba(255,255,255,0.35)',
            textTransform: 'uppercase', letterSpacing: '0.08em',
            marginBottom: '14px', textAlign: 'center'
          }}>Or try an example</p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            {examples.map((example) => (
              <button
                key={example.id}
                type="button"
                onClick={() => loadExample(example)}
                style={{
                  padding: '12px 20px',
                  borderRadius: '10px',
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(139,92,246,0.3)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  color: 'rgba(255,255,255,0.85)',
                  fontSize: '14px',
                  fontWeight: 500
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.background = 'rgba(139,92,246,0.15)';
                  e.currentTarget.style.borderColor = 'rgba(139,92,246,0.5)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                  e.currentTarget.style.borderColor = 'rgba(139,92,246,0.3)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '2px' }}>
                    {example.title}
                  </div>
                  <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)' }}>
                    {example.subtitle}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SetupPage;
