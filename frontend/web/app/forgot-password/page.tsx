'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth } from '@/lib/api';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card, { CardBody } from '@/components/ui/Card';
import { KeyRound, CheckCircle, ArrowLeft, Mail } from 'lucide-react';

export default function ForgotPasswordPage() {
    const [step, setStep] = useState<1 | 2>(1);
    const [username, setUsername] = useState('');
    const [otp, setOtp] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
    const router = useRouter();

    const handleRequestReset = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage(null);
        try {
            await auth.forgotPassword(username);
            setStep(2);
            setMessage({ type: 'success', text: 'Verification code sent to your email.' });
        } catch (err: any) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to send code.' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleConfirmReset = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage(null);
        try {
            await auth.confirmForgotPassword({ username, otp, new_password: newPassword });
            setMessage({ type: 'success', text: 'Password reset successfully! Redirecting...' });
            setTimeout(() => router.push('/'), 2000);
        } catch (err: any) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to reset password.' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardBody className="p-8">
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-500/20 text-blue-400 rounded-full mb-4">
                            <KeyRound size={32} />
                        </div>
                        <h1 className="text-2xl font-bold text-white mb-2">Reset Password</h1>
                        <p className="text-gray-400">
                            {step === 1 ? "Enter your username to receive a reset code" : "Enter the code and your new password"}
                        </p>
                    </div>

                    {message && (
                        <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${message.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                            {message.type === 'success' ? <CheckCircle size={20} /> : <KeyRound size={20} />}
                            {message.text}
                        </div>
                    )}

                    {step === 1 ? (
                        <form onSubmit={handleRequestReset} className="space-y-6">
                            <Input
                                label="Username"
                                placeholder="Enter your username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                icon={<Mail size={18} />}
                            />
                            <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
                                Send Reset Code
                            </Button>
                        </form>
                    ) : (
                        <form onSubmit={handleConfirmReset} className="space-y-6">
                            <Input
                                label="Verification Code"
                                placeholder="Enter 6-digit code"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                required
                            />
                            <Input
                                type="password"
                                label="New Password"
                                placeholder="Enter new password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                required
                            />
                            <Button type="submit" variant="primary" className="w-full" isLoading={isLoading}>
                                Reset Password
                            </Button>
                        </form>
                    )}

                    <div className="mt-6 text-center">
                        <Link href="/" className="text-gray-400 hover:text-white flex items-center justify-center gap-2 transition-colors">
                            <ArrowLeft size={16} />
                            Back to Login
                        </Link>
                    </div>
                </CardBody>
            </Card>
        </div>
    );
}
