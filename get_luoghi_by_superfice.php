<?php
$host = "127.0.0.1";
$user = "root";
$pass = "";
$dbname = "bike";
$port = 3308;

$conn = new mysqli($host, $user, $pass, $dbname, $port);
header('Content-Type: application/json');

$superficie = isset($_GET['superficie']) ? explode(',', $_GET['superficie']) : [];

if (empty($superficie)) {
  echo json_encode([]);
  exit;
}

$placeholders = implode(',', array_fill(0, count($superficie), '?'));
$stmt = $conn->prepare("SELECT DISTINCT luogo FROM all_superficie WHERE superficie IN ($placeholders)");
$types = str_repeat('s', count($superficie));
$stmt->bind_param($types, ...$superficie);
$stmt->execute();
$result = $stmt->get_result();

$anni = [];
while ($row = $result->fetch_assoc()) {
  $anni[] = $row['anno'];
}

echo json_encode($anni);
