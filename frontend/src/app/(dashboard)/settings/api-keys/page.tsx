"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Plus, Copy, Trash2 } from "lucide-react";

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  status: string;
  last_used_at: string | null;
  created_at: string;
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  useEffect(() => { loadKeys(); }, []);

  const loadKeys = async () => {
    try {
      const res = await api.get("/api-keys");
      setKeys(res.data.data || []);
    } catch {}
  };

  const handleCreate = async () => {
    try {
      const res = await api.post("/api-keys", { name: newKeyName });
      setGeneratedKey(res.data.raw_key);
      setNewKeyName("");
      loadKeys();
    } catch {}
  };

  const handleRevoke = async (id: string) => {
    if (!confirm("Revoke this API key?")) return;
    try {
      await api.delete(`/api-keys/${id}`);
      loadKeys();
    } catch {}
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">API Keys</h2>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
          <Plus className="h-4 w-4" /> Generate Key
        </button>
      </div>

      {generatedKey && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
          <p className="text-sm font-medium text-green-800 mb-2">API Key Generated (copy now - it won&apos;t be shown again):</p>
          <div className="flex items-center gap-2">
            <code className="flex-1 bg-white px-3 py-2 rounded border text-sm font-mono">{generatedKey}</code>
            <button onClick={() => navigator.clipboard.writeText(generatedKey)} className="p-2 hover:bg-green-100 rounded-lg">
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <button onClick={() => setGeneratedKey(null)} className="text-sm text-green-600 mt-2">Dismiss</button>
        </div>
      )}

      {showCreate && !generatedKey && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <input placeholder="Key name" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} className="border rounded-lg px-3 py-2 text-sm w-full mb-3" />
          <div className="flex gap-2">
            <button onClick={handleCreate} disabled={!newKeyName.trim()} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50">Generate</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-gray-100 rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 text-left text-sm text-gray-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Key</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last Used</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y text-sm">
            {keys.map((key) => (
              <tr key={key.id}>
                <td className="px-4 py-3 font-medium">{key.name}</td>
                <td className="px-4 py-3 font-mono text-gray-500">{key.key_prefix}...</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs ${key.status === "active" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>{key.status}</span>
                </td>
                <td className="px-4 py-3 text-gray-500">{key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : "Never"}</td>
                <td className="px-4 py-3 text-gray-500">{new Date(key.created_at).toLocaleDateString()}</td>
                <td className="px-4 py-3">
                  {key.status === "active" && (
                    <button onClick={() => handleRevoke(key.id)} className="text-red-500 hover:text-red-700"><Trash2 className="h-4 w-4" /></button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
