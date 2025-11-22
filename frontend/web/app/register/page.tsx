'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth } from '@/lib/api';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card, { CardBody } from '@/components/ui/Card';
import { Eye, EyeOff, UserPlus, ArrowRight, CheckCircle, Mail } from 'lucide-react';

export default function Register() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    // Form Data
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        otp: '',
        full_name: '',
        gender: '',
        hometown: '',
        current_address: ''
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    const handleRegisterInitial = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            // Call register endpoint (which uses Cognito sign_up)
            await auth.register({
                username: formData.username,
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                gender: formData.gender,
                hometown: formData.hometown,
                current_address: formData.current_address
            });
            setStep(2); // Move to verification step
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirmRegistration = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            // Confirm with Cognito
            await auth.confirmRegistration(formData.username, formData.otp);
            // Success! Redirect to login
            router.push('/?registered=true');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Verification failed. Please check the code.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center p-4">
            <Card className="w-full max-w-lg relative z-10">
                <CardBody className="p-8">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
                        <p className="text-gray-400">Step {step} of 2</p>

                        {/* Progress Bar */}
                        <div className="w-full bg-gray-700 h-2 rounded-full mt-4 overflow-hidden">
                            <div
                                className="bg-blue-500 h-full transition-all duration-500 ease-out"
                                style={{ width: `${(step / 2) * 100}%` }}
                            ></div>
                        </div>
                    </div>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm mb-6">
                            {error}
                        </div>
                    )}

                    {/* STEP 1: All Registration Info */}
                    {step === 1 && (
                        <form onSubmit={handleRegisterInitial} className="space-y-5">
                            <Input
                                id="username"
                                label="Username"
                                placeholder="Choose a username"
                                value={formData.username}
                                onChange={handleChange}
                                required
                            />
                            <Input
                                id="email"
                                type="email"
                                label="Email Address"
                                placeholder="name@example.com"
                                value={formData.email}
                                onChange={handleChange}
                                required
                            />
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    label="Password"
                                    placeholder="Create a strong password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-[38px] text-gray-400 hover:text-white transition-colors"
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>

                            <Input
                                id="full_name"
                                label="Full Name"
                                placeholder="John Doe"
                                value={formData.full_name}
                                onChange={handleChange}
                                required
                            />

                            <div className="space-y-2">
                                <label htmlFor="gender" className="block text-sm font-medium text-gray-300">Gender</label>
                                <select
                                    id="gender"
                                    value={formData.gender}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-white transition-all"
                                    required
                                >
                                    <option value="">Select Gender</option>
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>

                            <Input
                                id="hometown"
                                label="Hometown"
                                placeholder="City, Country"
                                value={formData.hometown}
                                onChange={handleChange}
                                required
                            />

                            <Input
                                id="current_address"
                                label="Current Address"
                                placeholder="123 Main St, Apt 4B"
                                value={formData.current_address}
                                onChange={handleChange}
                                required
                            />

                            <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
                                Register <ArrowRight size={18} className="ml-2" />
                            </Button>
                        </form>
                    )}

                    {/* STEP 2: Email Verification */}
                    {step === 2 && (
                        <form onSubmit={handleConfirmRegistration} className="space-y-5">
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <Mail size={32} className="text-blue-400" />
                                </div>
                                <p className="text-gray-300">
                                    We sent a verification code to <span className="font-semibold text-white">{formData.email}</span>
                                </p>
                                <p className="text-sm text-gray-400 mt-2">Check your email (including spam folder)</p>
                            </div>

                            <Input
                                id="otp"
                                label="Verification Code"
                                placeholder="Enter 6-digit code"
                                value={formData.otp}
                                onChange={handleChange}
                                maxLength={6}
                                className="text-center text-2xl tracking-widest"
                                required
                            />

                            <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
                                Verify & Complete <CheckCircle size={18} className="ml-2" />
                            </Button>
                        </form>
                    )}

                    <div className="mt-6 text-center text-sm text-gray-400">
                        Already have an account?{' '}
                        <Link href="/" className="text-blue-400 hover:text-blue-300 font-medium">
                            Sign In
                        </Link>
                    </div>
                </CardBody>
            </Card>
        </div>
    );
}
