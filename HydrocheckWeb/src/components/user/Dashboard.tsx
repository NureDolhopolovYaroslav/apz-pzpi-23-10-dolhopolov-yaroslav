import React, { useEffect, useState } from 'react';
import { getStatistics } from '../../api/api';
import type { Statistics } from '../../types';

const Dashboard: React.FC = () => {
    const [stats, setStats] = useState<Statistics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getStatistics()
            .then((res) => {
                setStats(res.data);
                setLoading(false);
            })
            .catch(() => {
                setError('Не вдалося завантажити статистику');
                setLoading(false);
            });
    }, []);

    if (loading) {
        return <div className="text-center py-10 text-gray-500">Завантаження...</div>;
    }

    if (error) {
        return <div className="text-center py-10 text-red-500">{error}</div>;
    }

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4 text-gray-800">Статистика</h1>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-6 rounded-lg shadow-md">
                    <div className="text-3xl font-bold text-blue-600">{stats?.total_devices ?? 0}</div>
                    <div className="text-gray-600">Пристроїв</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-md">
                    <div className="text-3xl font-bold text-green-600">{stats?.total_measurements ?? 0}</div>
                    <div className="text-gray-600">Вимірювань</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-md">
                    <div className="text-3xl font-bold text-red-600">{stats?.active_alerts ?? 0}</div>
                    <div className="text-gray-600">Активних сповіщень</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-md">
                    <div className="text-3xl font-bold text-purple-600">{stats?.avg_water_quality?.toFixed(2) ?? 'N/A'}</div>
                    <div className="text-gray-600">Середній WQI</div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;