import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/common/Header';
import Dashboard from './components/user/Dashboard';
import DevicesList from './components/user/DevicesList';
import AlertsList from './components/user/AlertsList';
import AdminPanel from './components/admin/AdminPanel';

function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen bg-gray-100">
                <Header />
                <div className="container mx-auto p-4">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/devices" element={<DevicesList />} />
                        <Route path="/alerts" element={<AlertsList />} />
                        <Route path="/admin" element={<AdminPanel />} />
                    </Routes>
                </div>
            </div>
        </BrowserRouter>
    );
}

export default App;