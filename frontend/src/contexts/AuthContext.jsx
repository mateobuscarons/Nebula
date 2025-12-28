import { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

const AuthContext = createContext({});

// Dev mode: bypass auth on localhost
const IS_DEV = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const DEV_USER = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'dev@localhost',
  user_metadata: { full_name: 'Local Developer' }
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(IS_DEV ? DEV_USER : null);
  const [loading, setLoading] = useState(!IS_DEV);

  useEffect(() => {
    // Skip auth check in dev mode
    if (IS_DEV) {
      console.log('🔧 Dev mode: Auth bypassed');
      return;
    }

    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin
      }
    });
    if (error) throw error;
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
