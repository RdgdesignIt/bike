

<?php
header('Content-Type: application/json');

$servername = "localhost:3308";
$user = "root";
$password = ""; // Assicurati che sia corretto
$dbname = "bike";

$conn = new mysqli($servername, $user, $password, $dbname);

if ($conn->connect_error) {
    die(json_encode(["error" => "Connessione fallita: " . $conn->connect_error]));
}

$sql = "SELECT id, data, velocita, Sellino, Manubrio FROM all_superficie";
$result = $conn->query($sql);

$data = [];

if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
}

echo json_encode(["data" => $data]);

$conn->close();
?>
