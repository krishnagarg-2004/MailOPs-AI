import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { ActionGraphView } from './pages/ActionGraphView';
import { DocumentsView } from './pages/DocumentsView';
import { InboxDashboardView } from './pages/InboxDashboardView';
import { Login } from './pages/Login';
import { SearchRAGView } from './pages/SearchRAGView';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Login Route */}
          <Route path="/login" element={<Login />} />

          {/* Protected Application Workspace */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<InboxDashboardView />} />
            <Route path="documents" element={<DocumentsView />} />
            <Route path="search" element={<SearchRAGView />} />
            <Route path="graph" element={<ActionGraphView />} />
          </Route>

          {/* Fallback Catch-All Route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
