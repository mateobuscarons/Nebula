import { useState, useEffect, useRef, useId, memo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Editor from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import mermaid from 'mermaid';
import 'katex/dist/katex.min.css';

// Initialize mermaid with dark theme
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#8b5cf6',
    primaryTextColor: '#fff',
    primaryBorderColor: '#6366f1',
    lineColor: '#6366f1',
    secondaryColor: '#1e1b4b',
    tertiaryColor: '#0f0f23',
    background: '#0a0a12',
    mainBkg: '#1a1a2e',
    nodeBorder: '#6366f1',
    clusterBkg: 'rgba(139,92,246,0.1)',
    titleColor: '#fff',
    edgeLabelBackground: '#1a1a2e',
  },
  flowchart: {
    curve: 'basis',
    padding: 20,
  },
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
});

// Memoized markdown components to prevent recreation on every render
const markdownComponents = {
  code({ node, inline, className, children, ...props }) {
    const match = /language-(\w+)/.exec(className || '');
    const language = match ? match[1] : '';
    const isBlock = !inline && (match || String(children).includes('\n'));
    const codeContent = String(children).replace(/\n$/, '');

    // Handle Mermaid diagrams
    if (language === 'mermaid' && isBlock) {
      return <MermaidDiagram chart={codeContent} />;
    }

    if (isBlock) {
      return (
        <SyntaxHighlighter
          style={oneDark}
          language={language || 'text'}
          PreTag="div"
          customStyle={{
            margin: '16px 0',
            borderRadius: '8px',
            fontSize: '13px',
            padding: '16px'
          }}
          {...props}
        >
          {codeContent}
        </SyntaxHighlighter>
      );
    }

    return (
      <code
        style={{
          background: 'rgba(139,92,246,0.15)',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '14px',
          color: '#c4b5fd'
        }}
        {...props}
      >
        {children}
      </code>
    );
  },
  p: ({ children }) => <p style={{ marginBottom: '16px' }}>{children}</p>,
  h1: ({ children }) => <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '16px', color: '#fff' }}>{children}</h1>,
  h2: ({ children }) => <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '12px', color: '#fff' }}>{children}</h2>,
  h3: ({ children }) => <h3 style={{ fontSize: '17px', fontWeight: 600, marginBottom: '10px', color: '#fff' }}>{children}</h3>,
  ul: ({ children }) => <ul style={{ marginBottom: '16px', paddingLeft: '24px' }}>{children}</ul>,
  ol: ({ children }) => <ol style={{ marginBottom: '16px', paddingLeft: '24px' }}>{children}</ol>,
  li: ({ children }) => <li style={{ marginBottom: '8px' }}>{children}</li>,
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: '3px solid #8b5cf6',
      paddingLeft: '16px',
      padding: '12px 16px',
      margin: '20px 0',
      background: 'rgba(139,92,246,0.08)',
      borderRadius: '0 8px 8px 0',
      color: 'rgba(255,255,255,0.85)',
    }}>
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div style={{ overflowX: 'auto', margin: '20px 0' }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '14px',
        background: 'rgba(10,10,18,0.6)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead style={{
      background: 'rgba(139,92,246,0.15)',
      borderBottom: '1px solid rgba(139,92,246,0.3)',
    }}>
      {children}
    </thead>
  ),
  th: ({ children }) => (
    <th style={{
      padding: '12px 16px',
      textAlign: 'left',
      fontWeight: 600,
      color: '#c4b5fd',
      fontSize: '13px',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
    }}>
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td style={{
      padding: '12px 16px',
      borderBottom: '1px solid rgba(255,255,255,0.06)',
      color: 'rgba(255,255,255,0.8)',
    }}>
      {children}
    </td>
  ),
  tr: ({ children }) => (
    <tr style={{
      transition: 'background 0.2s',
    }}>
      {children}
    </tr>
  ),
  strong: ({ children }) => <strong style={{ color: '#fff', fontWeight: 600 }}>{children}</strong>,
  em: ({ children }) => <em style={{ color: 'rgba(255,255,255,0.9)', fontStyle: 'italic' }}>{children}</em>,
  hr: () => <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '24px 0' }} />,
  pre: ({ children }) => <>{children}</>,
};

