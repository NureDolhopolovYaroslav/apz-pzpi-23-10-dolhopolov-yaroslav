package com.example.hydrocheckmobile.models

data class Device(
    val id: Int,
    val name: String,
    val location: String?,
    val device_type: String?,
    val status: String,
    val zone_id: Int?,
    val created_at: String
)