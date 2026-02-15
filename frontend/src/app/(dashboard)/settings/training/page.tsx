'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Plus, Trash2, Pencil, Cpu, Rocket, FlaskConical, Info, Zap } from 'lucide-react';

// -----------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------

interface TrainingMethod {
  id: string;
  name: string;
  method_key: string;
  description: string | null;
  default_config: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

interface CatalogBaseModel {
  id: string;
  model_name: string;
  display_name: string;
  size_billion: number | null;
  recommended_ram_gb: number | null;
  default_target_modules: string[] | null;
  is_active: boolean;
  created_at: string;
}

interface DeploymentTarget {
  id: string;
  name: string;
  target_key: string;
  config: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

type Tab = 'methods' | 'models' | 'targets';

// -----------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------

export default function TrainingCatalogPage() {
  const [tab, setTab] = useState<Tab>('methods');

  // Data
  const [methods, setMethods] = useState<TrainingMethod[]>([]);
  const [baseModels, setBaseModels] = useState<CatalogBaseModel[]>([]);
  const [targets, setTargets] = useState<DeploymentTarget[]>([]);

  // Registry info
  const [registeredTrainers, setRegisteredTrainers] = useState<Record<string, string>>({});
  const [registeredDeployers, setRegisteredDeployers] = useState<Record<string, string>>({});

  // Forms
  const [showForm, setShowForm] = useState(false);

  // Edit state
  const [editingMethodId, setEditingMethodId] = useState<string | null>(null);
  const [editMethod, setEditMethod] = useState({ name: '', method_key: '', description: '', default_config: '{}', is_active: true });
  const [editingModelId, setEditingModelId] = useState<string | null>(null);
  const [editModel, setEditModel] = useState({ display_name: '', size_billion: '', recommended_ram_gb: '', default_target_modules: '', is_active: true });
  const [editingTargetId, setEditingTargetId] = useState<string | null>(null);
  const [editTarget, setEditTarget] = useState({ name: '', target_key: '', config: '{}', is_active: true });

  const load = useCallback(async () => {
    const [mRes, bmRes, tRes, rRes] = await Promise.allSettled([
      api.get('/training/methods'),
      api.get('/training/base-models'),
      api.get('/training/targets'),
      api.get('/training/registry'),
    ]);
    if (mRes.status === 'fulfilled') setMethods(mRes.value.data.data || []);
    if (bmRes.status === 'fulfilled') setBaseModels(bmRes.value.data.data || []);
    if (tRes.status === 'fulfilled') setTargets(tRes.value.data.data || []);
    if (rRes.status === 'fulfilled') {
      setRegisteredTrainers(rRes.value.data.trainers || {});
      setRegisteredDeployers(rRes.value.data.deployers || {});
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // -----------------------------------------------------------------------
  // CRUD helpers
  // -----------------------------------------------------------------------

  const handleDeleteMethod = async (id: string) => {
    try { await api.delete(`/training/methods/${id}`); load(); }
    catch { alert('Failed to delete'); }
  };

  const handleDeleteBaseModel = async (id: string) => {
    try { await api.delete(`/training/base-models/${id}`); load(); }
    catch { alert('Failed to delete'); }
  };

  const handleDeleteTarget = async (id: string) => {
    try { await api.delete(`/training/targets/${id}`); load(); }
    catch { alert('Failed to delete'); }
  };

  // -----------------------------------------------------------------------
  // Edit helpers
  // -----------------------------------------------------------------------

  const startEditMethod = (m: TrainingMethod) => {
    setEditingMethodId(m.id);
    setEditMethod({ name: m.name, method_key: m.method_key, description: m.description || '', default_config: JSON.stringify(m.default_config, null, 2), is_active: m.is_active });
  };

  const handleUpdateMethod = async () => {
    if (!editingMethodId) return;
    try {
      let parsedConfig = {};
      try { parsedConfig = JSON.parse(editMethod.default_config); } catch { /* ignore */ }
      await api.put(`/training/methods/${editingMethodId}`, {
        name: editMethod.name,
        method_key: editMethod.method_key,
        description: editMethod.description || null,
        default_config: parsedConfig,
        is_active: editMethod.is_active,
      });
      setEditingMethodId(null);
      load();
    } catch (err: any) { alert(err?.response?.data?.detail || 'Failed to update'); }
  };

  const startEditModel = (m: CatalogBaseModel) => {
    setEditingModelId(m.id);
    setEditModel({
      display_name: m.display_name,
      size_billion: m.size_billion?.toString() || '',
      recommended_ram_gb: m.recommended_ram_gb?.toString() || '',
      default_target_modules: m.default_target_modules?.join(', ') || '',
      is_active: m.is_active,
    });
  };

  const handleUpdateModel = async () => {
    if (!editingModelId) return;
    try {
      let modules: string[] | null = null;
      if (editModel.default_target_modules.trim()) {
        modules = editModel.default_target_modules.split(',').map(s => s.trim());
      }
      await api.put(`/training/base-models/${editingModelId}`, {
        display_name: editModel.display_name,
        size_billion: editModel.size_billion ? parseFloat(editModel.size_billion) : null,
        recommended_ram_gb: editModel.recommended_ram_gb ? parseFloat(editModel.recommended_ram_gb) : null,
        default_target_modules: modules,
        is_active: editModel.is_active,
      });
      setEditingModelId(null);
      load();
    } catch (err: any) { alert(err?.response?.data?.detail || 'Failed to update'); }
  };

  const startEditTarget = (t: DeploymentTarget) => {
    setEditingTargetId(t.id);
    setEditTarget({ name: t.name, target_key: t.target_key, config: JSON.stringify(t.config, null, 2), is_active: t.is_active });
  };

  const handleUpdateTarget = async () => {
    if (!editingTargetId) return;
    try {
      let parsedConfig = {};
      try { parsedConfig = JSON.parse(editTarget.config); } catch { /* ignore */ }
      await api.put(`/training/targets/${editingTargetId}`, {
        name: editTarget.name,
        target_key: editTarget.target_key,
        config: parsedConfig,
        is_active: editTarget.is_active,
      });
      setEditingTargetId(null);
      load();
    } catch (err: any) { alert(err?.response?.data?.detail || 'Failed to update'); }
  };

  // -----------------------------------------------------------------------
  // Add forms
  // -----------------------------------------------------------------------

  const [newMethod, setNewMethod] = useState({ name: 'LoRA', method_key: 'lora', description: 'Low-Rank Adaptation — fine-tune เร็ว ใช้ RAM น้อย', default_config: '{"lora_r": 16, "lora_alpha": 32, "lora_dropout": 0.05}' });
  const [newBaseModel, setNewBaseModel] = useState({ model_name: 'TinyLlama/TinyLlama-1.1B-Chat-v1.0', display_name: 'TinyLlama 1.1B Chat', size_billion: '1.1', recommended_ram_gb: '4', default_target_modules: 'q_proj,v_proj,k_proj,o_proj' });
  const [newTarget, setNewTarget] = useState({ name: 'Local Ollama', target_key: 'ollama', config: '{"temperature": 0.7, "top_p": 0.9, "num_ctx": 4096}' });
  const [quickSetupLoading, setQuickSetupLoading] = useState(false);

  const handleAddMethod = async () => {
    try {
      let parsedConfig = {};
      try { parsedConfig = JSON.parse(newMethod.default_config); } catch { /* ignore */ }
      await api.post('/training/methods', {
        name: newMethod.name,
        method_key: newMethod.method_key,
        description: newMethod.description || null,
        default_config: parsedConfig,
      });
      setShowForm(false);
      setNewMethod({ name: '', method_key: '', description: '', default_config: '{}' });
      load();

    } catch (err: any) { alert(err?.response?.data?.detail || 'Failed'); }
  };

  const handleAddBaseModel = async () => {
    try {
      let modules: string[] | null = null;
      if (newBaseModel.default_target_modules.trim()) {
        modules = newBaseModel.default_target_modules.split(',').map(s => s.trim());
      }
      await api.post('/training/base-models', {
        model_name: newBaseModel.model_name,
        display_name: newBaseModel.display_name,
        size_billion: newBaseModel.size_billion ? parseFloat(newBaseModel.size_billion) : null,
        recommended_ram_gb: newBaseModel.recommended_ram_gb ? parseFloat(newBaseModel.recommended_ram_gb) : null,
        default_target_modules: modules,
      });
      setShowForm(false);
      setNewBaseModel({ model_name: '', display_name: '', size_billion: '', recommended_ram_gb: '', default_target_modules: '' });
      load();
    } catch (err: any) { alert(err?.response?.data?.detail || 'Failed'); }
  };

  const handleAddTarget = async () => {
    try {
      let parsedConfig = {};
      try { parsedConfig = JSON.parse(newTarget.config); } catch { /* ignore */ }
      await api.post('/training/targets', {
        name: newTarget.name,
        target_key: newTarget.target_key,
        config: parsedConfig,
      });
      setShowForm(false);
      setNewTarget({ name: '', target_key: '', config: '{}' });
      load();
    } catch (err: any) { alert(err?.response?.data?.detail || 'Failed'); }
  };

  const needsSetup = methods.length === 0 && baseModels.length === 0 && targets.length === 0;

  const handleQuickSetup = async () => {
    setQuickSetupLoading(true);
    try {
      const results = await Promise.allSettled([
        api.post('/training/methods', {
          name: 'LoRA',
          method_key: 'lora',
          description: 'Low-Rank Adaptation — fine-tune เร็ว ใช้ RAM น้อย เหมาะกับโมเดลขนาดเล็ก-กลาง',
          default_config: { lora_r: 16, lora_alpha: 32, lora_dropout: 0.05 },
        }),
        api.post('/training/base-models', {
          model_name: 'TinyLlama/TinyLlama-1.1B-Chat-v1.0',
          display_name: 'TinyLlama 1.1B Chat',
          size_billion: 1.1,
          recommended_ram_gb: 4,
          default_target_modules: ['q_proj', 'v_proj', 'k_proj', 'o_proj'],
        }),
        api.post('/training/targets', {
          name: 'Local Ollama',
          target_key: 'ollama',
          config: { temperature: 0.7, top_p: 0.9, num_ctx: 4096 },
        }),
      ]);
      const failed = results.filter(r => r.status === 'rejected');
      if (failed.length > 0) {
        console.warn('Quick setup: some items failed', failed);
      }
      await load();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Quick setup failed');
    } finally {
      setQuickSetupLoading(false);
    }
  };

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'methods', label: 'Training Methods', icon: <FlaskConical className="h-4 w-4" /> },
    { key: 'models', label: 'Base Models', icon: <Cpu className="h-4 w-4" /> },
    { key: 'targets', label: 'Deployment Targets', icon: <Rocket className="h-4 w-4" /> },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Training Catalog</h1>
      <p className="text-sm text-muted-foreground mb-4">
        Manage training methods, base models, and deployment targets. Add new items here — no code changes needed.
      </p>
      <div className="flex items-start gap-2 mb-6 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md text-xs text-blue-700 dark:text-blue-300">
        <Info className="h-4 w-4 shrink-0 mt-0.5" />
        <span>
          หน้านี้ใช้จัดการ catalog สำหรับระบบ fine-tuning — ข้อมูลที่เพิ่มที่นี่จะปรากฏเป็น dropdown ในหน้า
          {' '}<a href="/settings/models" className="underline font-medium hover:text-blue-900 dark:hover:text-blue-100">Settings &gt; Models</a>
          {' '}ตอนสร้าง training job ใหม่ ต้องเพิ่มอย่างน้อย 1 รายการในแต่ละแท็บเพื่อให้ระบบ training พร้อมใช้งาน
        </span>
      </div>

      {/* Quick Setup Banner */}
      {needsSetup && (
        <div className="mb-6 rounded-lg border-2 border-dashed border-blue-300 bg-blue-50/50 dark:bg-blue-950/20 p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-sm mb-1">ยังไม่มีข้อมูล — เริ่มต้นใช้งานเลย?</h3>
              <p className="text-xs text-muted-foreground">
                กดปุ่มนี้เพื่อสร้างค่าเริ่มต้นอัตโนมัติ: LoRA method, TinyLlama 1.1B base model, และ Local Ollama deploy target
                — สามารถแก้ไขหรือเพิ่มเติมได้ทีหลัง
              </p>
            </div>
            <button
              onClick={handleQuickSetup}
              disabled={quickSetupLoading}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 shrink-0 ml-4"
            >
              <Zap className="h-4 w-4" />
              {quickSetupLoading ? 'Creating...' : 'Quick Setup'}
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setShowForm(false); }}
            className={`flex items-center gap-2 px-4 py-2 text-sm border-b-2 -mb-px transition-colors ${
              tab === t.key
                ? 'border-primary text-primary font-medium'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Add button */}
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Add {tab === 'methods' ? 'Method' : tab === 'models' ? 'Base Model' : 'Target'}
        </button>
      </div>

      {/* ---------- Add Forms ---------- */}

      {showForm && tab === 'methods' && (
        <div className="rounded-lg border bg-card p-4 mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Name — ชื่อที่แสดงใน UI</label>
              <input placeholder="e.g. LoRA" value={newMethod.name} onChange={(e) => setNewMethod({ ...newMethod, name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Method Key — trainer ที่ลงทะเบียนไว้ใน Python</label>
              {Object.keys(registeredTrainers).length > 0 ? (
                <select value={newMethod.method_key} onChange={(e) => setNewMethod({ ...newMethod, method_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm">
                  <option value="">Select registry key...</option>
                  {Object.entries(registeredTrainers).map(([key, cls]) => (
                    <option key={key} value={key}>{key} ({cls})</option>
                  ))}
                </select>
              ) : (
                <>
                  <input placeholder="e.g. lora" value={newMethod.method_key} onChange={(e) => setNewMethod({ ...newMethod, method_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  <p className="text-xs text-muted-foreground mt-1">ค่าที่ใช้ได้: <button type="button" className="underline hover:text-foreground" onClick={() => setNewMethod({ ...newMethod, method_key: 'lora' })}>lora</button> (LoRATrainer)</p>
                </>
              )}
            </div>
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Description — อธิบายสั้นๆ ว่า method นี้คืออะไร</label>
            <input placeholder="e.g. Low-Rank Adaptation — fine-tune เร็ว ใช้ RAM น้อย" value={newMethod.description} onChange={(e) => setNewMethod({ ...newMethod, description: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Default Config (JSON) — ค่า hyperparameter เริ่มต้น</label>
            <textarea placeholder='e.g. {"lora_r": 16, "lora_alpha": 32, "lora_dropout": 0.05}' value={newMethod.default_config} onChange={(e) => setNewMethod({ ...newMethod, default_config: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm font-mono h-20" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleAddMethod} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
          </div>
        </div>
      )}

      {showForm && tab === 'models' && (
        <div className="rounded-lg border bg-card p-4 mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">HuggingFace Model ID — ชื่อโมเดลจาก huggingface.co</label>
              <input placeholder="e.g. TinyLlama/TinyLlama-1.1B-Chat-v1.0" value={newBaseModel.model_name} onChange={(e) => setNewBaseModel({ ...newBaseModel, model_name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Display Name — ชื่อสั้นๆ แสดงใน dropdown</label>
              <input placeholder="e.g. TinyLlama 1.1B" value={newBaseModel.display_name} onChange={(e) => setNewBaseModel({ ...newBaseModel, display_name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Size (Billion) — ขนาดโมเดล</label>
              <input type="number" step="0.1" placeholder="e.g. 1.1" value={newBaseModel.size_billion} onChange={(e) => setNewBaseModel({ ...newBaseModel, size_billion: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Min RAM (GB) — RAM ขั้นต่ำที่แนะนำ</label>
              <input type="number" step="1" placeholder="e.g. 4" value={newBaseModel.recommended_ram_gb} onChange={(e) => setNewBaseModel({ ...newBaseModel, recommended_ram_gb: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Target Modules — layer ที่ LoRA จะ inject</label>
              <input placeholder="e.g. q_proj,v_proj,k_proj,o_proj" value={newBaseModel.default_target_modules} onChange={(e) => setNewBaseModel({ ...newBaseModel, default_target_modules: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            ดูข้อมูลโมเดลได้ที่ <a href="https://huggingface.co/models?pipeline_tag=text-generation&sort=trending" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">huggingface.co/models</a>
            {' '}— โมเดลเล็กๆ เช่น TinyLlama (1.1B, ~4GB RAM) เหมาะสำหรับทดลอง
          </p>
          <div className="flex gap-2">
            <button onClick={handleAddBaseModel} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
          </div>
        </div>
      )}

      {showForm && tab === 'targets' && (
        <div className="rounded-lg border bg-card p-4 mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Name — ชื่อที่แสดงใน UI</label>
              <input placeholder="e.g. Local Ollama" value={newTarget.name} onChange={(e) => setNewTarget({ ...newTarget, name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Target Key — deployer ที่ลงทะเบียนไว้ใน Python</label>
              {Object.keys(registeredDeployers).length > 0 ? (
                <select value={newTarget.target_key} onChange={(e) => setNewTarget({ ...newTarget, target_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm">
                  <option value="">Select registry key...</option>
                  {Object.entries(registeredDeployers).map(([key, cls]) => (
                    <option key={key} value={key}>{key} ({cls})</option>
                  ))}
                </select>
              ) : (
                <>
                  <input placeholder="e.g. ollama" value={newTarget.target_key} onChange={(e) => setNewTarget({ ...newTarget, target_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  <p className="text-xs text-muted-foreground mt-1">ค่าที่ใช้ได้: <button type="button" className="underline hover:text-foreground" onClick={() => setNewTarget({ ...newTarget, target_key: 'ollama' })}>ollama</button> (OllamaDeployer)</p>
                </>
              )}
            </div>
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Config (JSON) — การตั้งค่าเฉพาะ target เช่น URL, temperature</label>
            <textarea placeholder='e.g. {"temperature": 0.7, "top_p": 0.9, "num_ctx": 4096}' value={newTarget.config} onChange={(e) => setNewTarget({ ...newTarget, config: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm font-mono h-20" />
          </div>
          <div className="flex gap-2">
            <button onClick={handleAddTarget} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
          </div>
        </div>
      )}

      {/* ---------- Lists ---------- */}

      {tab === 'methods' && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground mb-3">
            วิธีการ fine-tune เช่น LoRA, QLoRA — แต่ละ method จะเชื่อมกับ trainer class ใน Python registry (method key)
            และสามารถกำหนด default config (เช่น rank, alpha) ได้
          </p>
          {methods.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-400">
              No training methods configured. Add one to get started.
            </div>
          ) : methods.map((m) => (
            editingMethodId === m.id ? (
              <div key={m.id} className="rounded-lg border-2 border-blue-300 bg-card p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Name</label>
                    <input value={editMethod.name} onChange={(e) => setEditMethod({ ...editMethod, name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Method Key</label>
                    <input value={editMethod.method_key} onChange={(e) => setEditMethod({ ...editMethod, method_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Description</label>
                  <input value={editMethod.description} onChange={(e) => setEditMethod({ ...editMethod, description: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Default Config (JSON)</label>
                  <textarea value={editMethod.default_config} onChange={(e) => setEditMethod({ ...editMethod, default_config: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm font-mono h-20" />
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editMethod.is_active} onChange={(e) => setEditMethod({ ...editMethod, is_active: e.target.checked })} />
                    Active
                  </label>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleUpdateMethod} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
                  <button onClick={() => setEditingMethodId(null)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
                </div>
              </div>
            ) : (
              <div key={m.id} className="flex items-center justify-between rounded-lg border bg-card p-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">{m.name}</span>
                    <span className="text-xs bg-muted px-2 py-0.5 rounded">{m.method_key}</span>
                    {!m.is_active && <span className="text-xs text-red-500">inactive</span>}
                  </div>
                  {m.description && <p className="text-sm text-muted-foreground mt-1">{m.description}</p>}
                  {Object.keys(m.default_config).length > 0 && (
                    <p className="text-xs text-muted-foreground font-mono mt-1">{JSON.stringify(m.default_config)}</p>
                  )}
                </div>
                <div className="flex gap-1">
                  <button onClick={() => startEditMethod(m)} className="p-1 text-gray-400 hover:text-blue-500">
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button onClick={() => handleDeleteMethod(m.id)} className="p-1 text-gray-400 hover:text-red-500">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          ))}
        </div>
      )}

      {tab === 'models' && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground mb-3">
            โมเดลพื้นฐานจาก HuggingFace ที่จะนำมา fine-tune — ระบุ HF model ID, ขนาด, RAM ที่แนะนำ
            และ target modules สำหรับ LoRA (เช่น q_proj, v_proj)
          </p>
          {baseModels.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-400">
              No base models in catalog. Add models that your team can use for training.
            </div>
          ) : baseModels.map((m) => (
            editingModelId === m.id ? (
              <div key={m.id} className="rounded-lg border-2 border-blue-300 bg-card p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">HuggingFace Model ID</label>
                    <input value={m.model_name} disabled className="w-full px-3 py-2 border rounded-md text-sm bg-muted" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Display Name</label>
                    <input value={editModel.display_name} onChange={(e) => setEditModel({ ...editModel, display_name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Size (Billion)</label>
                    <input type="number" step="0.1" value={editModel.size_billion} onChange={(e) => setEditModel({ ...editModel, size_billion: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Min RAM (GB)</label>
                    <input type="number" step="1" value={editModel.recommended_ram_gb} onChange={(e) => setEditModel({ ...editModel, recommended_ram_gb: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Target Modules</label>
                    <input value={editModel.default_target_modules} onChange={(e) => setEditModel({ ...editModel, default_target_modules: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editModel.is_active} onChange={(e) => setEditModel({ ...editModel, is_active: e.target.checked })} />
                    Active
                  </label>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleUpdateModel} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
                  <button onClick={() => setEditingModelId(null)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
                </div>
              </div>
            ) : (
              <div key={m.id} className="flex items-center justify-between rounded-lg border bg-card p-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">{m.display_name}</span>
                    {!m.is_active && <span className="text-xs text-red-500">inactive</span>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{m.model_name}</p>
                  <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                    {m.size_billion && <span>{m.size_billion}B params</span>}
                    {m.recommended_ram_gb && <span>{m.recommended_ram_gb}GB RAM</span>}
                    {m.default_target_modules && <span>modules: {m.default_target_modules.join(', ')}</span>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => startEditModel(m)} className="p-1 text-gray-400 hover:text-blue-500">
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button onClick={() => handleDeleteBaseModel(m.id)} className="p-1 text-gray-400 hover:text-red-500">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          ))}
        </div>
      )}

      {tab === 'targets' && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground mb-3">
            เป้าหมายที่จะ deploy โมเดลหลัง train เสร็จ เช่น Ollama (local), vLLM, TGI
            — แต่ละ target เชื่อมกับ deployer class ใน Python registry และสามารถกำหนด config เฉพาะ (เช่น base_url) ได้
          </p>
          {targets.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-400">
              No deployment targets configured. Add where trained models should be deployed.
            </div>
          ) : targets.map((t) => (
            editingTargetId === t.id ? (
              <div key={t.id} className="rounded-lg border-2 border-blue-300 bg-card p-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Name</label>
                    <input value={editTarget.name} onChange={(e) => setEditTarget({ ...editTarget, name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground block mb-1">Target Key</label>
                    <input value={editTarget.target_key} onChange={(e) => setEditTarget({ ...editTarget, target_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground block mb-1">Config (JSON)</label>
                  <textarea value={editTarget.config} onChange={(e) => setEditTarget({ ...editTarget, config: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm font-mono h-20" />
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={editTarget.is_active} onChange={(e) => setEditTarget({ ...editTarget, is_active: e.target.checked })} />
                    Active
                  </label>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleUpdateTarget} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
                  <button onClick={() => setEditingTargetId(null)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
                </div>
              </div>
            ) : (
              <div key={t.id} className="flex items-center justify-between rounded-lg border bg-card p-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Rocket className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">{t.name}</span>
                    <span className="text-xs bg-muted px-2 py-0.5 rounded">{t.target_key}</span>
                    {!t.is_active && <span className="text-xs text-red-500">inactive</span>}
                  </div>
                  {Object.keys(t.config).length > 0 && (
                    <p className="text-xs text-muted-foreground font-mono mt-1">{JSON.stringify(t.config)}</p>
                  )}
                </div>
                <div className="flex gap-1">
                  <button onClick={() => startEditTarget(t)} className="p-1 text-gray-400 hover:text-blue-500">
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button onClick={() => handleDeleteTarget(t.id)} className="p-1 text-gray-400 hover:text-red-500">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )
          ))}
        </div>
      )}
    </div>
  );
}
