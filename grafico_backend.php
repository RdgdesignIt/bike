<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

header('Content-Type: application/json');

// Connessione DB
$host = "127.0.0.1";
$user = "root";
$pass = "";
$dbname = "bike";
$port = 3308;

$conn = new mysqli($host, $user, $pass, $dbname, $port);
if ($conn->connect_error) {
  echo json_encode(["error" => $conn->connect_error]);
  exit;
}

// Parametri GET
$dates      = isset($_GET['date']) && $_GET['date'] !== '' ? explode(',', $_GET['date']) : [];
$anno       = isset($_GET['anno']) && $_GET['anno'] !== '' ? explode(',', $_GET['anno']) : [];
$id         = isset($_GET['id']) && $_GET['id'] !== '' ? explode(',', $_GET['id']) : [];
$velocita   = isset($_GET['velocita']) && $_GET['velocita'] !== '' ? explode(',', $_GET['velocita']) : [];
$luogo      = isset($_GET['luogo']) && $_GET['luogo'] !== '' ? explode(',', $_GET['luogo']) : [];
$superficie = isset($_GET['superficie']) && $_GET['superficie'] !== '' ? explode(',', $_GET['superficie']) : [];
$bmi_fascia = isset($_GET['bmi']) && $_GET['bmi'] !== '' ? explode(',', $_GET['bmi']) : [];

// Query base
$sql = "SELECT 
  all_superficie.id,
  all_superficie.data,
  all_superficie.anno,
  all_superficie.velocita,
  all_superficie.luogo,
  all_superficie.superficie,
  all_superficie.sellino,
  all_superficie.manubrio,
  anagrafica.bmi,
  CASE
    WHEN anagrafica.bmi < 18.5 THEN 'Sottopeso'
    WHEN anagrafica.bmi < 25 THEN 'Normopeso'
    ELSE 'Sovrappeso'
  END AS bmi_fascia
FROM all_superficie
JOIN anagrafica ON all_superficie.id = anagrafica.id
WHERE 1=1";

$params = [];
$types = "";

// Funzione riutilizzabile
function aggiungiFiltro($valori, $campo, &$sql, &$params, &$types) {
  if (!empty($valori)) {
    $segnaposti = implode(',', array_fill(0, count($valori), '?'));
    $sql .= " AND $campo IN ($segnaposti)";
    $params = array_merge($params, $valori);
    $types .= str_repeat('s', count($valori));
  }
}

// Filtri dinamici
aggiungiFiltro($dates,      'data',        $sql, $params, $types);
aggiungiFiltro($anno,       'anno',        $sql, $params, $types);
aggiungiFiltro($id,         'all_superficie.id', $sql, $params, $types);
aggiungiFiltro($velocita,   'velocita',    $sql, $params, $types);
aggiungiFiltro($luogo,      'luogo',       $sql, $params, $types);
aggiungiFiltro($superficie, 'superficie',  $sql, $params, $types);

if (!empty($superficie)) {
  $sql .= " AND superficie IN (" . implode(',', array_fill(0, count($superficie), '?')) . ")";
  foreach ($superficie as $s) {
    $params[] = $s;
    $types .= "s";
  }
}


// Filtro BMI (fasce)
if (!empty($bmi_fascia)) {
  $segni = implode(',', array_fill(0, count($bmi_fascia), '?'));
  $sql .= " AND (CASE
                  WHEN anagrafica.bmi < 18.5 THEN 'Sottopeso'
                  WHEN anagrafica.bmi < 25 THEN 'Normopeso'
                  ELSE 'Sovrappeso'
                END) IN ($segni)";
  $params = array_merge($params, $bmi_fascia);
  $types .= str_repeat('s', count($bmi_fascia));
}

// Ordine finale
$sql .= " ORDER BY all_superficie.id";

// Debug logging
error_log("❖ Query finale: $sql");
error_log("❖ Parametri: " . implode(', ', $params));
error_log("Superficie GET: " . $_GET['superficie']);

// Esecuzione
$stmt = $conn->prepare($sql);
if (!$stmt) {
  echo json_encode(["error" => $conn->error]);
  exit;
}

if (!empty($params)) {
  $refs = [];
  foreach ($params as $i => $v) {
    $refs[$i] = &$params[$i];
  }
  array_unshift($refs, $types);
  call_user_func_array([$stmt, 'bind_param'], $refs);
}

$stmt->execute();
$result = $stmt->get_result();
$data = [];

while ($row = $result->fetch_assoc()) {
  $data[] = $row;
}

echo json_encode($data);
$stmt->close();
$conn->close();
