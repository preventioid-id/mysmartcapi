<?php
include 'db.php';

$method = $_SERVER['REQUEST_METHOD'];

// Buat direktori 'uploads' jika belum ada
$uploadDir = 'uploads';
if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}

switch ($method) {
    case 'GET':
        if (isset($_GET['id'])) {
            $id = $_GET['id'];
            $stmt = $conn->prepare("SELECT * FROM interviews WHERE id = :id");
            $stmt->bindParam(':id', $id);
            $stmt->execute();
            echo json_encode($stmt->fetch(PDO::FETCH_ASSOC));
        } else {
            $stmt = $conn->prepare("SELECT id, name, status, mode, duration, has_recording, recording_path FROM interviews ORDER BY created_at DESC");
            $stmt->execute();
            echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
        }
        break;

    case 'POST':
        // Data diambil dari $_POST karena menggunakan FormData
        $data = $_POST;

        // Proses upload file rekaman jika ada
        $recording_path = null;
        if (isset($_FILES['audio_file']) && $_FILES['audio_file']['error'] == 0) {
            $fileName = uniqid() . '-' . basename($_FILES['audio_file']['name']);
            $uploadPath = $uploadDir . '/' . $fileName;

            if (move_uploaded_file($_FILES['audio_file']['tmp_name'], $uploadPath)) {
                $recording_path = $uploadPath;
            } else {
                echo json_encode(['error' => 'Gagal menyimpan file rekaman.']);
                exit();
            }
        }
        
        // Konversi format tanggal dari dd/mm/yyyy ke Y-m-d untuk SQL
        $tanggal_lahir_sql = null;
        if (!empty($data['tanggal_lahir'])) {
            $date = DateTime::createFromFormat('d/m/Y', $data['tanggal_lahir']);
            if ($date) {
                $tanggal_lahir_sql = $date->format('Y-m-d');
            }
        }

        $sql = "INSERT INTO interviews (name, mode, duration, alamat, tempat_lahir, tanggal_lahir, usia, pendidikan, pekerjaan, hobi, nomor_telepon, alamat_email, status, has_recording, recording_path) VALUES (:name, :mode, :duration, :alamat, :tempat_lahir, :tanggal_lahir, :usia, :pendidikan, :pekerjaan, :hobi, :nomor_telepon, :alamat_email, 'Submitted', :has_recording, :recording_path)";
        $stmt = $conn->prepare($sql);

        $stmt->bindParam(':name', $data['nama']); // Key di FormData adalah 'nama'
        $stmt->bindParam(':mode', $data['mode']);
        $stmt->bindParam(':duration', $data['duration']);
        $stmt->bindParam(':alamat', $data['alamat']);
        $stmt->bindParam(':tempat_lahir', $data['tempat_lahir']);
        $stmt->bindParam(':tanggal_lahir', $tanggal_lahir_sql);
        $stmt->bindParam(':usia', $data['usia']);
        $stmt->bindParam(':pendidikan', $data['pendidikan']);
        $stmt->bindParam(':pekerjaan', $data['pekerjaan']);
        $stmt->bindParam(':hobi', $data['hobi']);
        $stmt->bindParam(':nomor_telepon', $data['nomor_telepon']);
        $stmt->bindParam(':alamat_email', $data['alamat_email']);
        $stmt->bindParam(':has_recording', $data['has_recording']);
        $stmt->bindParam(':recording_path', $recording_path);

        if ($stmt->execute()) {
            echo json_encode(['message' => 'Data wawancara berhasil ditambahkan.', 'id' => $conn->lastInsertId()]);
        } else {
            echo json_encode(['error' => 'Gagal menambahkan data.', 'details' => $stmt->errorInfo()]);
        }
        break;
    
    // Metode PUT dan DELETE tidak diubah
    case 'PUT':
        $data = json_decode(file_get_contents('php://input'));
        // ... (kode PUT yang ada tetap di sini) ...
        break;

    case 'DELETE':
        $id = $_GET['id'];
        $stmt = $conn->prepare("DELETE FROM interviews WHERE id = :id");
        $stmt->bindParam(':id', $id);
        if ($stmt->execute()) {
            echo json_encode(['message' => 'Data berhasil dihapus.']);
        } else {
            echo json_encode(['error' => 'Gagal menghapus data.']);
        }
        break;

    default:
        header("HTTP/1.0 405 Method Not Allowed");
        echo json_encode(['error' => 'Metode ' . $method . ' tidak diizinkan.']);
        break;
}
?>