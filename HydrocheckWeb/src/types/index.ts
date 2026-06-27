export interface Device {
    id: number;
    name: string;
    location: string | null;
    device_type: string | null;
    status: string;
    zone_id: number | null;
    created_at: string;
}

export interface Alert {
    id: number;
    device_id: number;
    parameter: string;
    value: number;
    message: string;
    severity: string;
    status: string;
    created_at: string;
}

export interface Statistics {
    total_devices: number;
    total_measurements: number;
    active_alerts: number;
    avg_water_quality: number | null;
}

export interface User {
    id: number;
    username: string;
    email: string;
    role: string;
    created_at: string;
}