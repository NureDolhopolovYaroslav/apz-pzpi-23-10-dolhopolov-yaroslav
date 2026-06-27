import React from 'react';
import { Link } from 'react-router-dom';

const Header: React.FC = () => {
    return (
        <header className="bg-blue-600 text-white p-4 shadow-lg">
            <div className="container mx-auto flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold">
                        <Link to="/">Hydrocheck</Link>
                    </h1>
                    <p className="text-sm">Моніторинг якості води</p>
                </div>
                <nav className="flex items-center gap-4">
                    <Link to="/" className="hover:underline">Дашборд</Link>
                    <Link to="/devices" className="hover:underline">Пристрої</Link>
                    <Link to="/alerts" className="hover:underline">Сповіщення</Link>
                    <Link to="/admin" className="hover:underline text-yellow-300">Адмін</Link>
                </nav>
            </div>
        </header>
    );
};

export default Header;