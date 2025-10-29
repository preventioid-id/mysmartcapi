<!-- src/components/RekapitulasiPendataan.vue -->
<template>
  <div class="recap-container">
    <div class="header">
      <h1>Rekapitulasi Pendataan</h1>
    </div>

    <div class="table-container">
      <table class="recap-table">
        <thead>
          <tr>
            <th class="no-column">No</th>
            <th class="name-column">Nama Kepala Keluarga</th>
            <th class="status-column">Status Pendataan</th>
            <th class="rekaman-column">Rekaman</th>
            <th class="mode-column">Mode Pendataan</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in dataList" :key="index">
            <td class="no-column">{{ index + 1 }}</td>
            <td class="name-column">{{ item.name }}</td>
            <td class="status-column">
              <span :class="getStatusClass(item.status)">
                {{ item.status }}
              </span>
            </td>
            <td class="rekaman-column">
              <button 
                class="play-btn" 
                :disabled="!item.hasRecording"
                @click="playRecording(item)"
                :title="item.hasRecording ? 'Putar rekaman' : 'Tidak ada rekaman'"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </button>
            </td>
            <td class="mode-column">
              <span :class="getModeClass(item.mode)">
                {{ item.mode }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="summary-section">
      <div class="summary-stats">
        <div class="stat-item">
          <span class="stat-number">{{ totalEntries }}</span>
          <div class="stat-label">Total Data</div>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ submittedCount }}</span>
          <div class="stat-label">Submitted</div>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ pendingCount }}</span>
          <div class="stat-label">Pending</div>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ aiModeCount }}</span>
          <div class="stat-label">dengan AI</div>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ manualModeCount }}</span>
          <div class="stat-label">Manual</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Sample data - sesuai dengan gambar
const dataList = ref([
  { name: 'Budi Santoso', status: 'Submitted', hasRecording: true, mode: 'dengan Asistensi AI' },
  { name: 'Siti Rahayu', status: 'Pending', hasRecording: false, mode: 'tanpa Asistensi AI' },
  { name: 'Ahmad Wijaya', status: 'No Data', hasRecording: false, mode: 'tanpa Asistensi AI' },
  { name: 'Dewi Lestari', status: 'Pending', hasRecording: true, mode: 'dengan Asistensi AI' },
  { name: 'Rudi Hermawan', status: 'No Data', hasRecording: false, mode: 'tanpa Asistensi AI' },
  { name: 'Maya Sari', status: 'Pending', hasRecording: false, mode: 'dengan Asistensi AI' },
  { name: 'Andi Pratama', status: 'No Data', hasRecording: false, mode: 'tanpa Asistensi AI' },
  { name: 'Rina Maharani', status: 'Submitted', hasRecording: true, mode: 'dengan Asistensi AI' },
  { name: 'Dedi Kurniawan', status: 'Submitted', hasRecording: true, mode: 'tanpa Asistensi AI' },
  { name: 'Fitri Handayani', status: 'No Data', hasRecording: false, mode: 'dengan Asistensi AI' },
  { name: 'Hendra Saputra', status: 'No Data', hasRecording: false, mode: 'tanpa Asistensi AI' },
  { name: 'Indah Permata', status: 'Pending', hasRecording: false, mode: 'dengan Asistensi AI' },
  { name: 'Joko Susilo', status: 'Submitted', hasRecording: true, mode: 'dengan Asistensi AI' },
  { name: 'Kartika Dewi', status: 'Submitted', hasRecording: true, mode: 'tanpa Asistensi AI' },
  { name: 'Lukman Hakim', status: 'Pending', hasRecording: false, mode: 'dengan Asistensi AI' }
])

// Computed properties for statistics
const totalEntries = computed(() => dataList.value.length)
const submittedCount = computed(() => 
  dataList.value.filter(item => item.status === 'Submitted').length
)
const pendingCount = computed(() => 
  dataList.value.filter(item => item.status === 'Pending').length
)
const aiModeCount = computed(() => 
  dataList.value.filter(item => item.mode === 'dengan Asistensi AI').length
)
const manualModeCount = computed(() => 
  dataList.value.filter(item => item.mode === 'tanpa Asistensi AI').length
)

// Methods
const getStatusClass = (status) => {
  const baseClass = 'status-badge '
  switch (status) {
    case 'Submitted':
      return baseClass + 'status-submitted'
    case 'Pending':
      return baseClass + 'status-pending'
    case 'No Data':
      return baseClass + 'status-no-data'
    default:
      return baseClass
  }
}

const getModeClass = (mode) => {
  const baseClass = 'mode-badge '
  return baseClass + (mode === 'dengan Asistensi AI' ? 'mode-ai' : 'mode-manual')
}

const playRecording = (item) => {
  if (item.hasRecording) {
    alert(`Memutar rekaman untuk: ${item.name}`)
    // Di sini bisa ditambahkan logika untuk memutar rekaman audio
  }
}
</script>

<style scoped>
.recap-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.header {
  background: #1155cc;
  color: white;
  padding: 20px;
  text-align: center;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.table-container {
  padding: 20px;
  overflow-x: auto;
}

.recap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.recap-table th {
  background: #1155cc;
  color: white;
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  border: 1px solid #0d47a1;
}

.recap-table td {
  padding: 10px 8px;
  border: 1px solid #ddd;
  text-align: center;
  vertical-align: middle;
}

.recap-table tr:nth-child(even) {
  background: #f9f9f9;
}

.recap-table tr:hover {
  background: #f0f0f0;
}

.no-column {
  width: 50px;
  font-weight: 600;
}

.name-column {
  text-align: left;
  min-width: 200px;
}

.status-column {
  width: 100px;
}

.rekaman-column {
  width: 80px;
}

.mode-column {
  width: 120px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-submitted {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.status-no-data {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f1b0b7;
}

.mode-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.mode-ai {
  background: #e3f2fd;
  color: #1565c0;
  border: 1px solid #bbdefb;
}

.mode-manual {
  background: #f3e5f5;
  color: #7b1fa2;
  border: 1px solid #e1bee7;
}

.play-btn {
  background: #28a745;
  color: white;
  border: none;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  transition: all 0.2s;
}

.play-btn:hover {
  background: #218838;
  transform: scale(1.1);
}

.play-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

.summary-section {
  background: #f8f9fa;
  padding: 20px;
  border-top: 1px solid #ddd;
}

.summary-stats {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  text-align: center;
  min-width: 120px;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #1155cc;
  display: block;
}

.stat-label {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  margin-top: 5px;
}

@media (max-width: 768px) {
  .header h1 {
    font-size: 18px;
  }

  .table-container {
    padding: 10px;
  }

  .recap-table {
    font-size: 12px;
  }

  .recap-table th,
  .recap-table td {
    padding: 8px 4px;
  }

  .name-column {
    min-width: 150px;
  }

  .summary-stats {
    flex-direction: column;
    gap: 15px;
  }

  .stat-item {
    min-width: auto;
  }
}
</style>