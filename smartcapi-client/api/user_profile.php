<?php
// Sertakan file koneksi database dan header
include 'db.php';

// Pastikan metode request adalah GET
if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405); // Method Not Allowed
    echo json_encode(['success' => false, 'message' => 'Metode request tidak diizinkan.']);
    exit();
}

// --- (Opsional tapi Direkomendasikan) Validasi Token Autentikasi ---
// Di aplikasi production, Anda harus memvalidasi token yang dikirim di header
// untuk memastikan hanya pengguna yang login yang bisa mengakses data ini.
/*
$headers = getallheaders();
if (!isset($headers['Authorization'])) {
    http_response_code(401); // Unauthorized
    echo json_encode(['success' => false, 'message' => 'Token autentikasi tidak ditemukan.']);
    exit();
}
// Logika untuk validasi token (misalnya, JWT) akan ada di sini...
*/
// -----------------------------------------------------------------


// Validasi input ID pengguna
if (!isset($_GET['id']) || empty($_GET['id'])) {
    http_response_code(400); // Bad Request
    echo json_encode(['success' => false, 'message' => 'ID pengguna tidak disertakan dalam permintaan.']);
    exit();
}

// Sanitasi input untuk keamanan
$user_id = htmlspecialchars(strip_tags($_GET['id']));

try {
    // Siapkan query SQL untuk mengambil data dari tabel 'users'
    // Kita hanya mengambil kolom yang dibutuhkan oleh halaman profil
    $sql = "SELECT 
                full_name, 
                email, 
                created_at, 
                is_voice_registered 
            FROM 
                users 
            WHERE 
                id = :id 
            LIMIT 1";

    $stmt = $conn->prepare($sql);
    $stmt->bindParam(':id', $user_id, PDO::PARAM_INT);
    $stmt->execute();

    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user) {
        // Jika pengguna ditemukan, format data sesuai kebutuhan frontend
        
        // Format tanggal agar lebih mudah dibaca
        $registered_date = new DateTime($user['created_at']);
        
        $profile_data = [
            'name' => $user['full_name'],
            'email' => $user['email'],
            'registered_at' => $registered_date->format('d F Y, H:i'), // Contoh: 23 September 2025, 00:12
            'has_voice_registered' => (bool)$user['is_voice_registered'] // Konversi 0/1 menjadi true/false
        ];

        // Kirim response sukses dengan data profil
        http_response_code(200);
        echo json_encode(['success' => true, 'data' => $profile_data]);

    } else {
        // Jika pengguna dengan ID tersebut tidak ditemukan
        http_response_code(404); // Not Found
        echo json_encode(['success' => false, 'message' => 'Pengguna tidak ditemukan.']);
    }

} catch (PDOException $e) {
    // Jika terjadi error pada database
    http_response_code(500); // Internal Server Error
    echo json_encode([
        'success' => false, 
        'message' => 'Terjadi kesalahan pada server database.',
        'error' => $e->getMessage() // Hanya untuk mode development
    ]);
}

// Tutup koneksi
$conn = null;
?>