// Memoized conversation content to prevent re-renders when typing
const ConversationContent = memo(function ConversationContent({ content }) {
  return (
    <div className="markdown-content" style={{
      fontSize: '15px', lineHeight: 1.7, color: 'rgba(255,255,255,0.85)'
    }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={markdownComponents}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});

// Mermaid diagram component - memoized to prevent re-renders when parent state changes
const MermaidDiagram = memo(function MermaidDiagram({ chart }) {
  const containerRef = useRef(null);
  const uniqueId = useId().replace(/:/g, '_');
  const [svg, setSvg] = useState('');
  const [error, setError] = useState(null);

  useEffect(() => {
    const renderChart = async () => {
      if (!chart) return;

      try {
        setError(null);
        const { svg: renderedSvg } = await mermaid.render(`mermaid-${uniqueId}`, chart);
        setSvg(renderedSvg);
      } catch (err) {
        console.error('Mermaid render error:', err);
        setError(err.message);
      }
    };

    renderChart();
  }, [chart, uniqueId]);

  if (error) {
    return (
      <div style={{
        padding: '16px',
        background: 'rgba(239,68,68,0.1)',
        border: '1px solid rgba(239,68,68,0.3)',
        borderRadius: '8px',
        color: '#ef4444',
        fontSize: '13px',
        margin: '16px 0'
      }}>
        <strong>Diagram Error:</strong> {error}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        margin: '20px 0',
        padding: '16px',
        background: 'rgba(139,92,246,0.05)',
        border: '1px solid rgba(139,92,246,0.2)',
        borderRadius: '12px',
        overflow: 'auto',
        display: 'flex',
        justifyContent: 'center',
      }}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
});

// Strip markdown syntax from text for plain text display
const stripMarkdown = (text) => {
  if (!text) return '';
  return text
    // Remove headers (## Heading → Heading)
    .replace(/^#{1,6}\s+/gm, '')
    // Remove bold (**bold** or __bold__ → bold)
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/__(.+?)__/g, '$1')
    // Remove italic (*italic* or _italic_ → italic)
    .replace(/\*(.+?)\*/g, '$1')
    .replace(/_(.+?)_/g, '$1')
    // Remove inline code (`code` → code)
    .replace(/`(.+?)`/g, '$1')
    // Remove links ([link](url) → link)
    .replace(/\[(.+?)\]\(.+?\)/g, '$1')
    // Remove horizontal rules
    .replace(/^[-*_]{3,}\s*$/gm, '')
    // Remove blockquotes (> quote → quote)
    .replace(/^>\s+/gm, '')
    // Remove strikethrough (~~text~~ → text)
    .replace(/~~(.+?)~~/g, '$1');
};

function LessonPage({ onComplete }) {
  const { moduleNumber, challengeNumber } = useParams();
  const navigate = useNavigate();

  const [currentResponse, setCurrentResponse] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [editorType, setEditorType] = useState('text'); // 'code' or 'text'
  const [editorLanguage, setEditorLanguage] = useState('yaml');
  const [lessonStatus, setLessonStatus] = useState({ current_phase: 'LOADING' });
  const [lessonInfo, setLessonInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  // Sources state (from lesson response)
  const [sources, setSources] = useState(null);

  // Ref to prevent double API calls (React StrictMode)
  const lessonStartedRef = useRef(false);

  // Start lesson on mount
  useEffect(() => {
    // Prevent duplicate calls from StrictMode
    if (lessonStartedRef.current) return;
    lessonStartedRef.current = true;

    startLesson();

    // Reset ref on cleanup for route changes
    return () => {
      lessonStartedRef.current = false;
    };
  }, [moduleNumber, challengeNumber]);

  const startLesson = async () => {
    try {
      setLoading(true);
      setError(null);

      const modNum = parseInt(moduleNumber);
      const chalNum = parseInt(challengeNumber);

      // Start lesson (sources included in response)
      const response = await api.startLesson(modNum, chalNum);
      handleResponse(response);

      // Sources are now included in the lesson response
      if (response.sources) {
        setSources(response.sources);
      }

    } catch (err) {
      console.error('Failed to start lesson:', err);
      setError(err.message || 'Failed to start lesson');
    } finally {
      setLoading(false);
    }
  };

  const handleResponse = (response) => {
    setCurrentResponse(response.conversation_content || '');
    setLessonStatus(response.lesson_status || {});
    setLessonInfo(response.lesson_info || null);

    // Handle editor content
    const editor = response.editor_content;
    if (editor && editor.type === 'code') {
      // Only use code editor when explicitly type: "code"
      setEditorContent(editor.content || '');
      setEditorType('code');
      setEditorLanguage(editor.language || 'yaml');
    } else if (editor && editor.type === 'text') {
      // Text type with provided content/template - strip markdown for plain text display
      setEditorContent(stripMarkdown(editor.content || ''));
      setEditorType('text');
      setEditorLanguage('text');
    } else {
      // No editor_content (null) or unknown type - use simple text input
      // This is the default for TEACHING phase where learners type freely
      setEditorContent('');
      setEditorType('text');
      setEditorLanguage('text');
    }
  };

  const handleSubmit = async () => {
    if (!editorContent.trim() || submitting) return;

    try {
      setSubmitting(true);
      setError(null);
      const response = await api.respondToLesson(
        parseInt(moduleNumber),
        parseInt(challengeNumber),
        editorContent
      );
      handleResponse(response);

      // Note: Do NOT clear editor here - handleResponse will handle it based on the response
    } catch (err) {
      console.error('Failed to submit response:', err);
      setError(err.message || 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e) => {
    // Cmd/Ctrl + Enter to submit
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleBackToDashboard = () => {
    // Only refresh/clear cache if lesson was completed (progress changed)
    if (onComplete && lessonStatus.current_phase === 'COMPLETED') {
      onComplete();
    }
    navigate('/dashboard');
  };

  const isCompleted = lessonStatus.current_phase === 'COMPLETED';

  // Phase indicator - 4-phase structure
  const phases = ['ENGAGE', 'DEEPEN', 'APPLY', 'COMPLETED'];
  const phaseLabels = {
    'ENGAGE': 'Warm Up',
    'DEEPEN': 'Understand',
    'APPLY': 'Apply',
    'COMPLETED': 'Done'
  };
  const phaseIcons = {
    'ENGAGE': '👋',
    'DEEPEN': '🧠',
    'APPLY': '🔧',
    'COMPLETED': '✓'
  };
  const currentPhaseIndex = phases.indexOf(lessonStatus.current_phase);

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
          <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.6)' }}>Starting lesson...</p>
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

  if (error && !currentResponse) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #050508 0%, #0a0a12 50%, #080810 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#ffffff',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
      }}>
        <div style={{
          textAlign: 'center', padding: '40px',
          background: 'rgba(239,68,68,0.1)', borderRadius: '16px',
          border: '1px solid rgba(239,68,68,0.3)'
        }}>
          <p style={{ fontSize: '18px', color: '#ef4444', marginBottom: '20px' }}>{error}</p>
          <button
            onClick={handleBackToDashboard}
            style={{
              padding: '12px 24px', borderRadius: '8px',
              background: 'rgba(139,92,246,0.2)', border: '1px solid rgba(139,92,246,0.4)',
              color: '#c4b5fd', fontSize: '14px', fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Back to Dashboard
          </button>
        </div>
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
      {/* Background blobs */}
      <div style={{
        position: 'fixed', top: '-15%', left: '-5%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.12) 0%, rgba(99,102,241,0.04) 50%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none'
      }} />
      <div style={{
        position: 'fixed', bottom: '-20%', right: '-5%',
        width: '550px', height: '550px', borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(79,70,229,0.1) 0%, rgba(67,56,202,0.03) 50%, transparent 70%)',
        filter: 'blur(80px)', pointerEvents: 'none'
      }} />

      {/* Header */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0,
        padding: '20px 32px',
        background: 'rgba(5,5,8,0.8)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        zIndex: 50,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)',
              boxShadow: '0 4px 20px rgba(139,92,246,0.3)'
            }}>
              <svg style={{ width: '16px', height: '16px', color: 'white' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path d="M12 14l9-5-9-5-9 5 9 5z" />
                <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
              </svg>
            </div>
            <span style={{ fontSize: '14px', fontWeight: 600, color: 'rgba(255,255,255,0.85)' }}>Nebula Learn</span>
          </div>

          {/* Lesson info */}
          {lessonInfo && (
            <div style={{ paddingLeft: '16px', borderLeft: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginBottom: '2px' }}>
                Module {lessonInfo.module_number} - Lesson {lessonInfo.challenge_number}
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'rgba(255,255,255,0.9)' }}>
                {lessonInfo.topic}
              </div>
            </div>
          )}
        </div>

        {/* Phase indicator & back button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          {/* Phase progress indicator */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {phases.slice(0, -1).map((phase, idx) => (
              <div key={phase} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px 10px',
                  borderRadius: '12px',
                  background: idx < currentPhaseIndex
                    ? 'rgba(110,231,183,0.15)'
                    : idx === currentPhaseIndex
                      ? 'rgba(139,92,246,0.2)'
                      : 'rgba(255,255,255,0.05)',
                  border: idx === currentPhaseIndex
                    ? '1px solid rgba(139,92,246,0.4)'
                    : '1px solid transparent',
                  transition: 'all 0.3s'
                }}>
                  <div style={{
                    width: '6px', height: '6px', borderRadius: '50%',
                    background: idx < currentPhaseIndex ? '#6ee7b7' :
                      idx === currentPhaseIndex ? '#8b5cf6' : 'rgba(255,255,255,0.3)',
                    boxShadow: idx === currentPhaseIndex ? '0 0 6px rgba(139,92,246,0.6)' : 'none',
                  }} />
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 500,
                    color: idx < currentPhaseIndex
                      ? '#6ee7b7'
                      : idx === currentPhaseIndex
                        ? '#c4b5fd'
                        : 'rgba(255,255,255,0.4)',
                    letterSpacing: '0.02em'
                  }}>
                    {phaseLabels[phase]}
                  </span>
                </div>
                {idx < phases.length - 2 && (
                  <div style={{
                    width: '12px', height: '1px',
                    background: idx < currentPhaseIndex ? '#6ee7b7' : 'rgba(255,255,255,0.15)'
                  }} />
                )}
              </div>
            ))}
          </div>

          <button
            onClick={handleBackToDashboard}
            style={{
              padding: '8px 16px', borderRadius: '8px',
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(255,255,255,0.7)', fontSize: '13px', fontWeight: 500,
              cursor: 'pointer', transition: 'all 0.2s',
              display: 'flex', alignItems: 'center', gap: '6px'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
              e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
            }}
          >
            <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </button>
        </div>
      </div>

      {/* Main content - lesson fills space up to sources */}
      <div style={{
        marginRight: sources?.grounded && (sources.sources?.length > 0 || sources.insight_source) ? '340px' : '60px',
        marginLeft: '160px',
        padding: '100px 0 40px',
        position: 'relative',
        zIndex: 10
      }}>
        {/* Lesson content */}
        <div style={{ width: '100%' }}>
        {/* Completion banner */}
        {isCompleted && (
          <div style={{
            marginBottom: '24px', padding: '24px', borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(110,231,183,0.15) 0%, rgba(16,185,129,0.1) 100%)',
            border: '1px solid rgba(110,231,183,0.3)',
            textAlign: 'center'
          }}>
            <div style={{
              fontSize: '48px', marginBottom: '12px'
            }}>
              🎉
            </div>
            <h2 style={{
              fontSize: '24px', fontWeight: 700, color: '#6ee7b7',
              marginBottom: '8px'
            }}>
              Lesson Completed!
            </h2>
            <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.6)', marginBottom: '20px' }}>
              Great work! You've mastered this lesson.
            </p>
            <button
              onClick={handleBackToDashboard}
              style={{
                padding: '14px 32px', borderRadius: '12px',
                background: 'linear-gradient(135deg, #6ee7b7 0%, #10b981 100%)',
                border: 'none',
                color: '#000', fontSize: '15px', fontWeight: 600,
                cursor: 'pointer', transition: 'all 0.3s',
                boxShadow: '0 4px 20px rgba(110,231,183,0.3)'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 8px 30px rgba(110,231,183,0.4)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 20px rgba(110,231,183,0.3)';
              }}
            >
              Return to Dashboard
            </button>
          </div>
        )}

        {/* Conversation area */}
        <div style={{
          marginBottom: '24px', borderRadius: '16px', overflow: 'hidden',
          background: 'linear-gradient(to bottom, rgba(10,10,18,0.95), rgba(8,8,16,0.98))',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
        }}>
          {/* Conversation header */}
          <div style={{
            padding: '16px 24px',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            display: 'flex', alignItems: 'center', gap: '10px'
          }}>
            <div style={{
              width: '28px', height: '28px', borderRadius: '8px',
              background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <svg style={{ width: '14px', height: '14px', color: 'white' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span style={{ fontSize: '14px', fontWeight: 600, color: 'rgba(255,255,255,0.8)' }}>
              AI Mentor
            </span>
          </div>

          {/* Conversation content */}
          <div style={{ padding: '24px' }}>
            {error && (
              <div style={{
                marginBottom: '16px', padding: '12px 16px', borderRadius: '8px',
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                color: '#ef4444', fontSize: '14px'
              }}>
                {error}
              </div>
            )}
            <ConversationContent content={currentResponse} />
          </div>
        </div>

        {/* Editor area - only show if not completed */}
        {!isCompleted && (
          <div style={{
            borderRadius: '16px', overflow: 'hidden',
            background: 'linear-gradient(to bottom, rgba(10,10,18,0.95), rgba(8,8,16,0.98))',
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
          }}>
            {/* Editor header */}
            <div style={{
              padding: '12px 24px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <svg style={{ width: '16px', height: '16px', color: 'rgba(255,255,255,0.5)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span style={{ fontSize: '13px', fontWeight: 500, color: 'rgba(255,255,255,0.6)' }}>
                  Your Response
                </span>
              </div>
              {editorType === 'code' && (
                <span style={{
                  padding: '4px 10px', borderRadius: '6px',
                  background: 'rgba(139,92,246,0.15)',
                  fontSize: '11px', fontWeight: 600, color: '#c4b5fd',
                  textTransform: 'uppercase'
                }}>
                  {editorLanguage}
                </span>
              )}
            </div>

            {/* Editor content */}
            <div style={{ padding: editorType === 'code' ? '0' : '16px' }}>
              {editorType === 'code' ? (
                <Editor
                  height="300px"
                  language={editorLanguage}
                  value={editorContent}
                  onChange={(value) => setEditorContent(value || '')}
                  onMount={(editor, monaco) => {
                    // Add Cmd/Ctrl + Enter to submit
                    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
                      handleSubmit();
                    });
                  }}
                  theme="vs-dark"
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    scrollBeyondLastLine: false,
                    padding: { top: 16, bottom: 16 },
                    wordWrap: 'on',
                    automaticLayout: true,
                  }}
                />
              ) : (
                <textarea
                  value={editorContent}
                  onChange={(e) => setEditorContent(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    lessonStatus.current_phase === 'ENGAGE'
                      ? "Type your answer..."
                      : lessonStatus.current_phase === 'DEEPEN'
                        ? "Explain your reasoning..."
                        : "Type your solution here..."
                  }
                  style={{
                    width: '100%',
                    minHeight: '200px',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '12px',
                    padding: '16px',
                    color: 'rgba(255,255,255,0.9)',
                    fontSize: '15px',
                    lineHeight: '1.6',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    resize: 'vertical',
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'rgba(139,92,246,0.5)';
                    e.target.style.boxShadow = '0 0 0 3px rgba(139,92,246,0.1)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(255,255,255,0.1)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              )}
            </div>

            {/* Submit button */}
            <div style={{
              padding: '16px 24px',
              borderTop: '1px solid rgba(255,255,255,0.06)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>
                Press <kbd style={{
                  padding: '2px 6px', borderRadius: '4px',
                  background: 'rgba(255,255,255,0.1)',
                  fontSize: '11px'
                }}>⌘</kbd> + <kbd style={{
                  padding: '2px 6px', borderRadius: '4px',
                  background: 'rgba(255,255,255,0.1)',
                  fontSize: '11px'
                }}>Enter</kbd> to submit
              </span>
              <button
                onClick={handleSubmit}
                disabled={!editorContent.trim() || submitting}
                style={{
                  padding: '12px 28px', borderRadius: '10px',
                  background: editorContent.trim() && !submitting
                    ? 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 50%, #6366f1 100%)'
                    : 'rgba(139,92,246,0.2)',
                  border: 'none',
                  color: editorContent.trim() && !submitting ? '#fff' : 'rgba(255,255,255,0.4)',
                  fontSize: '14px', fontWeight: 600,
                  cursor: editorContent.trim() && !submitting ? 'pointer' : 'not-allowed',
                  transition: 'all 0.3s',
                  boxShadow: editorContent.trim() && !submitting ? '0 4px 20px rgba(139,92,246,0.3)' : 'none',
                  display: 'flex', alignItems: 'center', gap: '8px'
                }}
                onMouseOver={(e) => {
                  if (editorContent.trim() && !submitting) {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 8px 30px rgba(139,92,246,0.4)';
                  }
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = editorContent.trim() && !submitting ? '0 4px 20px rgba(139,92,246,0.3)' : 'none';
                }}
              >
                {submitting ? (
                  <>
                    <svg style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} fill="none" viewBox="0 0 24 24">
                      <circle style={{ opacity: 0.25 }} cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path style={{ opacity: 0.75 }} fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Processing...
                  </>
                ) : (
                  <>
                    Submit
                    <svg style={{ width: '16px', height: '16px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
        </div>

        {/* Right: Sources Sidebar - Unified sources block */}
        {sources?.grounded && (sources.sources?.length > 0 || sources.insight_source) && (
          <div style={{
            position: 'fixed',
            right: '24px',
            top: '100px',
            width: '300px',
            zIndex: 40
          }}>
            <div style={{
              borderRadius: '12px',
              background: 'rgba(10,10,18,0.95)',
              border: '1px solid rgba(255,255,255,0.08)',
              overflow: 'hidden',
              padding: '16px'
            }}>
              <div style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'rgba(255,255,255,0.5)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: '12px'
              }}>
                Sources
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {/* Insight source first (if exists, has domain, and not already in resources) */}
                {sources.insight_source && sources.insight_domain &&
                 !sources.sources?.some(s => s.domain === sources.insight_domain) && (
                  <a
                    href={sources.insight_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px',
                      padding: '12px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.03)',
                      textDecoration: 'none',
                      transition: 'background 0.2s'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
                    onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                  >
                    <svg style={{ width: '12px', height: '12px', color: 'rgba(255,255,255,0.4)', flexShrink: 0, marginTop: '2px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: '12px',
                        fontWeight: 500,
                        color: 'rgba(255,255,255,0.75)',
                        marginBottom: '4px'
                      }}>
                        {sources.insight_domain}
                      </div>
                      {sources.insight_description && (
                        <div style={{
                          fontSize: '11px',
                          color: 'rgba(255,255,255,0.45)',
                          lineHeight: 1.4,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}>
                          {sources.insight_description}
                        </div>
                      )}
                    </div>
                  </a>
                )}

                {/* Other sources */}
                {sources.sources?.map((source, idx) => (
                    <a
                      key={idx}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '10px',
                        padding: '12px',
                        borderRadius: '8px',
                        background: 'rgba(255,255,255,0.03)',
                        textDecoration: 'none',
                        transition: 'background 0.2s'
                      }}
                      onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
                      onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                    >
                        <svg style={{ width: '12px', height: '12px', color: 'rgba(255,255,255,0.4)', flexShrink: 0, marginTop: '2px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: '12px',
                            fontWeight: 500,
                            color: 'rgba(255,255,255,0.75)',
                            marginBottom: '4px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {source.domain}
                          </div>
                          {source.description && (
                            <div style={{
                              fontSize: '11px',
                              color: 'rgba(255,255,255,0.45)',
                              lineHeight: 1.4,
                              display: '-webkit-box',
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden'
                            }}>
                              {source.description}
                            </div>
                          )}
                        </div>
                      </a>
                ))}

              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .markdown-content a {
          color: #8b5cf6;
          text-decoration: underline;
        }
        .markdown-content a:hover {
          color: #a78bfa;
        }
        textarea::placeholder {
          color: rgba(255,255,255,0.3);
        }
      `}</style>
    </div>
  );
}

export default LessonPage;
