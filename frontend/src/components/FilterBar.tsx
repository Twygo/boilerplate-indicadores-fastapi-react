import { FilterOptions, Filters } from "../lib/api";

type Props = {
  options: FilterOptions | null;
  filters: Filters;
  onChange: (filters: Filters) => void;
};

export function FilterBar({ options, filters, onChange }: Props) {
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch });

  return (
    <div className="filter-bar">
      <label>
        De
        <input
          type="date"
          value={filters.date_from ?? ""}
          min={options?.date_min ?? undefined}
          max={options?.date_max ?? undefined}
          onChange={(e) => set({ date_from: e.target.value || undefined })}
        />
      </label>
      <label>
        Até
        <input
          type="date"
          value={filters.date_to ?? ""}
          min={options?.date_min ?? undefined}
          max={options?.date_max ?? undefined}
          onChange={(e) => set({ date_to: e.target.value || undefined })}
        />
      </label>
      <label>
        Categoria
        <select value={filters.category ?? ""} onChange={(e) => set({ category: e.target.value || undefined })}>
          <option value="">Todas</option>
          {options?.categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </label>
      <label>
        Região
        <select value={filters.region ?? ""} onChange={(e) => set({ region: e.target.value || undefined })}>
          <option value="">Todas</option>
          {options?.regions.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </label>
      <label>
        Canal
        <select value={filters.channel ?? ""} onChange={(e) => set({ channel: e.target.value || undefined })}>
          <option value="">Todos</option>
          {options?.channels.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </label>
      <button type="button" onClick={() => onChange({})}>Limpar filtros</button>
    </div>
  );
}
