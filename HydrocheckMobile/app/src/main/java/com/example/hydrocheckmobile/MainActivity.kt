package com.example.hydrocheckmobile

import android.os.Bundle
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.hydrocheckmobile.models.Device
import com.example.hydrocheckmobile.repository.Repository
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {

    private lateinit var repository: Repository
    private lateinit var recyclerView: RecyclerView
    private lateinit var tvStatistics: TextView
    private lateinit var deviceAdapter: DeviceAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        repository = Repository()

        setupViews()
        loadData()
    }

    private fun setupViews() {
        tvStatistics = findViewById(R.id.tvStatistics)
        recyclerView = findViewById(R.id.recyclerView)
        recyclerView.layoutManager = LinearLayoutManager(this)

        deviceAdapter = DeviceAdapter(emptyList()) { device ->
            Toast.makeText(this, "Обрано: ${device.name}", Toast.LENGTH_SHORT).show()
        }
        recyclerView.adapter = deviceAdapter
    }

    private fun loadData() {
        lifecycleScope.launch {
            try {
                // Завантажуємо статистику
                val stats = repository.getStatistics()
                if (stats != null) {
                    tvStatistics.text = """
                    Статистика:
                    Пристроїв: ${stats.total_devices}
                    Вимірювань: ${stats.total_measurements}
                    Активних сповіщень: ${stats.active_alerts}
                    Середній WQI: ${stats.avg_water_quality ?: "н/д"}
                """.trimIndent()
                } else {
                    tvStatistics.text = "Не вдалося завантажити статистику"
                }

                // Завантажуємо пристрої
                val devices = repository.getDevices()
                if (devices != null) {
                    deviceAdapter.updateDevices(devices)
                } else {
                    Toast.makeText(this@MainActivity, "Не вдалося завантажити пристрої", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                // Виводимо помилку на екран замість падіння
                tvStatistics.text = "Помилка: ${e.message}"
                Toast.makeText(this@MainActivity, "Помилка: ${e.message}", Toast.LENGTH_LONG).show()
                e.printStackTrace()
            }
        }
    }
}