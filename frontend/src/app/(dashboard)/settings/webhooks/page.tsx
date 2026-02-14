'use client';

import { useState } from 'react';

interface WebhookItem {
  id: string;
  url: string;
  events: string[];
  status: string;
}

const EVENT_OPTIONS = [
  'query.created', 'query.completed', 'approval.needed', 'approval.completed',
  'knowledge.uploaded', 'knowledge.indexed', 'user.created', 'user.deleted',
];

export default function WebhookSettings() {
  const [webhooks, setWebhooks] = useState<WebhookItem[]>([
    { id: '1', url: 'https://hooks.slack.com/services/xxx', events: ['approval.needed'], status: 'active' },
  ]);
  const [showForm, setShowForm] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);

  const addWebhook = () => {
    if (!newUrl) return;
    setWebhooks([...webhooks, {
      id: String(Date.now()),
      url: newUrl,
      events: selectedEvents,
      status: 'active',
    }]);
    setNewUrl('');
    setSelectedEvents([]);
    setShowForm(false);
  };

  const removeWebhook = (id: string) => {
    setWebhooks(webhooks.filter((w) => w.id !== id));
  };

  return (
    <div className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Webhooks</h1>
          <p className="text-muted-foreground">Configure event notifications to external services</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Add Webhook
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded-lg border bg-card p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Endpoint URL</label>
            <input
              type="url"
              className="w-full rounded-md border px-3 py-2"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              placeholder="https://your-server.com/webhook"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Events</label>
            <div className="grid grid-cols-2 gap-2">
              {EVENT_OPTIONS.map((event) => (
                <label key={event} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedEvents.includes(event)}
                    onChange={(e) => {
                      if (e.target.checked) setSelectedEvents([...selectedEvents, event]);
                      else setSelectedEvents(selectedEvents.filter((ev) => ev !== event));
                    }}
                  />
                  {event}
                </label>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={addWebhook} className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm">Create</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 border rounded-md text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {webhooks.map((wh) => (
          <div key={wh.id} className="rounded-lg border bg-card p-4 flex items-center justify-between">
            <div>
              <p className="font-medium text-sm font-mono">{wh.url}</p>
              <div className="flex gap-1 mt-1 flex-wrap">
                {wh.events.map((ev) => (
                  <span key={ev} className="text-xs bg-muted px-2 py-0.5 rounded">{ev}</span>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">{wh.status}</span>
              <button onClick={() => removeWebhook(wh.id)} className="text-sm text-red-600 hover:underline">Delete</button>
            </div>
          </div>
        ))}
        {webhooks.length === 0 && (
          <p className="text-center text-muted-foreground py-8">No webhooks configured</p>
        )}
      </div>
    </div>
  );
}
