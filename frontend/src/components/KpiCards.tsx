import { Summary } from "../lib/api";

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function KpiCards({ summary }: { summary: Summary }) {
  const cards = [
    { label: "Receita total", value: currency.format(summary.total_revenue) },
    { label: "Unidades vendidas", value: summary.total_units.toLocaleString("pt-BR") },
    { label: "Nº de vendas", value: summary.total_sales.toLocaleString("pt-BR") },
    { label: "Ticket médio", value: currency.format(summary.average_ticket) },
  ];

  return (
    <div className="kpi-grid">
      {cards.map((c) => (
        <div className="kpi-card" key={c.label}>
          <span className="kpi-label">{c.label}</span>
          <span className="kpi-value">{c.value}</span>
        </div>
      ))}
    </div>
  );
}
