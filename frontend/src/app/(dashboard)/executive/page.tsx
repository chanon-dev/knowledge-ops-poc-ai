'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#0891b2'];

export default function ExecutiveDashboard() {
  const [usage, setUsage] = useState<any>(null);
  const [aiPerf, setAiPerf] = useState<any>(null);
  const [productivity, setProductivity] = useState<any>(null);
  const [topics, setTopics] = useState<any[]>([]);

  useEffect(() => {
    // In production, fetch from API
    setUsage({
      total_queries: 12450,
      active_users: 89,
      queries_per_day: Array.from({ length: 30 }, (_, i) => ({
        date: `2026-01-${String(i + 1).padStart(2, '0')}`,
        queries: Math.floor(Math.random() * 500 + 200),
      })),
      by_department: [
        { department: 'IT Operations', queries: 4500 },
        { department: 'HR', queries: 3200 },
        { department: 'Legal', queries: 2100 },
        { department: 'Finance', queries: 2650 },
      ],
    });
    setAiPerf({
      avg_latency_ms: 1420,
      drift_detected: false,
      confidence_trend: Array.from({ length: 14 }, (_, i) => ({
        date: `2026-01-${String(i + 1).padStart(2, '0')}`,
        avg_confidence: 0.82 + Math.random() * 0.1,
      })),
    });
    setProductivity({
      self_service_rate: 87.3,
      time_saved_hours: 312,
      total_queries: 12450,
      escalated_queries: 1584,
    });
    setTopics([
      { topic: 'vpn', count: 234 }, { topic: 'password', count: 189 },
      { topic: 'deployment', count: 156 }, { topic: 'kubernetes', count: 134 },
      { topic: 'database', count: 98 },
    ]);
  }, []);

  if (!usage) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Executive Dashboard</h1>
        <p className="text-muted-foreground">C-level summary of The Expert platform performance</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Queries', value: usage.total_queries.toLocaleString(), change: '+12%' },
          { label: 'Active Users', value: usage.active_users, change: '+8%' },
          { label: 'Self-Service Rate', value: `${productivity?.self_service_rate}%`, change: '+3%' },
          { label: 'Time Saved', value: `${productivity?.time_saved_hours}h`, change: '+15%' },
        ].map((kpi) => (
          <div key={kpi.label} className="rounded-lg border bg-card p-6">
            <p className="text-sm text-muted-foreground">{kpi.label}</p>
            <div className="flex items-baseline gap-2 mt-1">
              <p className="text-3xl font-bold">{kpi.value}</p>
              <span className="text-sm text-green-600">{kpi.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queries Over Time */}
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold mb-4">Queries Per Day</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={usage.queries_per_day}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="queries" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Department Breakdown */}
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold mb-4">Queries by Department</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={usage.by_department} dataKey="queries" nameKey="department" cx="50%" cy="50%" outerRadius={100} label>
                {usage.by_department.map((_: any, idx: number) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Performance + Top Topics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold mb-4">AI Confidence Trend</h3>
          {aiPerf?.drift_detected && (
            <div className="mb-2 p-2 bg-yellow-100 text-yellow-800 text-sm rounded">Model drift detected</div>
          )}
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={aiPerf?.confidence_trend || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis domain={[0.5, 1]} />
              <Tooltip />
              <Line type="monotone" dataKey="avg_confidence" stroke="#16a34a" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold mb-4">Top Queried Topics</h3>
          <div className="space-y-3">
            {topics.map((topic, idx) => (
              <div key={topic.topic} className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground w-4">{idx + 1}</span>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="font-medium">{topic.topic}</span>
                    <span className="text-sm text-muted-foreground">{topic.count}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${(topic.count / topics[0].count) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Avg Latency */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Average Response Time</p>
            <p className="text-2xl font-bold">{aiPerf?.avg_latency_ms}ms</p>
          </div>
          <div className={`text-sm px-3 py-1 rounded-full ${(aiPerf?.avg_latency_ms || 0) < 3000 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {(aiPerf?.avg_latency_ms || 0) < 3000 ? 'Within SLA' : 'Above SLA'}
          </div>
        </div>
      </div>
    </div>
  );
}
