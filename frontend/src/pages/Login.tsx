import React from 'react';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const { login, isAuthenticated } = useAuth();

  if (isAuthenticated) {
    window.location.href = '/dashboard';
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0f172a', color: '#f8fafc', fontFamily: 'sans-serif' }}>
      <div style={{ width: '100%', maxWidth: '400px', padding: '2rem', backgroundColor: '#1e293b', borderRadius: '0.75rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem', textAlign: 'center', color: '#38bdf8' }}>MailOps AI</h1>
        <p style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '2rem', textAlign: 'center' }}>Enterprise Communication & Work Intelligence Platform</p>
        
        <button
          onClick={() => login()}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.75rem',
            padding: '0.75rem 1rem',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            fontWeight: '600',
            borderRadius: '0.5rem',
            border: 'none',
            cursor: 'pointer',
            fontSize: '1rem',
          }}
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
};
