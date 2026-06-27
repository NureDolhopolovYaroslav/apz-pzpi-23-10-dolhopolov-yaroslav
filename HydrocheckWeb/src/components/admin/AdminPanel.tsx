import React, { useEffect, useState } from 'react';
import type { User } from '../../types';

const AdminPanel: React.FC = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);

    const loadUsers = () => {
        setLoading(true);
        fetch('http://localhost:8000/admin/users?skip=0&limit=100', {
            headers: {
                'admin-key': 'SECRET_ADMIN_KEY_123'
            }
        })
            .then((res) => {
                if (!res.ok) {
                    throw new Error('Помилка завантаження');
                }
                return res.json();
            })
            .then((data) => {
                setUsers(data);
                setLoading(false);
            })
            .catch(() => {
                setLoading(false);
            });
    };

    useEffect(() => {
        loadUsers();
    }, []);

    const handleDelete = (id: number, username: string) => {
        if (confirm(`Видалити користувача "${username}"?`)) {
            fetch(`http://localhost:8000/admin/users/${id}`, {
                method: 'DELETE',
                headers: {
                    'admin-key': 'SECRET_ADMIN_KEY_123'
                }
            })
                .then((res) => {
                    if (res.ok) {
                        loadUsers();
                    } else {
                        alert('Помилка видалення');
                    }
                })
                .catch(() => alert('Помилка видалення'));
        }
    };

    const handleRoleChange = (id: number, role: string) => {
        fetch(`http://localhost:8000/admin/users/${id}/role`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'admin-key': 'SECRET_ADMIN_KEY_123'
            },
            body: JSON.stringify({ role: role })
        })
            .then((res) => {
                if (res.ok) {
                    loadUsers();
                } else {
                    res.text().then(text => alert('Помилка зміни ролі: ' + text));
                }
            })
            .catch((err) => alert('Помилка зміни ролі: ' + err.message));
    };

    if (loading) {
        return <div className="text-center py-10 text-gray-500">Завантаження...</div>;
    }

    return (
        <div>
            <h1 className="text-2xl font-bold mb-4 text-gray-800">Адмін-панель</h1>
            
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="bg-gray-50 px-6 py-3 border-b">
                    <h2 className="font-semibold text-gray-800">Користувачі</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Логін</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Роль</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Дії</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {users.map((user) => (
                                <tr key={user.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-800">{user.id}</td>
                                    <td className="px-6 py-4 text-sm font-medium text-gray-800">{user.username}</td>
                                    <td className="px-6 py-4 text-sm text-gray-600">{user.email}</td>
                                    <td className="px-6 py-4 text-sm">
                                        <select
                                            value={user.role}
                                            onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                            className="border rounded px-2 py-1 text-sm text-gray-800 bg-white"
                                        >
                                            <option value="admin">admin</option>
                                            <option value="operator">operator</option>
                                            <option value="viewer">viewer</option>
                                        </select>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        {user.username !== 'superadmin' && (
                                            <button
                                                onClick={() => handleDelete(user.id, user.username)}
                                                className="text-red-600 hover:text-red-800 text-sm"
                                            >
                                                Видалити
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;