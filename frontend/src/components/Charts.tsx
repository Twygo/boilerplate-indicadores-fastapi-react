import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SeriesPoint } from "../lib/api";

const COLORS = ["#4f46e5", "#059669", "#d97706", "#dc2626", "#0891b2", "#7c3aed"];

export function RevenueLineChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ChartCard title="Receita por mês">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="revenue" stroke="#4f46e5" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function CategoryBarChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ChartCard title="Receita por categoria">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="revenue" fill="#059669" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function RegionPieChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ChartCard title="Receita por região">
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Tooltip />
          <Pie data={data} dataKey="revenue" nameKey="label" outerRadius={100} label>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function ChannelBarChart({ data }: { data: SeriesPoint[] }) {
  return (
    <ChartCard title="Unidades por canal">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="label" type="category" width={100} />
          <Tooltip />
          <Bar dataKey="units" fill="#d97706" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="chart-card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}
