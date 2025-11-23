'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    Camera,
    UserPlus,
    Users,
    Activity,
    LayoutDashboard,
    LogOut,
    Menu,
    X,
    ChevronLeft,
    Settings
} from 'lucide-react';

interface NavItem {
    name: string;
    href: string;
    icon: any;
    adminOnly?: boolean;
}

const navItems: NavItem[] = [
    { name: 'Identify', href: '/identify', icon: Camera },
    { name: 'Enroll', href: '/enroll', icon: UserPlus },
    { name: 'People', href: '/people', icon: Users },
    { name: 'Access Logs', href: '/access-logs', icon: Activity },
    { name: 'Admin Dashboard', href: '/dashboard/admin', icon: LayoutDashboard, adminOnly: true },
];

export default function Sidebar() {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const [user, setUser] = useState<any>(null);
    const pathname = usePathname();
    const router = useRouter();

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (userStr) {
            setUser(JSON.parse(userStr));
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/');
    };

    const filteredNavItems = navItems.filter(item =>
        !item.adminOnly || user?.role === 'Admin'
    );

    return (
        <>
            {/* Mobile Menu Button */}
            <button
                onClick={() => setIsMobileOpen(!isMobileOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-gray-800 rounded-lg text-white hover:bg-gray-700 transition-colors"
            >
                {isMobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Overlay for mobile */}
            {isMobileOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-30"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
                    fixed top-0 left-0 h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 
                    border-r border-gray-800 z-40 transition-all duration-300 flex flex-col
                    ${isCollapsed ? 'w-20' : 'w-64'}
                    ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
                `}
            >
                {/* Logo & Collapse Button */}
                <div className="p-4 border-b border-gray-800 flex items-center justify-between">
                    {!isCollapsed && (
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                                <Camera className="text-white" size={20} />
                            </div>
                            <div>
                                <h1 className="text-white font-bold text-lg">FaceRecog</h1>
                                <p className="text-gray-500 text-xs">AI Recognition</p>
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="hidden lg:block p-2 hover:bg-gray-800 rounded-lg text-gray-400 hover:text-white transition-colors"
                    >
                        <ChevronLeft className={`transition-transform ${isCollapsed ? 'rotate-180' : ''}`} size={20} />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                    {filteredNavItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                onClick={() => setIsMobileOpen(false)}
                                className={`
                                    flex items-center gap-3 px-4 py-3 rounded-lg transition-all
                                    ${isActive
                                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/50'
                                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                    }
                                    ${isCollapsed ? 'justify-center' : ''}
                                `}
                            >
                                <Icon size={20} />
                                {!isCollapsed && <span className="font-medium">{item.name}</span>}
                            </Link>
                        );
                    })}
                </nav>

                {/* User Profile Section */}
                <div className="p-4 border-t border-gray-800">
                    {user && (
                        <div className={`mb-3 ${isCollapsed ? 'hidden' : 'block'}`}>
                            <div className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                                    {user.username[0].toUpperCase()}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-white font-medium text-sm truncate">{user.username}</p>
                                    <p className="text-gray-400 text-xs">{user.role || 'User'}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <Link
                            href="/dashboard/user"
                            className={`flex items-center gap-3 px-4 py-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors ${isCollapsed ? 'justify-center' : ''}`}
                        >
                            <Settings size={18} />
                            {!isCollapsed && <span className="text-sm">Profile</span>}
                        </Link>
                        <button
                            onClick={handleLogout}
                            className={`w-full flex items-center gap-3 px-4 py-2 rounded-lg text-red-400 hover:bg-red-900/20 hover:text-red-300 transition-colors ${isCollapsed ? 'justify-center' : ''}`}
                        >
                            <LogOut size={18} />
                            {!isCollapsed && <span className="text-sm">Logout</span>}
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
}
