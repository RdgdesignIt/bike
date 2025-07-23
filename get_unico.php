<?php
header('Content-Type: application/json');

// Configurazione DB
$conn = new mysqli('127.0.0.1', 'root', '', 'bike', 3308);
if ($conn->connect_error) {
  echo json_encode(["error" => "Errore connessione DB"]);
  exit;
}

// Parametri GET
$campo = $_GET['campo'] ?? null;
$filtra = $_GET['filtro'] ?? null;         // es: 'superficie'
$valori = $_GET['valori'] ?? null;         // es: 'sterrato,asfalto'

if (!$campo || ($filtra && !$valori)) {
  echo json_encode([]);
  exit;
}

$valoriArray = $valori ? explode(',', $valori) : [];
$placeholders = implode(',', array_fill(0, count($valoriArray), '?'));

// Costruzione query
$query = "SELECT DISTINCT `$campo` FROM all_superficie";
$params = [];
$types = '';

if ($filtra && !empty($valoriArray)) {
  $query .= " WHERE `$filtra` IN ($placeholders)";
  $params = $valoriArray;
  $types = str_repeat('s', count($valoriArray));
}

$query .= " ORDER BY `$campo`";

$stmt = $conn->prepare($query);
if ($filtra && !empty($params)) {
  $stmt->bind_param($types, ...$params);
}
$stmt->execute();
$res = $stmt->get_result();

$out = [];
while ($row = $res->fetch_assoc()) {
  $out[] = $row[$campo];
}

echo json_encode($out);
