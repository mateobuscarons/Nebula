import { useState, useRef, useEffect } from 'react';

const styles = `
  @keyframes flowPath {
    0% { stroke-dashoffset: 20; }
    100% { stroke-dashoffset: 0; }
  }
  @keyframes glowPulse {
    0%, 100% { filter: drop-shadow(0 0 4px rgba(139,92,246,0.6)); }
    50% { filter: drop-shadow(0 0 10px rgba(139,92,246,0.9)); }
  }
  @keyframes nodeGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(139,92,246,0.3), inset 0 0 20px rgba(139,92,246,0.1); }
    50% { box-shadow: 0 0 35px rgba(139,92,246,0.5), inset 0 0 25px rgba(139,92,246,0.15); }
  }
  @keyframes destinationGlow {
    0%, 100% { box-shadow: 0 0 30px rgba(251,191,36,0.35), inset 0 0 20px rgba(251,191,36,0.1); }
    50% { box-shadow: 0 0 50px rgba(251,191,36,0.55), inset 0 0 25px rgba(251,191,36,0.15); }
  }
  @keyframes cardShine {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  .pathway-line {
    stroke-dasharray: 8 6;
    animation: flowPath 1.2s linear infinite;
  }
  .pathway-glow {
    animation: glowPulse 2.5s ease-in-out infinite;
  }
  .node-circle {
    animation: nodeGlow 3s ease-in-out infinite;
    transition: all 0.3s ease;
  }
  .node-circle:hover {
    transform: scale(1.1);
  }
  .destination-circle {
    animation: destinationGlow 3s ease-in-out infinite;
  }
  .chapter-card {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .chapter-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 30px rgba(139,92,246,0.15);
  }
  .chapter-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -200%;
    width: 200%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
    animation: cardShine 8s ease-in-out infinite;
  }
`;

function ChapterNode({ chapter, index, isExpanded, onToggle, position }) {
  const chapterNum = chapter.chapter || chapter.module_order || index + 1;
  const title = chapter.title;
  const outcome = chapter.outcome || chapter.competency_goal;
  const concepts = chapter.concepts || chapter.mental_map || [];
  const practice = chapter.practice || chapter.application || [];
  const unlocks = chapter.unlocks;

  const isLeft = position === 'left';

  return (
    <div
      className="chapter-card"
      onClick={onToggle}
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '16px',
        flexDirection: isLeft ? 'row' : 'row-reverse',
        cursor: 'pointer',
        padding: '20px',
        borderRadius: '16px',
        background: 'linear-gradient(135deg, rgba(25,25,35,0.95) 0%, rgba(18,18,26,0.95) 100%)',
        border: isExpanded
          ? '1px solid rgba(139,92,246,0.4)'
          : '1px solid rgba(255,255,255,0.08)',
        boxShadow: isExpanded
          ? '0 12px 40px rgba(0,0,0,0.5), 0 0 20px rgba(139,92,246,0.1)'
          : '0 8px 32px rgba(0,0,0,0.4)',
        overflow: 'hidden',
      }}
    >
      {/* Subtle gradient overlay */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '60%',
        background: 'linear-gradient(180deg, rgba(139,92,246,0.03) 0%, transparent 100%)',
        pointerEvents: 'none',
        borderRadius: '16px 16px 0 0',
      }} />

      {/* Node */}
      <div
        className="node-circle"
        style={{
          flexShrink: 0,
          width: '52px',
          height: '52px',
          borderRadius: '50%',
          background: 'linear-gradient(145deg, rgba(40,40,55,0.98) 0%, rgba(25,25,35,0.98) 100%)',
          border: '2px solid rgba(139,92,246,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          zIndex: 2,
        }}
      >
        <span style={{
          fontSize: '17px',
          fontWeight: 700,
          color: '#fff',
          fontFamily: 'ui-monospace, monospace',
        }}>
          {String(chapterNum).padStart(2, '0')}
        </span>
      </div>

      {/* Content */}
      <div style={{
        flex: 1,
        textAlign: 'left',
        position: 'relative',
        zIndex: 2,
      }}>
        {/* Chapter label */}
        <div style={{
          fontSize: '10px',
          fontWeight: 600,
          color: 'rgba(139,92,246,0.8)',
          textTransform: 'uppercase',
          letterSpacing: '0.12em',
          marginBottom: '6px',
        }}>
          Chapter {chapterNum}
        </div>

        <h3 style={{
          fontSize: '18px',
          fontWeight: 700,
          color: '#ffffff',
          marginBottom: '8px',
          lineHeight: 1.25,
          letterSpacing: '-0.01em',
        }}>
          {title}
        </h3>

        <p style={{
          fontSize: '14px',
          color: 'rgba(255,255,255,0.6)',
          lineHeight: 1.55,
          margin: 0,
        }}>
          {outcome}
        </p>

        {/* Expanded Content */}
        {isExpanded && (
          <div style={{
            marginTop: '16px',
            padding: '16px',
            borderRadius: '12px',
            background: 'rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(139,92,246,0.15)',
            textAlign: 'left',
          }}>
            {concepts.length > 0 && (
              <div style={{ marginBottom: practice.length > 0 ? '14px' : 0 }}>
                <div style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: 'rgba(139,92,246,0.9)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  marginBottom: '10px'
                }}>
                  What you'll learn
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {concepts.map((c, i) => (
                    <span key={i} style={{
                      padding: '5px 12px',
                      borderRadius: '20px',
                      background: 'rgba(139,92,246,0.15)',
                      border: '1px solid rgba(139,92,246,0.25)',
                      fontSize: '12px',
                      fontWeight: 500,
                      color: '#d4c4f7'
                    }}>
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {practice.length > 0 && (
              <div>
                <div style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  color: 'rgba(139,92,246,0.9)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  marginBottom: '10px'
                }}>
                  What you'll practice
                </div>
                <ul style={{
                  margin: 0,
                  paddingLeft: '16px',
                  fontSize: '13px',
                  color: 'rgba(255,255,255,0.7)',
                  lineHeight: 1.6
                }}>
                  {practice.map((p, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>{p}</li>
                  ))}
                </ul>
              </div>
            )}

            {unlocks && (
              <div style={{
                marginTop: '14px',
                paddingTop: '14px',
                borderTop: '1px solid rgba(255,255,255,0.06)',
                fontSize: '12px',
                color: 'rgba(255,255,255,0.5)'
              }}>
                <span style={{ color: '#a78bfa', fontWeight: 600 }}>Unlocks →</span> {unlocks}
              </div>
            )}
          </div>
        )}

        {/* Click hint */}
        {!isExpanded && (
          <div style={{
            marginTop: '10px',
            fontSize: '11px',
            color: 'rgba(139,92,246,0.6)',
            fontWeight: 500,
          }}>
            Click to see details
          </div>
        )}
      </div>
    </div>
  );
}

