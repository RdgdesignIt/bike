$(document).ready(function () {
  function getFilteredData() {
    if (typeof window.table === 'undefined') {
      alert("⏳ La tabella non è ancora pronta.");
      return null;
    }
    return window.table.rows({ search: 'applied' }).data().toArray();
  }

  $('#exportExcel').on('click', function () {
    const filteredData = getFilteredData();
    if (!filteredData || filteredData.length === 0) {
      alert("⚠️ Nessun dato da esportare.");
      return;
    }

    const headers = ['Data', 'ID', 'Anno', 'Velocità', 'Luogo', 'Superficie', 'Sellino', 'Manubrio', 'Diff % M/S'];
    const rows = filteredData.map(row => {
      const s = parseFloat(row.sellino);
      const m = parseFloat(row.manubrio);
      const diff = (s && m) ? (((m - s) / s) * 100).toFixed(2) + '%' : 'N/D';
      return [row.data, row.id, row.anno, row.velocita, row.luogo, row.superficie, row.sellino, row.manubrio, diff];
    });

    const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Dati Bicicletta');
    XLSX.writeFile(wb, 'dati_bike_filtrati.xlsx');
  });

  $('#exportCSV').on('click', function () {
    const filteredData = getFilteredData();
    if (!filteredData || filteredData.length === 0) {
      alert("⚠️ Nessun dato da esportare.");
      return;
    }

    const headers = ['Data', 'ID', 'Anno', 'Velocità', 'Sellino', 'Manubrio', 'Diff Percentuale'];
    const rows = filteredData.map(row => {
      const s = parseFloat(row.sellino);
      const m = parseFloat(row.manubrio);
      const diff = (s && m) ? (((m - s) / s) * 100).toFixed(2) + '%' : 'N/D';
      return [row.data, row.id, row.anno, row.velocita, row.sellino, row.manubrio, diff];
    });

    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'dati_filtrati.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  $('#downloadChart').on('click', function () {
    const canvas = document.getElementById('bikeChart');
    if (!canvas) {
      alert("❌ Grafico non trovato.");
      return;
    }
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = 'grafico_bike.png';
    link.click();
  });
});
