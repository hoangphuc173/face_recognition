import { useState, useEffect } from 'react';
import Login from './components/Login';
import { Register } from './components/Register';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
import People from './components/People';
import Camera from './components/Camera';
import Logs from './components/Logs';
import { Enroll } from './components/Enroll';
import { AdminDashboard } from './components/admin/AdminDashboard';
import { UserManagement } from './components/admin/UserManagement';
import { useAuth } from './hooks/useAuth';

type Page = 'dashboard' | 'identify' | 'enroll' | 'people' | 'logs' | 'admin-dashboard' | 'user-management';

function App() {
  const { isAuthenticated: authStatus, user, login: authLogin } = useAuth();
  const [isAuthenticated, setIsAuthenticated] = useState(authStatus);
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [isLoading, setIsLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);

  useEffect(() => {
    // Check for existing token
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard onNavigate={(page) => setCurrentPage(page as Page)} />;
      case 'people':
        return <People />;
      case 'identify':
        return <Camera />;
      case 'enroll':
        return <Enroll />;
      case 'logs':
        return <Logs />;
      case 'admin-dashboard':
        return <AdminDashboard onNavigate={(page) => setCurrentPage(page as Page)} />;
      case 'user-management':
        return <UserManagement />;
      default:
        return <Dashboard onNavigate={(page) => setCurrentPage(page as Page)} />;
    }
  };

  if (isLoading) {
    return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-white">Loading...</div>;
  }

  if (!isAuthenticated) {
    if (showRegister) {
      return (
        <Register
          onSuccess={() => {
            setShowRegister(false);
            // Optionally show success message on login page
          }}
          onBackToLogin={() => setShowRegister(false)}
        />
      );
    }
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onSignUpClick={() => setShowRegister(true)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar
        currentPage={currentPage}
        onNavigate={(page) => setCurrentPage(page as Page)}
        onLogout={handleLogout}
      />
      <main className="container mx-auto pb-8">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
