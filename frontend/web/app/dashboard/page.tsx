'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
    const router = useRouter();

    useEffect(() => {
        const userStr = localStorage.getItem('user');
        if (!userStr) {
            router.push('/');
            return;
        }

        // All users go to the same dashboard
        router.push('/dashboard/main');
    }, []);

    return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">
            <div className="animate-pulse flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-gray-400">Loading dashboard...</p>
            </div>
        </div>
    );
}
