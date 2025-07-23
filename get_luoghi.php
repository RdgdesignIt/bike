<?php
$host = "127.0.0.1";
$user = "root";
$pass = "";
$dbname = "bike";
$port = 3308;

$conn = new mysqli($host, $user, $pass, $dbname, $port);
header('Content-Type: application/json');

$query = "SELECT DISTINCT luogo FROM all_superficie ORDER BY luogo";
$result = $conn->query($query);

$luoghi = [];
while ($row = $result->fetch_assoc()) {
  $luoghi[] = $row['luogo'];
}

echo json_encode($luoghi);
