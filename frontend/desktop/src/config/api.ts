import axios from 'axios';

// Use VITE_API_BASE_URL from environment variables
const API_URL = import.meta.env.VITE_API_BASE_URL || 'https://placeholder-api-url.execute-api.us-east-1.amazonaws.com/prod';

const api = axios.create({
  baseURL: API_URL,
});

// Add token to all requests automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const auth = {
  login: async (username: string, password: string) => {
    const response = await api.post('/auth/token', { username, password });
    return response.data;
  },

  sendOtp: async (email: string) => {
    const response = await api.post('/auth/otp/send', { email });
    return response.data;
  },

  register: async (data: {
    username: string;
    full_name: string;
    email: string;
    password: string;
    otp: string;
    gender?: string;
    hometown?: string;
    current_address?: string;
  }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  updateProfile: async (data: {
    full_name?: string;
    gender?: string;
    hometown?: string;
    current_address?: string;
  }) => {
    const response = await api.put('/auth/profile', data);
    return response.data;
  }
};

export const admin = {
  listUsers: async () => {
    const response = await api.get('/auth/admin/users');
    return response.data;
  },

  updateUser: async (username: string, data: {
    email?: string;
    full_name?: string;
    enabled?: boolean;
    role?: string;
  }) => {
    const response = await api.put(`/auth/admin/users/${username}`, data);
    return response.data;
  },

  deleteUser: async (username: string) => {
    const response = await api.delete(`/auth/admin/users/${username}`);
    return response.data;
  }
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
