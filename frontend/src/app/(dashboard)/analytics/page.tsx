"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { BarChart3, Users, TrendingUp, Clock } from "lucide-react";

interface StatsData {
  total_queries: number;
  active_users: number;
  queries_per_day: { date: string; queries: number }[];
  by_department: { department: string; queries: number }[];
}

interface AIPerformanceData {
  avg_latency_ms: number;
  confidence_trend: { date: string; avg_confidence: number }[];
  total_tokens_input: number;
  total_tokens_output: number;
}

function StatCard({ title, value, icon: Icon, description }: { title: string; value: string | number; icon: any; description?: string }) {
  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {description && <p className="text-xs text-gray-400 mt-1">{description}</p>}
        </div>
        <div className="h-12 w-12 rounded-lg bg-blue-50 flex items-center justify-center">
          <Icon className="h-6 w-6 text-blue-600" />
        </div>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [aiPerf, setAiPerf] = useState<AIPerformanceData | null>(null);

  useEffect(() => {
    api.get("/analytics/usage").then((res) => setStats(res.data)).catch(() => {});
    api.get("/analytics/ai-performance").then((res) => setAiPerf(res.data)).catch(() => {});
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Analytics</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard title="Total Queries" value={stats?.total_queries ?? 0} icon={BarChart3} />
        <StatCard title="Active Users" value={stats?.active_users ?? 0} icon={Users} />
        <StatCard title="Avg Latency" value={`${Math.round(aiPerf?.avg_latency_ms ?? 0)}ms`} icon={Clock} />
        <StatCard title="Total Tokens" value={(aiPerf?.total_tokens_input ?? 0) + (aiPerf?.total_tokens_output ?? 0)} icon={TrendingUp} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border p-6">
          <h3 className="font-medium mb-4">Queries per Day</h3>
          <div className="space-y-2">
            {stats?.queries_per_day?.slice(-14).map((d) => (
              <div key={d.date} className="flex items-center gap-3 text-sm">
                <span className="w-24 text-gray-500">{d.date}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4">
                  <div
                    className="bg-blue-500 rounded-full h-4"
                    style={{
                      width: `${Math.min(100, (d.queries / Math.max(...(stats?.queries_per_day?.map((x) => x.queries) || [1]))) * 100)}%`,
                    }}
                  />
                </div>
                <span className="w-8 text-right font-medium">{d.queries}</span>
              </div>
            ))}
            {(!stats?.queries_per_day || stats.queries_per_day.length === 0) && (
              <p className="text-gray-400 text-center py-4">No data yet</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl border p-6">
          <h3 className="font-medium mb-4">By Department</h3>
          <div className="space-y-3">
            {stats?.by_department?.map((d) => (
              <div key={d.department} className="flex items-center justify-between text-sm">
                <span>{d.department}</span>
                <span className="font-medium">{d.queries} queries</span>
              </div>
            ))}
            {(!stats?.by_department || stats.by_department.length === 0) && (
              <p className="text-gray-400 text-center py-4">No data yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
