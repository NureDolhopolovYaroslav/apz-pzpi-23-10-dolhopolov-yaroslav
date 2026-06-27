import React, { useEffect, useState } from 'react';
import { getAlerts } from '../../api/api';
import type { Alert } from '../../types';

const AlertsList: React.FC = () => {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<string>('active');

    const loadAlerts = () => {
        setLoading(true);
        getAlerts(filter === 'all' ? undefined : filter)
            .then((res) => {
                setAlerts(res.data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    };

    useEffect(() => {
        loadAlerts();
    }, [filter]);

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-red-100 text-red-700';
            case 'warning': return 'bg-yellow-100 text-yellow-700';
            case 'info': return 'bg-blue-100 text-blue-700';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    const getStatusColor = (status: string) => {
        return status === 'active' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700';
    };

    if (loading) {
        return <div className="text-center py-10 text-gray-500">Завантаження...</div>;
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-bold text-gray-800">Сповіщення</h1>
                <div className="flex gap-2">
                    <button
                        onClick={() => setFilter('active')}
                        className={`px-4 py-2 rounded ${filter === 'active' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
                    >
                        Активні
                    </button>
                    <button
                        onClick={() => setFilter('all')}
                        className={`px-4 py-2 rounded ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
                    >
                        Всі
                    </button>
                </div>
            </div>

            {alerts.length === 0 ? (
                <div className="text-center py-10 text-gray-500">Немає сповіщень</div>
            ) : (
                <div className="space-y-3">
                    {alerts.map((alert) => (
                        <div key={alert.id} className="bg-white p-4 rounded-lg shadow-md border-l-4"
                             style={{ borderLeftColor: alert.severity === 'critical' ? '#dc2626' : alert.severity === 'warning' ? '#f59e0b' : '#3b82f6' }}>
                            <div className="flex justify-between items-start">
                                <div>
                                    <div className="font-bold">{alert.parameter}</div>
                                    <div className="text-gray-600 text-sm">{alert.message}</div>
                                    <div className="text-gray-400 text-xs mt-1">
                                        Пристрій ID: {alert.device_id} • {new Date(alert.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityColor(alert.severity)}`}>
                                        {alert.severity}
                                    </span>
                                    <span className={`ml-2 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(alert.status)}`}>
                                        {alert.status}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AlertsList;