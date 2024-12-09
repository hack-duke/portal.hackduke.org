import { useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { FullPageLoadingSpinner } from './FullPageLoadingSpinner';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth0();

  if (isLoading) {
    return <FullPageLoadingSpinner/>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;