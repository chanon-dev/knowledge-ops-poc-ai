'use client';

import { useState } from 'react';

const PLUGINS = [
  {
    name: 'log-parser',
    version: '1.0.0',
    description: 'Parse and analyze common log formats (Apache, Nginx, syslog)',
    icon: '📋',
    installed: true,
    category: 'Analysis',
  },
  {
    name: 'config-validator',
    version: '1.0.0',
    description: 'Validate YAML/JSON configuration files for errors and security issues',
    icon: '✅',
    installed: true,
    category: 'Validation',
  },
  {
    name: 'incident-report',
    version: '1.0.0',
    description: 'Auto-generate structured incident reports from resolution data',
    icon: '📝',
    installed: true,
    category: 'Reporting',
  },
  {
    name: 'jira-integration',
    version: '1.0.0',
    description: 'Create and manage Jira tickets from escalated queries',
    icon: '🔗',
    installed: false,
    category: 'Integration',
  },
  {
    name: 'slack-notifier',
    version: '1.0.0',
    description: 'Send approval notifications and query results to Slack channels',
    icon: '💬',
    installed: false,
    category: 'Integration',
  },
];

export default function MarketplacePage() {
  const [plugins, setPlugins] = useState(PLUGINS);
  const [filter, setFilter] = useState<string>('all');

  const categories = ['all', ...Array.from(new Set(plugins.map((p) => p.category)))];
  const filtered = filter === 'all' ? plugins : plugins.filter((p) => p.category === filter);

  const toggleInstall = (name: string) => {
    setPlugins(plugins.map((p) =>
      p.name === name ? { ...p, installed: !p.installed } : p
    ));
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Plugin Marketplace</h1>
        <p className="text-muted-foreground">Browse and install plugins to extend KnowledgeOps</p>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 mb-6">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 rounded-md text-sm capitalize ${
              filter === cat ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Plugin Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((plugin) => (
          <div key={plugin.name} className="rounded-lg border bg-card p-6 flex flex-col">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{plugin.icon}</span>
                <div>
                  <h3 className="font-semibold">{plugin.name}</h3>
                  <p className="text-xs text-muted-foreground">v{plugin.version}</p>
                </div>
              </div>
              <span className="text-xs bg-muted px-2 py-0.5 rounded">{plugin.category}</span>
            </div>

            <p className="text-sm text-muted-foreground flex-1 mb-4">{plugin.description}</p>

            <button
              onClick={() => toggleInstall(plugin.name)}
              className={`w-full py-2 rounded-md text-sm font-medium ${
                plugin.installed
                  ? 'border text-red-600 hover:bg-red-50'
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              }`}
            >
              {plugin.installed ? 'Uninstall' : 'Install'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
