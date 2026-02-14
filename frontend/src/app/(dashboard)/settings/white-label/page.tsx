'use client';

import { useState } from 'react';

export default function WhiteLabelSettings() {
  const [branding, setBranding] = useState({
    company_name: '',
    primary_color: '#2563eb',
    secondary_color: '#1e40af',
    logo_url: '',
    favicon_url: '',
    login_background_url: '',
    custom_css: '',
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/v1/branding', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(branding),
      });
      if (res.ok) alert('Branding updated!');
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  };

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-bold mb-2">White-Label Settings</h1>
      <p className="text-muted-foreground mb-6">Customize the appearance of The Expert for your organization</p>

      <div className="space-y-6">
        {/* Company Name */}
        <div>
          <label className="block text-sm font-medium mb-1">Company Name</label>
          <input
            type="text"
            className="w-full rounded-md border px-3 py-2"
            value={branding.company_name}
            onChange={(e) => setBranding({ ...branding, company_name: e.target.value })}
            placeholder="Your Company Name"
          />
        </div>

        {/* Logo Upload */}
        <div>
          <label className="block text-sm font-medium mb-1">Logo URL</label>
          <input
            type="url"
            className="w-full rounded-md border px-3 py-2"
            value={branding.logo_url}
            onChange={(e) => setBranding({ ...branding, logo_url: e.target.value })}
            placeholder="https://example.com/logo.png"
          />
          {branding.logo_url && (
            <div className="mt-2 p-4 border rounded-md bg-muted">
              <img src={branding.logo_url} alt="Logo preview" className="h-12 object-contain" />
            </div>
          )}
        </div>

        {/* Colors */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Primary Color</label>
            <div className="flex gap-2 items-center">
              <input
                type="color"
                value={branding.primary_color}
                onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                className="w-10 h-10 rounded border cursor-pointer"
              />
              <input
                type="text"
                value={branding.primary_color}
                onChange={(e) => setBranding({ ...branding, primary_color: e.target.value })}
                className="flex-1 rounded-md border px-3 py-2"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Secondary Color</label>
            <div className="flex gap-2 items-center">
              <input
                type="color"
                value={branding.secondary_color}
                onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                className="w-10 h-10 rounded border cursor-pointer"
              />
              <input
                type="text"
                value={branding.secondary_color}
                onChange={(e) => setBranding({ ...branding, secondary_color: e.target.value })}
                className="flex-1 rounded-md border px-3 py-2"
              />
            </div>
          </div>
        </div>

        {/* Preview */}
        <div>
          <label className="block text-sm font-medium mb-2">Preview</label>
          <div className="border rounded-lg overflow-hidden">
            <div className="h-12 flex items-center px-4 text-white font-semibold" style={{ backgroundColor: branding.primary_color }}>
              {branding.company_name || 'The Expert'}
            </div>
            <div className="p-4 bg-background">
              <div className="h-8 w-32 rounded" style={{ backgroundColor: branding.secondary_color, opacity: 0.3 }} />
            </div>
          </div>
        </div>

        {/* Custom CSS */}
        <div>
          <label className="block text-sm font-medium mb-1">Custom CSS (Advanced)</label>
          <textarea
            className="w-full rounded-md border px-3 py-2 font-mono text-sm"
            rows={6}
            value={branding.custom_css}
            onChange={(e) => setBranding({ ...branding, custom_css: e.target.value })}
            placeholder=":root { --custom-var: #000; }"
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Branding'}
        </button>
      </div>
    </div>
  );
}
