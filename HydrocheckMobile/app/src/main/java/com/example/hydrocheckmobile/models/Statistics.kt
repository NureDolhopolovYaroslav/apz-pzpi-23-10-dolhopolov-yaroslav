package com.example.hydrocheckmobile.models

data class Statistics(
    val total_devices: Int,
    val total_measurements: Int,
    val active_alerts: Int,
    val avg_water_quality: Double?
)