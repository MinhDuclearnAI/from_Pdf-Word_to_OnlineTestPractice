import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

interface ScoreDistributionChartProps {
  data: Array<{ score: number; count: number }>;
}

export const ScoreDistributionChart: React.FC<ScoreDistributionChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-900/10 border border-slate-800 rounded-xl">
        <p className="text-slate-400 text-sm">Chưa có đủ dữ liệu để hiển thị biểu đồ phổ điểm.</p>
      </div>
    );
  }

  // Sort by score ascendingly
  const sortedData = [...data].sort((a, b) => a.score - b.score);

  return (
    <div className="w-full h-80 bg-slate-900/40 p-4 border border-slate-800 rounded-xl">
      <h3 className="text-sm font-semibold text-slate-350 mb-4">Biểu đồ phổ điểm lớp học</h3>
      <ResponsiveContainer width="100%" height="80%">
        <BarChart data={sortedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="score" stroke="#94a3b8" fontSize={12} />
          <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#0b0f19", borderColor: "#1e293b", color: "#f8fafc" }}
            cursor={{ fill: "rgba(59, 110, 255, 0.05)" }}
          />
          <Bar dataKey="count" name="Số học sinh" fill="#3b6eff" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
export default ScoreDistributionChart;
