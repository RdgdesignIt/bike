<?php
// Connessione al database
$host = "127.0.0.1";
$user = 'root';
$pass = '';
$db = 'bike';
$port = 3308;

//$conn = new mysqli($host, $user, $pass, $dbname, $port);
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db; port=$port; charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);

    // Query per unire le due tabelle
    $stmt = $pdo->query("
        SELECT 
            s.Data,
            s.Luogo,
            s.Superfice,
            s.ID,
            s.Anno,
            s.Velocita,
            s.Sellino,
            s.Manubrio,
            s.`Diff Percentuale`,
            a.Altezza,
            a.Peso
        FROM 
            all_superficie s a ON s.ID = a.ID
    ");

    $results = $stmt->fetchAll();

    // Imposta l'header per il download JSON
    header('Content-Type: application/json');
    header('Content-Disposition: attachment; filename="dati_bici.json"');

    echo json_encode($results, JSON_PRETTY_PRINT);

} catch (PDOException $e) {
    echo "Errore: " . $e->getMessage();
}
?>
