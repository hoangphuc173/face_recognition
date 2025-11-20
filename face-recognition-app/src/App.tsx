import { useState } from 'react';
import './App.css';
import Login from './components/Login';
import Camera from './components/Camera';
import People from './components/People';

type Page = 'camera' | 'people';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPage, setCurrentPage] = useState<Page>('camera');

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setCurrentPage('camera'); // Default page after login
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'camera':
        return <Camera />;
      case 'people':
        return <People />;
      default:
        return <Camera />;
    }
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="container">
      <nav>
        <div>
          <button onClick={() => setCurrentPage('camera')}>Camera</button>
          <button onClick={() => setCurrentPage('people')}>People</button>
        </div>
        <button onClick={handleLogout}>Logout</button>
      </nav>
      <main>
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
