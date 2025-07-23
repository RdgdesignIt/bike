<?php
$host = "127.0.0.1";
$user = 'root';
$pass = '';
$dbname = 'bike';
$port = 3308;

$conn = new mysqli($host, $user, $pass, $dbname, $port);
header('Content-Type: application/json');

$anni = isset($_GET['anno']) ? explode(',', $_GET['anno']) : [];

if (empty($anni)) {
  echo json_encode([]);
  exit;
}

$placeholders = implode(',', array_fill(0, count($anni), '?'));
$query = "SELECT DISTINCT id FROM all_superficie WHERE anno IN ($placeholders) ORDER BY id";

$stmt = $conn->prepare($query);

$types = str_repeat('s', count($anni));
$stmt->bind_param($types, ...$anni);
$stmt->execute();
$result = $stmt->get_result();

$ids = [];
while ($row = $result->fetch_assoc()) {
  $ids[] = $row['id'];
}

echo json_encode($ids);
