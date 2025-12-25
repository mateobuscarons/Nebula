import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

function Dashboard({ sessionState, onRefresh, cachedData, setCachedData }) {
  const [progress, setProgress] = useState(cachedData?.progress || null);
  const [challengesMetadata, setChallengesMetadata] = useState(cachedData?.metadata || {});
  const [loading, setLoading] = useState(!cachedData);
  const [hoveredChallenge, setHoveredChallenge] = useState(null);
  const [expandedChallenge, setExpandedChallenge] = useState(null);
  const [expandedModule, setExpandedModule] = useState(null);
  const navigate = useNavigate();
  const { signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    navigate('/');
  };

  useEffect(() => {
    // Only load if no cached data
    if (!cachedData) {
      loadProgress();
    }
  }, []);

  const loadProgress = async () => {
    try {
      const [progressData, metadataData] = await Promise.all([
        api.getProgress(),
        api.getChallengesMetadata()
      ]);
      setProgress(progressData);
      setChallengesMetadata(metadataData);
      // Cache the data in parent
      setCachedData?.({ progress: progressData, metadata: metadataData });
    } catch (error) {
      console.error('Failed to load progress:', error);
    } finally {
      setLoading(false);
    }
  };


  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #050508 0%, #0a0a12 50%, #080810 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#ffffff',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <svg style={{ width: '48px', height: '48px', animation: 'spin 1s linear infinite', marginBottom: '20px' }} fill="none" viewBox="0 0 24 24">
            <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.6)' }}>Loading your progress...</p>
        </div>
        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #050508 0%, #0a0a12 50%, #080810 100%)',
      color: '#ffffff',
      position: 'relative',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .challenge-card {
          animation: fadeIn 0.5s ease forwards;
        }
      `}</style>

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

      {/* Vignette */}
      <div style={{
        position: 'fixed', inset: 0,
        background: 'radial-gradient(ellipse at center, transparent 0%, rgba(5,5,8,0.4) 70%, rgba(5,5,8,0.8) 100%)',
        pointerEvents: 'none'
      }} />

      {/* Gradient blobs around borders */}
      <div style={{
        position: 'fixed', top: '-15%', left: '-10%',
        width: '600px', height: '600px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, rgba(139,92,246,0.06) 40%, transparent 70%)',
        filter: 'blur(80px)', pointerEvents: 'none'
      }} />
      <div style={{
        position: 'fixed', top: '-10%', right: '-15%',
        width: '550px', height: '550px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.10) 0%, rgba(79,70,229,0.05) 40%, transparent 70%)',
        filter: 'blur(70px)', pointerEvents: 'none'
      }} />
      <div style={{
        position: 'fixed', bottom: '-20%', left: '-5%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(124,58,237,0.11) 0%, rgba(99,102,241,0.05) 40%, transparent 70%)',
        filter: 'blur(75px)', pointerEvents: 'none'
      }} />
      <div style={{
        position: 'fixed', bottom: '-15%', right: '-10%',
        width: '650px', height: '650px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(79,70,229,0.10) 0%, rgba(67,56,202,0.05) 40%, transparent 70%)',
        filter: 'blur(85px)', pointerEvents: 'none'
      }} />

      <div style={{
        position: 'fixed', top: '30%', right: '-12%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)',
        filter: 'blur(70px)', pointerEvents: 'none'
      }} />

      {/* Logo */}
      <div style={{
        position: 'absolute', top: '28px', left: '32px', zIndex: 50,
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
          position: 'absolute', top: '28px', right: '32px', zIndex: 50,
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

      {/* Main content */}
      <div style={{
        maxWidth: '1200px', margin: '0 auto', padding: '100px 24px 80px',
        position: 'relative', zIndex: 10
      }}>
        {/* Header with progress */}
        <div style={{ marginBottom: '48px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <div>
              <h1 style={{
                fontSize: '48px', fontWeight: 700, letterSpacing: '-0.03em',
                marginBottom: '8px', lineHeight: 1.1
              }}>
                <span style={{
                  display: 'inline-block',
                  backgroundImage: 'linear-gradient(135deg, #e8e8e8 0%, #b4a0e5 50%, #8b8bda 100%)',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>Your Journey</span>
              </h1>
              <p style={{
                fontSize: '17px', color: 'rgba(255,255,255,0.45)'
              }}>Track your progress and master new skills</p>
            </div>

            <button
              onClick={() => navigate('/path/view')}
              style={{
                padding: '12px 24px', borderRadius: '12px',
                background: 'linear-gradient(135deg, rgba(139,92,246,0.15) 0%, rgba(99,102,241,0.15) 100%)',
                border: '1px solid rgba(139,92,246,0.3)',
                color: '#c4b5fd',
                fontSize: '14px', fontWeight: 600,
                cursor: 'pointer', transition: 'all 0.3s',
                display: 'flex', alignItems: 'center', gap: '8px',
                boxShadow: '0 4px 12px rgba(139,92,246,0.1)'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(139,92,246,0.25) 0%, rgba(99,102,241,0.25) 100%)';
                e.currentTarget.style.borderColor = 'rgba(139,92,246,0.5)';
                e.currentTarget.style.boxShadow = '0 8px 20px rgba(139,92,246,0.25)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(139,92,246,0.15) 0%, rgba(99,102,241,0.15) 100%)';
                e.currentTarget.style.borderColor = 'rgba(139,92,246,0.3)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(139,92,246,0.1)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <svg style={{ width: '18px', height: '18px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              View Learning Path
            </button>
          </div>

          {/* Progress bar glass card */}
          <div style={{ position: 'relative' }}>
            <div style={{
              position: 'absolute', inset: '-2px', borderRadius: '16px',
              background: 'linear-gradient(135deg, rgba(139,92,246,0.3) 0%, rgba(99,102,241,0.2) 100%)',
              filter: 'blur(20px)', opacity: 0.4, pointerEvents: 'none'
            }} />
            <div style={{
              position: 'relative', borderRadius: '14px', padding: '24px',
              background: 'linear-gradient(to bottom, rgba(10,10,18,0.95), rgba(8,8,16,0.98)), rgba(255,255,255,0.04)',
              backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.08)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
            }}>
              <div style={{
                position: 'absolute', inset: 0, borderRadius: '14px',
                background: 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 40%)',
                pointerEvents: 'none'
              }} />
              <div style={{ position: 'relative' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 600, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Overall Progress</span>
                  <span style={{ fontSize: '20px', fontWeight: 700, color: '#a78bfa' }}>
                    {Math.round(progress?.completion_percentage || 0)}%
                  </span>
                </div>
                <div style={{
                  position: 'relative', height: '12px', borderRadius: '8px',
                  background: 'rgba(255,255,255,0.05)',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${progress?.completion_percentage || 0}%`,
                    background: 'linear-gradient(90deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
                    borderRadius: '8px',
                    transition: 'width 1s ease',
                    boxShadow: '0 0 20px rgba(139,92,246,0.5)'
                  }} />
                </div>
                <p style={{ marginTop: '12px', fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}>
                  {progress?.total_completed || 0} of {progress?.total_challenges || 0} challenges completed
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Modules grid */}
        <div style={{ display: 'grid', gap: '24px' }}>
          {progress?.modules?.map((module, moduleIdx) => {
            const moduleMetadata = challengesMetadata[module.module_number] || {};
            const moduleChallenges = moduleMetadata.challenges || [];

            return (
              <div
                key={module.module_number}
                className="challenge-card"
                style={{
                  position: 'relative', borderRadius: '16px', padding: '28px',
                  background: 'linear-gradient(to bottom, rgba(10,10,18,0.95), rgba(8,8,16,0.98)), rgba(255,255,255,0.04)',
                  backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                  transition: 'all 0.3s ease',
                  animationDelay: `${moduleIdx * 0.1}s`,
                  opacity: 0
                }}
              >
                <div style={{
                  position: 'absolute', inset: 0, borderRadius: '16px',
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 40%)',
                  pointerEvents: 'none'
                }} />

                <div style={{ position: 'relative' }}>
                  {/* Module header */}
                  <div style={{ marginBottom: '24px', paddingBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                          <span style={{
                            padding: '4px 12px', borderRadius: '20px',
                            background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.3)',
                            fontSize: '12px', fontWeight: 600, color: '#c4b5fd'
                          }}>
                            Module {module.module_number}
                          </span>
                          <h3 style={{
                            fontSize: '20px', fontWeight: 600, color: '#ffffff',
                            letterSpacing: '-0.01em', margin: 0
                          }}>
                            {moduleMetadata.module_title || `Module ${module.module_number}`}
                          </h3>
                        </div>
                        {moduleMetadata.module_description && (
                          <p style={{
                            fontSize: '14px', color: 'rgba(255,255,255,0.5)',
                            margin: '8px 0', lineHeight: 1.5
                          }}>
                            {moduleMetadata.module_description}
                          </p>
                        )}

                        {/* Expandable buttons side by side */}
                        {(moduleMetadata.module_context_bridge || (moduleMetadata.acquired_competencies && moduleMetadata.acquired_competencies.length > 0)) && (
                          <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                            {moduleMetadata.module_context_bridge && (
                              <button
                                onClick={() => setExpandedModule(expandedModule === `${module.module_number}-bridge` ? null : `${module.module_number}-bridge`)}
                                style={{
                                  flex: 1, padding: '8px 12px', borderRadius: '6px',
                                  background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)',
                                  color: '#818cf8', fontSize: '12px', fontWeight: 600,
                                  cursor: 'pointer', transition: 'all 0.2s',
                                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                                }}
                              >
                                <svg style={{ width: '14px', height: '14px', transition: 'transform 0.2s', transform: expandedModule === `${module.module_number}-bridge` ? 'rotate(180deg)' : 'rotate(0deg)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                                What You Already Know
                              </button>
                            )}
                            {moduleMetadata.acquired_competencies && moduleMetadata.acquired_competencies.length > 0 && (
                              <button
                                onClick={() => setExpandedModule(expandedModule === `${module.module_number}-competencies` ? null : `${module.module_number}-competencies`)}
                                style={{
                                  flex: 1, padding: '8px 12px', borderRadius: '6px',
                                  background: 'rgba(110,231,183,0.1)', border: '1px solid rgba(110,231,183,0.2)',
                                  color: '#6ee7b7', fontSize: '12px', fontWeight: 600,
                                  cursor: 'pointer', transition: 'all 0.2s',
                                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
                                }}
                              >
                                <svg style={{ width: '14px', height: '14px', transition: 'transform 0.2s', transform: expandedModule === `${module.module_number}-competencies` ? 'rotate(180deg)' : 'rotate(0deg)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                                What You'll Be Able To Do
                              </button>
                            )}
                          </div>
                        )}

                        {/* Context Bridge - Expanded */}
                        {expandedModule === `${module.module_number}-bridge` && moduleMetadata.module_context_bridge && (
                          <div style={{
                            marginTop: '12px', padding: '16px', borderRadius: '8px',
                            background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                              <svg style={{ width: '16px', height: '16px', color: '#818cf8' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                              </svg>
                              <span style={{ fontSize: '12px', fontWeight: 600, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Building On Your Knowledge
                              </span>
                            </div>
                            <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)', margin: 0, lineHeight: 1.4 }}>
                              {moduleMetadata.module_context_bridge}
                            </p>
                          </div>
                        )}

                        {/* Acquired Competencies - Expanded */}
                        {expandedModule === `${module.module_number}-competencies` && moduleMetadata.acquired_competencies && (
                          <div style={{
                            marginTop: '12px', padding: '16px', borderRadius: '8px',
                            background: 'rgba(110,231,183,0.08)', border: '1px solid rgba(110,231,183,0.15)'
                          }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                              <svg style={{ width: '16px', height: '16px', color: '#6ee7b7' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              <span style={{ fontSize: '12px', fontWeight: 600, color: '#6ee7b7', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                What You'll Master
                              </span>
                            </div>
                            <ul style={{ margin: 0, padding: '0 0 0 20px', listStyle: 'disc' }}>
                              {moduleMetadata.acquired_competencies.map((comp, idx) => (
                                <li key={idx} style={{ fontSize: '13px', color: 'rgba(255,255,255,0.7)', marginBottom: '4px', lineHeight: 1.4 }}>
                                  {comp}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      <span style={{
                        fontSize: '14px', fontWeight: 600, marginLeft: '16px',
                        color: module.completed === module.total ? '#6ee7b7' : '#a78bfa'
                      }}>
                        {module.completed} / {module.total}
                      </span>
                    </div>
                  </div>

                  {/* Challenges grid */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                    gap: '16px'
                  }}>
                    {Array.from({ length: module.total }, (_, i) => {
                      const challengeNum = i + 1;
                      const challengeDetail = module.challenge_details?.[challengeNum];
                      const status = challengeDetail?.status || 'not_started';
                      const isCompleted = status === 'completed';
                      const isInProgress = status === 'in_progress';
                      const challengeInfo = moduleChallenges.find(c => c.challenge_number === challengeNum);
                      const challengeKey = `${module.module_number}-${challengeNum}`;
                      const isExpanded = expandedChallenge === challengeKey;
                      const urac = challengeInfo?.urac_blueprint || {};

                      // Sequential access logic: first challenge always accessible,
                      // subsequent challenges require previous to be completed
                      const prevChallengeDetail = challengeNum > 1 ? module.challenge_details?.[challengeNum - 1] : null;
                      const prevCompleted = challengeNum === 1 || prevChallengeDetail?.status === 'completed';
                      const isAccessible = prevCompleted && !isCompleted;
                      const isLocked = !prevCompleted && !isCompleted && !isInProgress;

                      return (
                        <div
                          key={challengeNum}
                          onMouseEnter={() => setHoveredChallenge(challengeKey)}
                          onMouseLeave={() => setHoveredChallenge(null)}
                          style={{
                            padding: '18px', borderRadius: '12px',
                            background: hoveredChallenge === challengeKey && !isLocked ?
                              'rgba(255,255,255,0.08)' : isLocked ? 'rgba(255,255,255,0.01)' : 'rgba(255,255,255,0.03)',
                            border: isCompleted ?
                              '1px solid rgba(110,231,183,0.3)' :
                              isInProgress ? '1px solid rgba(251,191,36,0.3)' :
                              isLocked ? '1px solid rgba(255,255,255,0.04)' : '1px solid rgba(255,255,255,0.06)',
                            cursor: isLocked ? 'not-allowed' : 'pointer',
                            transition: 'all 0.3s ease',
                            transform: hoveredChallenge === challengeKey && !isLocked ?
                              'translateY(-2px)' : 'translateY(0)',
                            boxShadow: hoveredChallenge === challengeKey && !isLocked ?
                              '0 8px 24px rgba(139,92,246,0.2)' : 'none',
                            opacity: isLocked ? 0.5 : 1
                          }}
                          onClick={() => !isLocked && setExpandedChallenge(isExpanded ? null : challengeKey)}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: isExpanded ? '16px' : '0' }}>
                            <div style={{
                              width: '36px', height: '36px', borderRadius: '8px', flexShrink: 0,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              background: isCompleted ?
                                'linear-gradient(135deg, #6ee7b7 0%, #10b981 100%)' :
                                isInProgress ?
                                  'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)' :
                                  isLocked ? 'rgba(100,100,100,0.15)' : 'rgba(139,92,246,0.15)',
                              boxShadow: isCompleted ? '0 0 12px rgba(110,231,183,0.4)' :
                                isInProgress ? '0 0 12px rgba(251,191,36,0.4)' : 'none',
                              fontSize: '14px', fontWeight: 600,
                              color: (isCompleted || isInProgress) ? '#ffffff' : isLocked ? 'rgba(255,255,255,0.3)' : '#a78bfa'
                            }}>
                              {isCompleted ? '✓' : isInProgress ? '◐' : isLocked ? (
                                <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                              ) : challengeNum}
                            </div>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{
                                fontSize: '15px', fontWeight: 600,
                                color: 'rgba(255,255,255,0.9)',
                                lineHeight: 1.3, marginBottom: '4px'
                              }}>
                                {challengeInfo?.topic || `Challenge ${challengeNum}`}
                              </div>
                              <div style={{
                                fontSize: '12px',
                                color: isCompleted ? '#6ee7b7' : isInProgress ? '#fbbf24' : isLocked ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.4)'
                              }}>
                                {isCompleted ? 'Completed' : isInProgress ? 'In Progress' : isLocked ? 'Locked' : 'Not Started'}
                              </div>
                            </div>
                            <svg style={{
                              width: '16px', height: '16px', color: 'rgba(255,255,255,0.4)',
                              transition: 'transform 0.2s', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                              flexShrink: 0
                            }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>

                          {/* Start/Continue button - Expanded */}
                          {isExpanded && (
                            <div style={{ paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                              {!isCompleted && !isLocked && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/lesson/${module.module_number}/${challengeNum}`);
                                  }}
                                  style={{
                                    width: '100%', padding: '12px 20px',
                                    borderRadius: '8px',
                                    background: isInProgress
                                      ? 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)'
                                      : 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
                                    border: 'none',
                                    color: isInProgress ? '#000' : '#fff',
                                    fontSize: '14px', fontWeight: 600,
                                    cursor: 'pointer', transition: 'all 0.3s',
                                    boxShadow: isInProgress
                                      ? '0 4px 15px rgba(251,191,36,0.3)'
                                      : '0 4px 15px rgba(139,92,246,0.3)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                                  }}
                                  onMouseOver={(e) => {
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.boxShadow = isInProgress
                                      ? '0 8px 25px rgba(251,191,36,0.4)'
                                      : '0 8px 25px rgba(139,92,246,0.4)';
                                  }}
                                  onMouseOut={(e) => {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = isInProgress
                                      ? '0 4px 15px rgba(251,191,36,0.3)'
                                      : '0 4px 15px rgba(139,92,246,0.3)';
                                  }}
                                >
                                  {isInProgress ? (
                                    <>
                                      <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      Continue Lesson
                                    </>
                                  ) : (
                                    <>
                                      <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      Start Lesson
                                    </>
                                  )}
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div >
  );
}

export default Dashboard;
