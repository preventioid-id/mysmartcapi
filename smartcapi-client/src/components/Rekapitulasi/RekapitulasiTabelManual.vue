<template>
  <div class="table-container">
    <table class="recap-table">
      <thead>
        <tr>
          <th class="no-column">No</th>
          <th class="name-column">Nama Responden</th>
          <th class="status-column">Status Pendataan</th>
          <th class="duration-column">Durasi Wawancara (detik)</th>
          <th class="action-column">Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="data.length === 0">
          <td colspan="5" class="empty-state">Belum ada data untuk ditampilkan.</td>
        </tr>
        <tr v-for="(item, index) in data" :key="item.name">
          <td class="no-column">{{ index + 1 }}</td>
          <td class="name-column">{{ item.name }}</td>
          <td class="status-column">
            <span :class="getStatusClass(item.status)">
              {{ item.status }}
            </span>
          </td>
          <td class="duration-column">{{ item.duration || 0 }}</td>
          <td class="action-column">
            <button class="icon-btn edit-btn" title="Edit Data" @click="handleEdit(item)">
              ✏️
            </button>
            <button class="icon-btn delete-btn" title="Hapus Data" @click="handleDelete(item)">
              🗑️
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  data: { type: Array, required: true },
  getStatusClass: { type: Function, required: true },
  // BARU: Props untuk handle action
  handleEdit: { type: Function, required: true },
  handleDelete: { type: Function, required: true },
});
</script>

<style scoped>
.table-container { padding-top: 20px; overflow-x: auto; }
.recap-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.recap-table th { background: #f0f0f0; color: #333; padding: 12px 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #ddd; }
.recap-table td { padding: 10px 8px; border-bottom: 1px solid #ddd; text-align: center; vertical-align: middle; }
.no-column { width: 50px; }
.name-column { text-align: left; min-width: 200px; }
.status-column { width: 120px; }
.duration-column { width: 150px; font-weight: 500; }
.empty-state { padding: 40px; text-align: center; color: #888; }

.status-badge { padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; }
.status-submitted { background: #d4edda; color: #155724; }
.status-pending { background: #fff3cd; color: #856404; }
.status-no-data { background: #f8d7da; color: #721c24; }

/* BARU: Style untuk kolom dan tombol Action */
.action-column { width: 100px; }
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 5px;
  margin: 0 5px;
  border-radius: 50%;
  transition: background-color 0.2s;
}
.icon-btn:hover { background-color: #f0f0f0; }
.edit-btn:hover { background-color: #d4edda; }
.delete-btn:hover { background-color: #f8d7da; }
</style>cdL