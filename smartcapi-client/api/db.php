<?php
// Header untuk mengizinkan CORS (Cross-Origin Resource Sharing)
// Penting agar frontend Vue.js bisa berkomunikasi dengan backend PHP Anda.
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Headers: *");
header("Access-Control-Allow-Methods: *");
header("Content-Type: application/json; charset=UTF-8");

// Konfigurasi koneksi database
$host = 'localhost'; // Host database Anda (biasanya localhost untuk pengembangan lokal)
$db_name = 'smartcapi_db'; // Nama database yang Anda buat
$username = 'root'; // Username database Anda

// Password database Anda.
// Sesuaikan dengan password yang Anda atur untuk MariaDB.
// Baris untuk XAMPP default (tanpa password) dinonaktifkan.
// $password = '';
$password = 'password_anda_untuk_mariadb'; // <-- PASTIKAN INI ADALAH PASSWORD YANG BENAR!

// Mencoba membuat koneksi ke database menggunakan PDO (PHP Data Objects)
try {
    $conn = new PDO("mysql:host={$host};dbname={$db_name}", $username, $password);
    // Mengatur mode error PDO agar exception dilemparkan saat ada error SQL
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    // Jika koneksi gagal, kembalikan respons JSON dengan pesan error dan hentikan eksekusi script
    echo json_encode(['error' => 'Connection failed: ' . $e->getMessage()]);
    exit(); // Hentikan script agar tidak ada kode lain yang berjalan tanpa koneksi database
}
?>