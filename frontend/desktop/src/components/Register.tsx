import React, { useState } from 'react';
import { LogIn, UserPlus, Mail, Lock, User, AlertCircle, CheckCircle } from 'lucide-react';
import Button from './ui/Button';
import Input from './ui/Input';
import Card from './ui/Card';
import { auth } from '../config/api';

interface RegisterProps {
    onSuccess: () => void;
    onBackToLogin: () => void;
}

export function Register({ onSuccess, onBackToLogin }: RegisterProps) {
    const [formData, setFormData] = useState({
        username: '',
        fullName: '',
        email: '',
        password: '',
        confirmPassword: '',
        gender: '',
        hometown: '',
        currentAddress: '',
        otp: ''
    });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [isLoading, setIsLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [step, setStep] = useState(1); // 1: Details, 2: OTP

    const validateForm = (): boolean => {
        const newErrors: Record<string, string> = {};

        // Username validation
        if (!formData.username) {
            newErrors.username = 'Username is required';
        } else if (formData.username.length < 3) {
            newErrors.username = 'Username must be at least 3 characters';
        }

        // Full name validation
        if (!formData.fullName) {
            newErrors.fullName = 'Full name is required';
        }

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!formData.email) {
            newErrors.email = 'Email is required';
        } else if (!emailRegex.test(formData.email)) {
            newErrors.email = 'Please enter a valid email address';
        }

        // Password validation
        if (!formData.password) {
            newErrors.password = 'Password is required';
        } else if (formData.password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }

        // Confirm password validation
        if (!formData.confirmPassword) {
            newErrors.confirmPassword = 'Please confirm your password';
        } else if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Passwords do not match';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMessage('');
        setSuccessMessage('');

        if (step === 1) {
            if (!validateForm()) {
                return;
            }

            setIsLoading(true);
            try {
                await auth.sendOtp(formData.email);
                setStep(2);
                setSuccessMessage('OTP sent to your email. Please check and enter below.');
            } catch (error: any) {
                const message = error.response?.data?.detail || 'Failed to send OTP. Please try again.';
                setErrorMessage(message);
            } finally {
                setIsLoading(false);
            }
        } else {
            // Step 2: Verify OTP and Register
            if (!formData.otp) {
                setErrors(prev => ({ ...prev, otp: 'OTP is required' }));
                return;
            }

            setIsLoading(true);
            try {
                await auth.register({
                    username: formData.username,
                    full_name: formData.fullName,
                    email: formData.email,
                    password: formData.password,
                    otp: formData.otp,
                    gender: formData.gender || undefined,
                    hometown: formData.hometown || undefined,
                    current_address: formData.currentAddress || undefined
                });

                setSuccessMessage('Account created successfully! Redirecting to login...');

                // Redirect to login after 2 seconds
                setTimeout(() => {
                    onSuccess();
                }, 2000);
            } catch (error: any) {
                const message = error.response?.data?.detail || 'Registration failed. Please try again.';
                setErrorMessage(message);
            } finally {
                setIsLoading(false);
            }
        }
    };

    const handleChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        // Clear error for this field when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: '' }));
        }
    };

    const getPasswordStrength = (): { label: string; color: string; width: string } => {
        const { password } = formData;
        if (!password) return { label: '', color: '', width: '0%' };

        let strength = 0;
        if (password.length >= 6) strength++;
        if (password.length >= 10) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;

        if (strength <= 2) return { label: 'Weak', color: 'bg-red-500', width: '33%' };
        if (strength <= 3) return { label: 'Medium', color: 'bg-yellow-500', width: '66%' };
        return { label: 'Strong', color: 'bg-green-500', width: '100%' };
    };

    const passwordStrength = getPasswordStrength();

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
            <Card className="w-full max-w-md p-8 space-y-6 shadow-2xl">
                <div className="text-center space-y-2">
                    <div className="flex justify-center">
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-full">
                            <UserPlus className="w-8 h-8 text-white" />
                        </div>
                    </div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Create Account</h1>
                    <p className="text-gray-600 dark:text-gray-400">Sign up to get started</p>
                </div>

                {errorMessage && (
                    <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-4 rounded">
                        <div className="flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 text-red-500" />
                            <p className="text-sm text-red-700 dark:text-red-400">{errorMessage}</p>
                        </div>
                    </div>
                )}

                {successMessage && (
                    <div className="bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 p-4 rounded">
                        <div className="flex items-center gap-2">
                            <CheckCircle className="w-5 h-5 text-green-500" />
                            <p className="text-sm text-green-700 dark:text-green-400">{successMessage}</p>
                        </div>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Account Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <Input
                                icon={User}
                                type="text"
                                placeholder="Username"
                                value={formData.username}
                                onChange={(e) => handleChange('username', e.target.value)}
                                error={errors.username}
                                disabled={isLoading}
                                autoFocus
                            />
                        </div>

                        <div>
                            <Input
                                icon={User}
                                type="text"
                                placeholder="Full Name"
                                value={formData.fullName}
                                onChange={(e) => handleChange('fullName', e.target.value)}
                                error={errors.fullName}
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div>
                        <Input
                            icon={Mail}
                            type="email"
                            placeholder="Email Address"
                            value={formData.email}
                            onChange={(e) => handleChange('email', e.target.value)}
                            error={errors.email}
                            disabled={isLoading}
                        />
                    </div>

                    {/* Additional Profile Info (Optional) */}
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                            Additional Information (Optional)
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <select
                                    value={formData.gender}
                                    onChange={(e) => handleChange('gender', e.target.value)}
                                    disabled={isLoading}
                                    className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-white"
                                >
                                    <option value="">Select Gender</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>

                            <div>
                                <Input
                                    type="text"
                                    placeholder="Hometown"
                                    value={formData.hometown}
                                    onChange={(e) => handleChange('hometown', e.target.value)}
                                    disabled={isLoading}
                                />
                            </div>
                        </div>

                        <div className="mt-4">
                            <Input
                                type="text"
                                placeholder="Current Address"
                                value={formData.currentAddress}
                                onChange={(e) => handleChange('currentAddress', e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                        <div>
                            <Input
                                icon={Lock}
                                type="password"
                                placeholder="Password"
                                value={formData.password}
                                onChange={(e) => handleChange('password', e.target.value)}
                                error={errors.password}
                                disabled={isLoading}
                            />
                            {formData.password && (
                                <div className="mt-2">
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-gray-600 dark:text-gray-400">Password strength:</span>
                                        <span className={`font-medium ${passwordStrength.label === 'Strong' ? 'text-green-600' :
                                            passwordStrength.label === 'Medium' ? 'text-yellow-600' :
                                                'text-red-600'
                                            }`}>
                                            {passwordStrength.label}
                                        </span>
                                    </div>
                                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${passwordStrength.color} transition-all duration-300`}
                                            style={{ width: passwordStrength.width }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="mt-4">
                            <Input
                                icon={Lock}
                                type="password"
                                placeholder="Confirm Password"
                                value={formData.confirmPassword}
                                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                                error={errors.confirmPassword}
                                disabled={isLoading || step === 2}
                            />
                        </div>

                        {step === 2 && (
                            <div className="mt-4 animate-fade-in">
                                <Input
                                    icon={Lock}
                                    type="text"
                                    placeholder="Enter OTP"
                                    value={formData.otp}
                                    onChange={(e) => handleChange('otp', e.target.value)}
                                    error={errors.otp}
                                    disabled={isLoading}
                                    autoFocus
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    Check your email for the verification code.
                                </p>
                            </div>
                        )}

                        <Button
                            type="submit"
                            className="w-full mt-6"
                            size="lg"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                                    {step === 1 ? 'Sending OTP...' : 'Creating Account...'}
                                </>
                            ) : (
                                <>
                                    <UserPlus className="w-5 h-5 mr-2" />
                                    {step === 1 ? 'Next: Verify Email' : 'Complete Registration'}
                                </>
                            )}
                        </Button>
                    </div>
                </form>

                <div className="text-center">
                    <button
                        onClick={onBackToLogin}
                        className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center justify-center gap-2 mx-auto"
                        disabled={isLoading}
                    >
                        <LogIn className="w-4 h-4" />
                        Already have an account? Sign In
                    </button>
                </div>
            </Card>
        </div>
    );
}
