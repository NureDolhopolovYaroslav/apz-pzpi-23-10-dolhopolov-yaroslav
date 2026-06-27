package com.example.hydrocheckmobile

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.RecyclerView
import com.example.hydrocheckmobile.models.Device

class DeviceAdapter(
    private var devices: List<Device>,
    private val onItemClick: (Device) -> Unit
) : RecyclerView.Adapter<DeviceAdapter.DeviceViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DeviceViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_device, parent, false)
        return DeviceViewHolder(view)
    }

    override fun onBindViewHolder(holder: DeviceViewHolder, position: Int) {
        val device = devices[position]
        holder.bind(device)
        holder.cardView.setOnClickListener { onItemClick(device) }
    }

    override fun getItemCount(): Int = devices.size

    fun updateDevices(newDevices: List<Device>) {
        devices = newDevices
        notifyDataSetChanged()
    }

    class DeviceViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val cardView: CardView = itemView.findViewById(R.id.cardView)
        private val tvDeviceName: TextView = itemView.findViewById(R.id.tvDeviceName)
        private val tvDeviceLocation: TextView = itemView.findViewById(R.id.tvDeviceLocation)
        private val tvDeviceStatus: TextView = itemView.findViewById(R.id.tvDeviceStatus)

        fun bind(device: Device) {
            tvDeviceName.text = device.name
            tvDeviceLocation.text = device.location ?: "Локація не вказана"
            tvDeviceStatus.text = "Статус: ${device.status}"

            when (device.status) {
                "active" -> tvDeviceStatus.setTextColor(0xFF4CAF50.toInt())
                "inactive" -> tvDeviceStatus.setTextColor(0xFFF44336.toInt())
                else -> tvDeviceStatus.setTextColor(0xFFFF9800.toInt())
            }
        }
    }
}