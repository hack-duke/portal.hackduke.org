import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import LoginPage from './pages/LoginPage';
import AdminPage from './pages/AdminPage'
import ProtectedRoute from './components/ProtectedRoute';
import ApplicationPage from './pages/ApplicationPage';
import ApplicationStatusPage from './pages/ApplicationStatusPage';
import './App.css'
import { FullPageLoadingSpinner } from './components/FullPageLoadingSpinner';

function App() {
  const { isLoading } = useAuth0();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route 
        path="/application" 
        element={
          <ProtectedRoute>
            <ApplicationPage />
          </ProtectedRoute>
        } 
        />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/status" element={
          <ProtectedRoute>
            <ApplicationStatusPage />
          </ProtectedRoute>
        } />
      </Routes>
    </Router>
  )
}

export default App;