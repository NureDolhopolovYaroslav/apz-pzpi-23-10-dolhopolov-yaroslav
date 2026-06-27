package com.example.hydrocheckmobile.models

data class Measurement(
    val id: Int,
    val device_id: Int,
    val ph: Double?,
    val temperature: Double?,
    val turbidity: Double?,
    val oxygen: Double?,
    val nitrates: Double?,
    val recorded_at: String
)