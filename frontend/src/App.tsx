import { useEffect, useState } from "react";
import { FilterBar } from "./components/FilterBar";
import { KpiCards } from "./components/KpiCards";
import { CategoryBarChart, ChannelBarChart, RegionPieChart, RevenueLineChart } from "./components/Charts";
import { AcessePeloHub } from "./components/AcessePeloHub";
import { Filters, FilterOptions, Summary, getFilterOptions, getSummary } from "./lib/api";
import { precisaEntrarPeloHub } from "./lib/hub";

export default function App() {
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [filters, setFilters] = useState<Filters>({});
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [semLogin, setSemLogin] = useState(false); // API respondeu 401 (AUTH_MODE=hub)

  useEffect(() => {
    getFilterOptions()
      .then(setOptions)
      .catch((e) => (precisaEntrarPeloHub(e) ? setSemLogin(true) : setError("Não consegui carregar os filtros. A API tá de pé?")));
  }, []);

  useEffect(() => {
    setLoading(true);
    getSummary(filters)
      .then(setSummary)
      .catch((e) => (precisaEntrarPeloHub(e) ? setSemLogin(true) : setError("Não consegui carregar os indicadores. A API tá de pé?")))
      .finally(() => setLoading(false));
  }, [filters]);

  if (semLogin) {
    return (
      <div className="app">
        <AcessePeloHub />
      </div>
    );
  }

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
