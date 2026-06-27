package com.example.hydrocheckmobile.models

data class Alert(
    val id: Int,
    val device_id: Int,
    val parameter: String,
    val value: Float,
    val message: String,
    val severity: String,
    val status: String,
    val created_at: String
)