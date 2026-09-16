import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Layout, LoginPage } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ClaimsPage } from './pages/ClaimsPage';
import { WorkQueuesPage } from './pages/WorkQueuesPage';
import { DenialsPage } from './pages/DenialsPage';
import { PaymentsPage } from './pages/PaymentsPage';
import { AgentsPage } from './pages/AgentsPage';
import { AssistantPage } from './pages/AssistantPage';
import { UsersPage } from './pages/UsersPage';

function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
  const { user, isLoading, hasRole } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !hasRole(allowedRoles as any)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="claims" element={<ClaimsPage />} />
        <Route path="work-queues" element={<WorkQueuesPage />} />
        <Route path="denials" element={<DenialsPage />} />
        <Route path="payments" element={<PaymentsPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="users" element={<UsersPage />} />
      </Route>
    </Routes>
  );
}