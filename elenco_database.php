


<?php
$servername = "localhost:3308";
$username = "root";
$password = "";
$dbname = "bike"; // Usa il nome del tuo database

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connessione fallita: " . $conn->connect_error);
}

// Recupera i parametri di filtro dalla query string
$filtro = isset($_GET['filtro']) ? $_GET['filtro'] : '';
$valoreFiltro = isset($_GET['valoreFiltro']) ? $_GET['valoreFiltro'] : '';

// Inizia la query di base
$sql = "SELECT id, data, velocita, Sellino, Manubrio FROM all_csv";

// Se un filtro è stato selezionato, aggiungi una clausola WHERE
if ($filtro != '' && $valoreFiltro != '') {
    $sql .= " WHERE $filtro LIKE '%" . $conn->real_escape_string($valoreFiltro) . "%'";
}

$result = $conn->query($sql);

if ($result->num_rows > 0) {
    while ($row = $result->fetch_assoc()) {
        echo "<tr>
                <td>" . htmlspecialchars($row['id']) . "</td>
                <td>" . htmlspecialchars($row['data']) . "</td>
                <td>" . htmlspecialchars($row['velocita']) . "</td>
                <td>" . htmlspecialchars($row['Sellino']) . "</td>
                <td>" . htmlspecialchars($row['Manubrio']) . "</td>
                <td><button class='btn btn-danger' onclick='deleteBici(" . $row['id'] . ")'>Elimina</button></td>
              </tr>";
    }
} else {
    echo "<tr><td colspan='6' class='text-center'>Nessuna bici trovata</td></tr>";
}

$conn->close();
?>
