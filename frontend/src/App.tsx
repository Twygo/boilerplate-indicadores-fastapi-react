import { useEffect, useState } from "react";
import { FilterBar } from "./components/FilterBar";
import { KpiCards } from "./components/KpiCards";
import { CategoryBarChart, ChannelBarChart, RegionPieChart, RevenueLineChart } from "./components/Charts";
import { Filters, FilterOptions, Summary, getFilterOptions, getSummary } from "./lib/api";

export default function App() {
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [filters, setFilters] = useState<Filters>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getFilterOptions().then(setOptions).catch(() => setError("Não consegui carregar os filtros. A API tá de pé?"));
  }, []);

  useEffect(() => {
    setLoading(true);
    getSummary(filters)
      .then(setSummary)
      .catch(() => setError("Não consegui carregar os indicadores. A API tá de pé?"))
      .finally(() => setLoading(false));
  }, [filters]);

  return (
    <div className="app">
      <header>
        <h1>📊 Indicadores</h1>
        <p>Boilerplate FastAPI + React + Postgres — troque os dados/gráficos como quiser.</p>
      </header>

      <FilterBar options={options} filters={filters} onChange={setFilters} />

      {error && <p className="error">{error}</p>}
      {loading && !summary && <p>Carregando...</p>}

      {summary && (
        <>
          <KpiCards summary={summary} />
          <div className="chart-grid">
            <RevenueLineChart data={summary.by_month} />
            <CategoryBarChart data={summary.by_category} />
            <RegionPieChart data={summary.by_region} />
            <ChannelBarChart data={summary.by_channel} />
          </div>
        </>
      )}
    </div>
  );
}
