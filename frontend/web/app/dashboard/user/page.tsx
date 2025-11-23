'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Card, { CardBody } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { User, MapPin, Home, Calendar, Edit } from 'lucide-react';
import { auth } from '@/lib/api';

export default function UserDashboard() {
    const [profile, setProfile] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            // We need to implement GET /auth/profile in backend
            // For now, use local storage or mock
            const userStr = localStorage.getItem('user');
            if (!userStr) {
                router.push('/');
                return;
            }
            const user = JSON.parse(userStr);

            // Mock extended profile data
            setProfile({
                ...user,
                full_name: user.full_name || 'John Doe',
                gender: 'Male',
                hometown: 'New York, USA',
                current_address: '123 Main St, Apt 4B, NY',
                join_date: 'Nov 2023'
            });
        } catch (error) {
            console.error('Failed to fetch profile', error);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Loading...</div>;
    }

    return (
        <div className="min-h-screen bg-gray-900 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white">My Profile</h1>
                    <p className="text-gray-400 mt-1">Manage your personal information</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {/* Left Column: Avatar & Basic Info */}
                    <Card className="md:col-span-1">
                        <CardBody className="p-6 text-center">
                            <div className="w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-500/30">
                                <span className="text-4xl font-bold text-white">{profile.username[0].toUpperCase()}</span>
                            </div>
                            <h2 className="text-xl font-bold text-white mb-1">{profile.full_name}</h2>
                            <p className="text-blue-400 text-sm mb-4">@{profile.username}</p>

                            <div className="flex justify-center gap-2 mb-6">
                                <span className="px-3 py-1 bg-gray-800 rounded-full text-xs text-gray-400 border border-gray-700">
                                    {profile.role || 'Member'}
                                </span>
                            </div>

                            <Button variant="outline" className="w-full">
                                <Edit size={16} className="mr-2" />
                                Edit Avatar
                            </Button>
                        </CardBody>
                    </Card>

                    {/* Right Column: Detailed Info */}
                    <Card className="md:col-span-2">
                        <CardBody className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-lg font-semibold text-white">Personal Information</h3>
                                <Button variant="ghost" className="text-blue-400 hover:text-blue-300">
                                    Edit Info
                                </Button>
                            </div>

                            <div className="space-y-6">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                    <div className="space-y-1">
                                        <label className="text-sm text-gray-500 flex items-center gap-2">
                                            <User size={14} /> Full Name
                                        </label>
                                        <p className="text-white font-medium">{profile.full_name}</p>
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-sm text-gray-500 flex items-center gap-2">
                                            <User size={14} /> Gender
                                        </label>
                                        <p className="text-white font-medium">{profile.gender}</p>
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-sm text-gray-500 flex items-center gap-2">
                                            <Home size={14} /> Hometown
                                        </label>
                                        <p className="text-white font-medium">{profile.hometown}</p>
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-sm text-gray-500 flex items-center gap-2">
                                            <MapPin size={14} /> Current Address
                                        </label>
                                        <p className="text-white font-medium">{profile.current_address}</p>
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-sm text-gray-500 flex items-center gap-2">
                                            <Calendar size={14} /> Joined
                                        </label>
                                        <p className="text-white font-medium">{profile.join_date}</p>
                                    </div>
                                </div>
                            </div>
                        </CardBody>
                    </Card>
                </div>
            </div>
        </div>
    );
}
