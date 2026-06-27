package com.example.hydrocheckmobile.api

import com.example.hydrocheckmobile.models.Alert
import com.example.hydrocheckmobile.models.Device
import com.example.hydrocheckmobile.models.Measurement
import com.example.hydrocheckmobile.models.Statistics
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {
    @GET("api/stats/")
    suspend fun getStatistics(
        @Query("user_id") userId: Int? = null,
        @Query("zone_id") zoneId: Int? = null
    ): Response<Statistics>

    @GET("api/devices/")
    suspend fun getDevices(
        @Query("zone_id") zoneId: Int? = null,
        @Query("status") status: String? = null,
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 100
    ): Response<List<Device>>

    @GET("api/devices/{device_id}/measurements/")
    suspend fun getMeasurements(
        @Path("device_id") deviceId: Int,
        @Query("limit") limit: Int = 50
    ): Response<List<Measurement>>

    @GET("api/alerts/")
    suspend fun getAlerts(
        @Query("device_id") deviceId: Int? = null,
        @Query("status") status: String? = "active",
        @Query("severity") severity: String? = null
    ): Response<List<Alert>>
}