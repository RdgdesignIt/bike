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
$query = "SELECT DISTINCT data FROM all_superficie WHERE anno IN ($placeholders) ORDER BY data";

$stmt = $conn->prepare($query);
$types = str_repeat('s', count($anni));

// bind_param con riferimenti
$tmp = [];
foreach ($anni as $k => $v) {
  $tmp[$k] = &$anni[$k];
}
array_unshift($tmp, $types);
call_user_func_array([$stmt, 'bind_param'], $tmp);

$stmt->execute();
$result = $stmt->get_result();

$date = [];
while ($row = $result->fetch_assoc()) {
  $date[] = $row['data'];
}

echo json_encode($date);
