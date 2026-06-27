import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Перехоплювач для додавання admin_key до всіх запитів на /admin/
api.interceptors.request.use((config) => {
    if (config.url?.includes('/admin/')) {
        config.headers['admin_key'] = 'SECRET_ADMIN_KEY_123';
    }
    return config;
});

// Статистика
export const getStatistics = () => api.get('/api/stats/');

// Пристрої
export const getDevices = () => api.get('/api/devices/');

// Сповіщення
export const getAlerts = (status?: string) =>
    api.get('/api/alerts/', { params: { status } });

// Адмін: користувачі - ВИПРАВЛЕНО
export const getUsers = (skip: number = 0, limit: number = 100) => {
    console.log('Запит до /admin/users з admin_key');
    return api.get('/admin/users', {
        params: { skip, limit },
        headers: { 
            'admin_key': 'SECRET_ADMIN_KEY_123',
            'Accept': 'application/json'
        }
    });
};

export const deleteUser = (userId: number) =>
    api.delete(`/admin/users/${userId}`, {
        headers: { 'admin_key': 'SECRET_ADMIN_KEY_123' }
    });

export const updateUserRole = (userId: number, role: string) =>
    api.patch(`/admin/users/${userId}/role`, { role }, {
        headers: { 'admin_key': 'SECRET_ADMIN_KEY_123' }
    });

export default api;