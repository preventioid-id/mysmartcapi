<?php
include 'db.php'; // Menggunakan koneksi database yang sama

// Hanya izinkan metode POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header("HTTP/1.0 405 Method Not Allowed");
    echo json_encode(['error' => 'Metode tidak diizinkan.']);
    exit();
}

$data = json_decode(file_get_contents('php://input'));

// Validasi data input sederhana
if (
    !isset($data->full_name) || !isset($data->username) || 
    !isset($data->password) || !isset($data->email) || !isset($data->phone)
) {
    echo json_encode(['error' => 'Semua field wajib diisi.']);
    exit();
}

// KEAMANAN: Selalu hash password sebelum disimpan ke database!
$hashed_password = password_hash($data->password, PASSWORD_DEFAULT);

try {
    $sql = "INSERT INTO users (full_name, username, password, email, phone) VALUES (:full_name, :username, :password, :email, :phone)";
    $stmt = $conn->prepare($sql);

    // Bind parameters
    $stmt->bindParam(':full_name', $data->full_name);
    $stmt->bindParam(':username', $data->username);
    $stmt->bindParam(':password', $hashed_password); // Simpan password yang sudah di-hash
    $stmt->bindParam(':email', $data->email);
    $stmt->bindParam(':phone', $data->phone);

    if ($stmt->execute()) {
        echo json_encode(['message' => 'Registrasi berhasil.', 'userId' => $conn->lastInsertId()]);
    } else {
        echo json_encode(['error' => 'Registrasi gagal. Mungkin username atau email sudah ada.']);
    }
} catch (PDOException $e) {
    // Tangani error jika username/email sudah ada (unique constraint violation)
    if ($e->getCode() == 23000) {
        echo json_encode(['error' => 'Username atau email sudah terdaftar.']);
    } else {
        echo json_encode(['error' => 'Terjadi kesalahan pada server.', 'details' => $e->getMessage()]);
    }
}
?>