<?php
$host = "127.0.0.1";
$user = "root";
$pass = "";
$dbname = "bike";
$port = 3308;

$conn = new mysqli($host, $user, $pass, $dbname, $port);
header('Content-Type: application/json');

$superfice = isset($_GET['superfice']) ? explode(',', $_GET['superfice']) : [];

if (empty($superfice)) {
  echo json_encode([]);
  exit;
}

$placeholders = implode(',', array_fill(0, count($superfice), '?'));
$stmt = $conn->prepare("SELECT DISTINCT anno FROM superficie WHERE superfice IN ($placeholders)");
$types = str_repeat('s', count($superfice));
$stmt->bind_param($types, ...$superfice);
$stmt->execute();
$result = $stmt->get_result();

$anni = [];
while ($row = $result->fetch_assoc()) {
  $anni[] = $row['anno'];
}

echo json_encode($anni);
