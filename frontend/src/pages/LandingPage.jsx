import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import './LandingPage.css';

export default function LandingPage() {
  const { user, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleSignIn = async () => {
    try {
      await signInWithGoogle();
    } catch (error) {
      console.error('Sign in error:', error);
    }
  };

  return (
    <div className="landing-page">
      <header className="landing-header">
        <h1>Nebula</h1>
      </header>

      <main className="landing-main">
        {/* Section 1: The Hook */}
        <section className="hero-section">
          <h2>Stop collecting knowledge. Start building mastery.</h2>
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

          <button onClick={handleSignIn} className="cta-button secondary">
            Build my profile
          </button>
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
              <h4>The Mastery Solution</h4>
              <p>
                We optimize for the right kind of effort. By focusing on real-world objectives and
                providing the exact tools you need at the right moment, we turn information into instinct.
                You won't just "know" the subject; you'll own the skill.
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
