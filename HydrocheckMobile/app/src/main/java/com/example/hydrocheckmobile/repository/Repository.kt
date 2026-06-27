package com.example.hydrocheckmobile.repository

import com.example.hydrocheckmobile.api.RetrofitClient
import com.example.hydrocheckmobile.models.Alert
import com.example.hydrocheckmobile.models.Device
import com.example.hydrocheckmobile.models.Measurement
import com.example.hydrocheckmobile.models.Statistics

class Repository {
    private val apiService = RetrofitClient.apiService

    suspend fun getStatistics(userId: Int? = null, zoneId: Int? = null): Statistics? {
        val response = apiService.getStatistics(userId, zoneId)
        return if (response.isSuccessful) response.body() else null
    }

    suspend fun getDevices(zoneId: Int? = null, status: String? = null): List<Device>? {
        val response = apiService.getDevices(zoneId, status)
        return if (response.isSuccessful) response.body() else null
    }

    suspend fun getMeasurements(deviceId: Int): List<Measurement>? {
        val response = apiService.getMeasurements(deviceId)
        return if (response.isSuccessful) response.body() else null
    }

    suspend fun getAlerts(deviceId: Int? = null): List<Alert>? {
        val response = apiService.getAlerts(deviceId)
        return if (response.isSuccessful) response.body() else null
    }
}