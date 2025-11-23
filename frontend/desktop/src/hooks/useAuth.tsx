import { useState, useEffect } from 'react';

interface User {
    username: string;
    full_name: string;
    email: string;
    role: string;
    gender?: string;
    hometown?: string;
    current_address?: string;
}

// Helper to decode JWT (basic - for groups/role extraction)
function parseJWT(token: string): any {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

export function useAuth() {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Load user and token from localStorage on mount
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
        }
        setIsLoading(false);
    }, []);

    const login = (tokenData: { access_token: string; role: string;[key: string]: any }, userData: User) => {
        // Store access_token (Cognito token)
        localStorage.setItem('token', tokenData.access_token);
        localStorage.setItem('user', JSON.stringify(userData));
        setToken(tokenData.access_token);
        setUser(userData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setToken(null);
        setUser(null);
    };

    const updateUser = (userData: User) => {
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);
    };

    const isAuthenticated = !!token && !!user;
    const isAdmin = user?.role === 'Admin';

    return {
        user,
        token,
        isLoading,
        isAuthenticated,
        isAdmin,
        login,
        logout,
        updateUser,
    };
}
