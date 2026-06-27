import React, { useEffect, useState } from 'react';
import { getDevices } from '../../api/api';
import type { Device } from '../../types';

const DevicesList: React.FC = () => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getDevices()
            .then((res) => {
                setDevices(res.data);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    if (loading) {
        return <div className="text-center py-10 text-gray-500">Завантаження...</div>;
    }

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4 text-gray-800">Пристрої</h1>
            <div className="space-y-2">
                {devices.map((device) => (
                    <div key={device.id} className="bg-white p-4 rounded-lg shadow-md border">
                        <div className="flex justify-between items-center">
                            <div>
                                <div className="font-bold">{device.name}</div>
                                <div className="text-gray-500 text-sm">{device.location || 'Локація не вказана'}</div>
                            </div>
                            <div>
                                <span className={`px-3 py-1 rounded-full text-sm ${
                                    device.status === 'active' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                                }`}>
                                    {device.status === 'active' ? 'Активний' : 'Неактивний'}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DevicesList;