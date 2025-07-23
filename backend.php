<?php
// Imposta intestazioni e debug
header('Content-Type: application/json');
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Connessione al DB
$host = "127.0.0.1";
$user = 'root';      // <-- Cambia con il tuo username
$pass = '';      // <-- Cambia con la tua password
$dbname = 'bike';
$port = 3308;

// Connessione MySQLi
$conn = new mysqli($host, $user, $pass, $dbname, $port);

// Controllo connessione
if ($conn->connect_error) {
    echo json_encode(["error" => "Errore connessione DB: " . $conn->connect_error]);
    exit;
}

// Parametri GET
$anno = isset($_GET['anno']) && $_GET['anno'] !== '' ? explode(',', $_GET['anno']) : [];
$data = isset($_GET['data']) && $_GET['data'] !== '' ? explode(',', $_GET['data']) : [];
$velocita = isset($_GET['velocita']) && $_GET['velocita'] !== '' ? explode(',', $_GET['velocita']) : [];
$id = isset($_GET['id']) && $_GET['id'] !== '' ? explode(',', $_GET['id']) : [];

$luogo = isset($_GET['luogo']) && $_GET['luogo'] !== '' ? explode(',', $_GET['luogo']) : [];



$superficie = isset($_GET['superficie']) && $_GET['superficie'] !== '' ? explode(',', $_GET['superficie']) : [];
  
$bmi_fascia = isset($_GET['bmi']) && $_GET['bmi'] !== '' ? explode(',', $_GET['bmi']) : [];



// Costruzione query
// Costruzione query
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
WHERE 1=1

";
$params = [];
$types = "";

// Aggiunta condizioni
if (!empty($anno)) {
  $sql .= " AND anno IN (" . implode(',', array_fill(0, count($anno), '?')) . ")";
  $params = array_merge($params, $anno);
  $types .= str_repeat("s", count($anno));
}

if (!empty($data)) {
  $sql .= " AND data IN (" . implode(',', array_fill(0, count($data), '?')) . ")";
  $params = array_merge($params, $data);
  $types .= str_repeat("s", count($data));
}

if (!empty($velocita)) {
  $sql .= " AND velocita IN (" . implode(',', array_fill(0, count($velocita), '?')) . ")";
  $params = array_merge($params, $velocita);
  $types .= str_repeat("s", count($velocita));
}

if (!empty($id)) {
  $sql .= " AND id IN (" . implode(',', array_fill(0, count($id), '?')) . ")";
  $params = array_merge($params, $id);
  $types .= str_repeat("s", count($id));
}

if (!empty($luogo)) {
  $sql .= " AND luogo IN (" . implode(',', array_fill(0, count($luogo), '?')) . ")";
  $params = array_merge($params, $luogo);
  $types .= str_repeat("s", count($luogo));
}

if (!empty($superficie)) {
  $sql .= " AND superficie IN (" . implode(',', array_fill(0, count($superficie), '?')) . ")";
  $params = array_merge($params, $superficie);
  $types .= str_repeat("s", count($superficie));
}


if (!empty($bmi_fascia)) {
  $sql .= " AND (CASE
                    WHEN anagrafica.bmi < 18.5 THEN 'Sottopeso'
                    WHEN anagrafica.bmi < 25 THEN 'Normopeso'
                    ELSE 'Sovrappeso'
                  END) IN (" . implode(',', array_fill(0, count($bmi_fascia), '?')) . ")";
  foreach ($bmi_fascia as $fascia) {
    $params[] = $fascia;
    $types .= 's';
  }
}






$sql .= " ORDER BY all_superficie.id"; // ✅ ora è alla fine
//$sql .= " ORDER BY id";

// Prepara ed esegui query

error_log("❖ QUERY: $sql");
error_log("❖ PARAMS: " . implode(', ', $params));

$stmt = $conn->prepare($sql);

if ($params) {
    $bindParams = [];
    foreach ($params as $key => $val) {
        $bindParams[$key] = &$params[$key];
    }
    array_unshift($bindParams, $types);
    call_user_func_array([$stmt, 'bind_param'], $bindParams);
}

$stmt->execute();
$result = $stmt->get_result();

// Risultati
$data = [];
while ($row = $result->fetch_assoc()) {
  $bmi = (float)$row['bmi'];
  if ($bmi < 18.5) {
    $row['bmi_fascia'] = 'Sottopeso';
  } elseif ($bmi < 25) {
    $row['bmi_fascia'] = 'Normopeso';
  } else {
    $row['bmi_fascia'] = 'Sovrappeso';
  }
  $data[] = $row;
}


header('Content-Type: application/json');

if (json_last_error() !== JSON_ERROR_NONE) {
  error_log('Errore JSON: ' . json_last_error_msg());
}

if (!headers_sent()) {
  header('Content-Type: application/json');
}



echo json_encode(["data" => $data]);
$stmt->close();
$conn->close();

