import React from 'react';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, login } = useAuth();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: '#0f172a', color: '#e2e8f0' }}>
        <div>Loading authentication state...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    login();
    return null;
  }

  return <>{children}</>;
};