export default function NeuralPathway({ learningPath }) {
  const [expandedChapter, setExpandedChapter] = useState(null);
  const [nodePositions, setNodePositions] = useState([]);
  const containerRef = useRef(null);
  const nodeRefs = useRef([]);
  const destinationRef = useRef(null);

  const journey = learningPath?.journey || {};
  const chapters = learningPath?.chapters || learningPath?.curriculum || [];
  const title = journey.title || '';
  const destination = journey.destination || '';

  const toggleChapter = (chapterNum) => {
    setExpandedChapter(expandedChapter === chapterNum ? null : chapterNum);
  };

  const getPosition = (index) => index % 2 === 0 ? 'left' : 'right';

  // Calculate node positions for SVG path
  useEffect(() => {
    const updatePositions = () => {
      if (!containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();

      // Get chapter node positions
      const positions = nodeRefs.current.map((ref, index) => {
        if (!ref) return null;
        const nodeEl = ref.querySelector('.node-circle');
        if (!nodeEl) return null;
        const rect = nodeEl.getBoundingClientRect();
        return {
          x: rect.left - containerRect.left + rect.width / 2,
          y: rect.top - containerRect.top + rect.height / 2,
        };
      }).filter(Boolean);

      // Add destination position
      if (destinationRef.current) {
        const destEl = destinationRef.current.querySelector('.destination-circle');
        if (destEl) {
          const rect = destEl.getBoundingClientRect();
          positions.push({
            x: rect.left - containerRect.left + rect.width / 2,
            y: rect.top - containerRect.top + rect.height / 2,
          });
        }
      }

      setNodePositions(positions);
    };

    // Multiple updates to catch layout changes
    updatePositions();
    const t1 = setTimeout(updatePositions, 50);
    const t2 = setTimeout(updatePositions, 150);
    const t3 = setTimeout(updatePositions, 300);

    window.addEventListener('resize', updatePositions);

    return () => {
      window.removeEventListener('resize', updatePositions);
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [chapters.length, expandedChapter]);

  // Generate SVG path through all nodes
  const generatePath = () => {
    if (nodePositions.length < 2) return '';

    let path = `M ${nodePositions[0].x} ${nodePositions[0].y}`;

    for (let i = 1; i < nodePositions.length; i++) {
      const prev = nodePositions[i - 1];
      const curr = nodePositions[i];

      // Control points for smooth S-curve
      const midY = (prev.y + curr.y) / 2;

      path += ` C ${prev.x} ${midY}, ${curr.x} ${midY}, ${curr.x} ${curr.y}`;
    }

    return path;
  };

  return (
    <>
      <style>{styles}</style>

      <div style={{ padding: '0 20px', maxWidth: '950px', margin: '0 auto' }}>
        {/* Journey Header */}
        {(destination || chapters.length > 0) && (
          <div style={{ textAlign: 'center', marginBottom: '44px' }}>
            {destination && (
              <div style={{
                margin: '20px auto 26px',
                maxWidth: '720px',
                position: 'relative',
              }}>
                {/* Opening quote mark */}
                <span style={{
                  position: 'absolute',
                  top: '-4px',
                  left: '0px',
                  fontSize: '42px',
                  fontFamily: 'Georgia, "Times New Roman", serif',
                  color: 'rgba(139,92,246,0.25)',
                  lineHeight: 1,
                  userSelect: 'none',
                }}>"</span>
                <p style={{
                  fontSize: '16px',
                  color: 'rgba(255,255,255,0.75)',
                  lineHeight: 1.75,
                  margin: 0,
                  fontWeight: 300,
                  letterSpacing: '0.01em',
                  paddingLeft: '32px',
                  paddingRight: '16px',
                  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                }}>
                  {destination}
                </p>
              </div>
            )}

            {/* Chapter badge */}
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '20px',
              background: 'rgba(139,92,246,0.08)',
              border: '1px solid rgba(139,92,246,0.15)',
            }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="rgba(139,92,246,0.65)" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <span style={{ fontSize: '12px', color: 'rgba(139,92,246,0.75)', fontWeight: 600 }}>
                {chapters.length} Chapters
              </span>
            </div>
          </div>
        )}

        {/* Pathway Container */}
        <div ref={containerRef} style={{ position: 'relative' }}>
          {/* SVG Path */}
          <svg
            className="pathway-glow"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              pointerEvents: 'none',
              zIndex: 0,
              overflow: 'visible',
            }}
          >
            <defs>
              <linearGradient id="pathGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="75%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#fbbf24" />
              </linearGradient>
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {/* Background glow line */}
            <path
              d={generatePath()}
              fill="none"
              stroke="rgba(139,92,246,0.12)"
              strokeWidth="12"
              strokeLinecap="round"
            />

            {/* Main animated line */}
            <path
              className="pathway-line"
              d={generatePath()}
              fill="none"
              stroke="url(#pathGradient)"
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#glow)"
            />
          </svg>

          {/* Chapter nodes */}
          <div style={{ position: 'relative', zIndex: 1 }}>
            {chapters.map((chapter, index) => {
              const chapterNum = chapter.chapter || chapter.module_order || index + 1;
              const position = getPosition(index);

              return (
                <div
                  key={chapterNum}
                  ref={el => nodeRefs.current[index] = el}
                  style={{
                    display: 'flex',
                    justifyContent: position === 'left' ? 'flex-start' : 'flex-end',
                    marginBottom: '60px',
                  }}
                >
                  <div style={{ width: '100%', maxWidth: '440px' }}>
                    <ChapterNode
                      chapter={chapter}
                      index={index}
                      isExpanded={expandedChapter === chapterNum}
                      onToggle={() => toggleChapter(chapterNum)}
                      position={position}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Destination */}
          <div
            ref={destinationRef}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              paddingTop: '20px',
              paddingBottom: '30px',
            }}
          >
            <div
              className="destination-circle"
              style={{
                width: '72px',
                height: '72px',
                borderRadius: '50%',
                background: 'linear-gradient(145deg, rgba(60,55,35,0.98) 0%, rgba(35,32,20,0.98) 100%)',
                border: '2.5px solid rgba(251,191,36,0.65)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="rgba(251,191,36,1)" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="6" />
                <circle cx="12" cy="12" r="2" fill="rgba(251,191,36,1)" />
              </svg>
            </div>
            <div style={{ marginTop: '14px', textAlign: 'center' }}>
              <div style={{
                fontSize: '12px',
                fontWeight: 700,
                color: 'rgba(251,191,36,0.9)',
                textTransform: 'uppercase',
                letterSpacing: '0.15em',
              }}>
                Destination
              </div>
              {destination && (
                <p style={{
                  marginTop: '8px',
                  fontSize: '13px',
                  color: 'rgba(255,255,255,0.5)',
                  maxWidth: '280px',
                  lineHeight: 1.5,
                }}>
                  {destination}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
