import axios from 'axios';

// This should be an environment variable. For now, placeholder.
// After deployment, we will update this with the real API Gateway URL.
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://placeholder-api-url.execute-api.us-east-1.amazonaws.com/prod';

const api = axios.create({
    baseURL: API_URL,
});

export const auth = {
    login: (username: string, password: string) =>
        api.post('/auth/token', { username, password }),

    register: (data: any) =>
        api.post('/auth/register', data),

    confirmRegistration: (username: string, code: string) =>
        api.post('/auth/confirm-registration', { username, code }),

    forgotPassword: (username: string) =>
        api.post('/auth/forgot-password', { username }),

    confirmForgotPassword: (data: any) =>
        api.post('/auth/forgot-password/confirm', data),
};

export const enroll = {
    enrollUser: (formData: FormData) =>
        api.post('/enroll', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }),
};

export const identify = {
    identifyFace: (formData: FormData) =>
        api.post('/identify', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }),
};

export const people = {
    list: () => api.get('/people'),
    delete: (userId: string) => api.delete(`/people/${userId}`),
};

export const logs = {
    list: () => api.get('/logs'),
};

export default api;
