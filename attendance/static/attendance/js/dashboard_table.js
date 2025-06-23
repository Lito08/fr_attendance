document.addEventListener("DOMContentLoaded", () => {
  const table = document.querySelector("#logTable");
  if (!table) return;
  // Simple-DataTables with Bootstrap 5 styling
  new simpleDatatables.DataTable(table, {
    perPageSelect: [5, 10, 25],
    perPage: 5,
    searchable: true,
    labels: { placeholder: "🔍 Search…" }
  });
});
