'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { Plus, Trash2, Cpu, Server, Eye, EyeOff, Play, Settings2, Info } from 'lucide-react';

interface Provider {
  id: string;
  name: string;
  provider_type: string;
  base_url: string;
  has_api_key: boolean;
  is_active: boolean;
  created_at: string;
}

interface AllowedModel {
  id: string;
  model_name: string;
  is_default: boolean;
  provider_id: string | null;
  provider_name: string;
  created_at: string;
}

interface ProviderModel {
  name: string;
  size: number;
}

interface TrainedModel {
  id: string;
  name: string;
  base_model: string;
  status: string;
  metrics: Record<string, number>;
  created_at: string;
}

interface TrainingJob {
  id: string;
  status: string;
  progress: number;
  status_message?: string;
  metrics?: Record<string, number>;
  model_name?: string;
  deployed_to_target?: boolean;
  error?: string;
  device_info?: Record<string, string>;
  base_model_name?: string;
  method_key?: string;
}

interface CatalogMethod {
  id: string;
  name: string;
  method_key: string;
  default_config: Record<string, any>;
}

interface CatalogBaseModel {
  id: string;
  model_name: string;
  display_name: string;
  size_billion: number | null;
  recommended_ram_gb: number | null;
}

interface CatalogTarget {
  id: string;
  name: string;
  target_key: string;
}

interface TrainingConfig {
  defaults: {
    base_model: string;
    epochs: number;
    learning_rate: number;
    batch_size: number;
    deploy_to_ollama: boolean;
    min_samples: number;
  };
  device: Record<string, string>;
  catalog: {
    methods: CatalogMethod[];
    base_models: CatalogBaseModel[];
    targets: CatalogTarget[];
  };
  registry: {
    trainers: Record<string, string>;
    deployers: Record<string, string>;
  };
}

const PROGRESS_LABELS: Record<number, string> = {
  0: 'Queued...',
  10: 'Exporting training data...',
  30: 'Preparing dataset...',
  50: 'Loading model...',
  60: 'Training adapter...',
  80: 'Evaluating model...',
  90: 'Deploying model...',
  100: 'Training complete!',
};

function getProgressLabel(progress: number): string {
  const keys = Object.keys(PROGRESS_LABELS).map(Number).sort((a, b) => b - a);
  for (const key of keys) {
    if (progress >= key) return PROGRESS_LABELS[key];
  }
  return 'Waiting...';
}

export default function ModelManagement() {
  // Providers
  const [providers, setProviders] = useState<Provider[]>([]);
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [newProvider, setNewProvider] = useState({ name: '', provider_type: 'openai_compatible', base_url: '', api_key: '' });
  const [showApiKey, setShowApiKey] = useState(false);

  // Allowed models
  const [allowedModels, setAllowedModels] = useState<AllowedModel[]>([]);
  const [loadingAllowed, setLoadingAllowed] = useState(true);
  const [showAddModel, setShowAddModel] = useState(false);
  const [addModelSource, setAddModelSource] = useState<string>('ollama');
  const [providerModels, setProviderModels] = useState<ProviderModel[]>([]);

  // Fine-tuned models
  const [trainedModels, setTrainedModels] = useState<TrainedModel[]>([]);

  // Training
  const [training, setTraining] = useState(false);
  const [trainingJob, setTrainingJob] = useState<TrainingJob | null>(null);
  const [showTrainConfig, setShowTrainConfig] = useState(false);
  const [serverConfig, setServerConfig] = useState<TrainingConfig | null>(null);
  const [trainConfig, setTrainConfig] = useState({
    method_key: 'lora',
    method_id: '' as string,
    base_model_name: '',
    base_model_id: '' as string,
    deployment_target_id: '' as string,
    epochs: 3,
    learning_rate: 2e-4,
    batch_size: 4,
  });
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadTrainedModels = useCallback(async () => {
    try {
      const res = await api.get('/models');
      setTrainedModels(res.data.data || []);
    } catch { /* ignore */ }
  }, []);

  const loadTrainingConfig = useCallback(async () => {
    try {
      const res = await api.get('/models/training-config');
      const config: TrainingConfig = res.data;
      setServerConfig(config);
      setTrainConfig((prev) => ({
        ...prev,
        method_key: config.catalog.methods[0]?.method_key || 'lora',
        method_id: config.catalog.methods[0]?.id || '',
        base_model_name: config.catalog.base_models[0]?.model_name || config.defaults.base_model,
        base_model_id: config.catalog.base_models[0]?.id || '',
        deployment_target_id: config.catalog.targets[0]?.id || '',
        epochs: config.defaults.epochs,
        learning_rate: config.defaults.learning_rate,
        batch_size: config.defaults.batch_size,
      }));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadProviders();
    loadAllowedModels();
    loadTrainedModels();
    loadTrainingConfig();
  }, [loadTrainedModels, loadTrainingConfig]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const loadProviders = async () => {
    try {
      const res = await api.get('/models/providers');
      setProviders(res.data.data || []);
    } catch { /* ignore */ }
  };

  const loadAllowedModels = async () => {
    setLoadingAllowed(true);
    try {
      const res = await api.get('/models/allowed');
      setAllowedModels(res.data.data || []);
    } catch { /* ignore */ }
    finally { setLoadingAllowed(false); }
  };

  const handleAddProvider = async () => {
    if (!newProvider.name || !newProvider.base_url) return;
    try {
      await api.post('/models/providers', newProvider);
      await loadProviders();
      setShowAddProvider(false);
      setNewProvider({ name: '', provider_type: 'openai_compatible', base_url: '', api_key: '' });
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to add provider');
    }
  };

  const handleRemoveProvider = async (id: string) => {
    try {
      await api.delete(`/models/providers/${id}`);
      setProviders((prev) => prev.filter((p) => p.id !== id));
    } catch { alert('Failed to remove provider'); }
  };

  const handleSelectModelSource = async (source: string) => {
    setAddModelSource(source);
    setProviderModels([]);
    try {
      if (source === 'ollama') {
        const res = await api.get('/models/ollama');
        setProviderModels(res.data.data || []);
      } else {
        const res = await api.get(`/models/providers/${source}/models`);
        setProviderModels(res.data.data || []);
      }
    } catch { setProviderModels([]); }
  };

  const handleAddModel = async (modelName: string) => {
    const providerId = addModelSource === 'ollama' ? null : addModelSource;
    try {
      await api.post('/models/allowed', { model_name: modelName, provider_id: providerId });
      await loadAllowedModels();
      setShowAddModel(false);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to add model');
    }
  };

  const handleRemoveModel = async (id: string) => {
    try {
      await api.delete(`/models/allowed/${id}`);
      setAllowedModels((prev) => prev.filter((m) => m.id !== id));
    } catch { alert('Failed to remove model'); }
  };

  const handleShowAddModel = () => {
    if (!showAddModel) {
      handleSelectModelSource('ollama');
    }
    setShowAddModel(!showAddModel);
  };

  const triggerTraining = async () => {
    setTraining(true);
    setTrainingJob({ id: '', status: 'queued', progress: 0 });
    setShowTrainConfig(false);

    try {
      const payload: Record<string, any> = {
        method_key: trainConfig.method_key,
        config_overrides: {
          epochs: trainConfig.epochs,
          learning_rate: trainConfig.learning_rate,
          batch_size: trainConfig.batch_size,
        },
      };
      if (trainConfig.base_model_id) payload.base_model_id = trainConfig.base_model_id;
      else payload.base_model_name = trainConfig.base_model_name;
      if (trainConfig.method_id) payload.method_id = trainConfig.method_id;
      if (trainConfig.deployment_target_id) payload.deployment_target_id = trainConfig.deployment_target_id;

      const res = await api.post('/models/train', payload);
      const jobId = res.data.job_id;
      setTrainingJob({ id: jobId, status: 'queued', progress: 0 });

      // Poll for status
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await api.get(`/models/${jobId}/status`);
          const job = statusRes.data;
          setTrainingJob(job);

          if (job.status === 'completed' || job.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setTraining(false);
            if (job.status === 'completed') {
              loadTrainedModels();
            }
          }
        } catch {
          // keep polling
        }
      }, 3000);
    } catch (err: any) {
      setTraining(false);
      setTrainingJob({
        id: '',
        status: 'failed',
        progress: 0,
        error: err?.response?.data?.detail || 'Failed to start training',
      });
    }
  };

  const availableToAdd = providerModels.filter(
    (pm) => !allowedModels.some((am) => am.model_name === pm.name)
  );

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Model Management</h1>

      {/* AI Providers Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold">AI Providers</h2>
            <p className="text-sm text-muted-foreground">
              Configure external AI providers (OpenAI, Groq, Together AI, etc.)
            </p>
            <div className="flex items-start gap-2 mt-2 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md text-xs text-blue-700 dark:text-blue-300">
              <Info className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                เพิ่ม AI provider ภายนอกที่ต้องการเชื่อมต่อ เช่น OpenAI, Groq หรือ provider อื่นที่รองรับ OpenAI-compatible API
                — Ollama (local) พร้อมใช้งานเสมอโดยไม่ต้อง config เพิ่ม
              </span>
            </div>
          </div>
          <button
            onClick={() => setShowAddProvider(!showAddProvider)}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add Provider
          </button>
        </div>

        {showAddProvider && (
          <div className="rounded-lg border bg-card p-4 mb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input
                placeholder="Provider name (e.g. OpenAI)"
                value={newProvider.name}
                onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })}
                className="px-3 py-2 border rounded-md text-sm"
              />
              <select
                value={newProvider.provider_type}
                onChange={(e) => setNewProvider({ ...newProvider, provider_type: e.target.value })}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value="openai_compatible">OpenAI Compatible</option>
                <option value="ollama">Ollama</option>
              </select>
            </div>
            <input
              placeholder="Base URL (e.g. https://api.openai.com/v1)"
              value={newProvider.base_url}
              onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })}
              className="w-full px-3 py-2 border rounded-md text-sm"
            />
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                placeholder="API Key (optional for Ollama)"
                value={newProvider.api_key}
                onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                className="w-full px-3 py-2 border rounded-md text-sm pr-10"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <div className="flex gap-2">
              <button onClick={handleAddProvider} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Save</button>
              <button onClick={() => setShowAddProvider(false)} className="px-4 py-2 text-sm border rounded-md hover:bg-gray-50">Cancel</button>
            </div>
          </div>
        )}

        {providers.length === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-300 p-4 text-center text-sm text-gray-400">
            No external providers configured. Default Ollama server is always available.
          </div>
        ) : (
          <div className="space-y-2">
            {providers.map((p) => (
              <div key={p.id} className="flex items-center justify-between rounded-lg border bg-card p-3">
                <div className="flex items-center gap-3">
                  <Server className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="font-medium text-sm">{p.name}</span>
                    <span className="text-xs text-gray-400 ml-2">{p.provider_type}</span>
                    <p className="text-xs text-gray-400">{p.base_url}</p>
                  </div>
                </div>
                <button onClick={() => handleRemoveProvider(p.id)} className="p-1 text-gray-400 hover:text-red-500 rounded">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <hr className="my-6" />

      {/* Allowed Chat Models Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-bold">Allowed Chat Models</h2>
            <p className="text-sm text-muted-foreground">
              Models that users can select in chat. If none are configured, all Ollama models will be available.
            </p>
            <div className="flex items-start gap-2 mt-2 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md text-xs text-blue-700 dark:text-blue-300">
              <Info className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                กำหนดว่า user สามารถเลือกใช้โมเดลใดได้บ้างในหน้า Chat — เลือกได้ทั้งจาก Ollama (local) และ provider ภายนอกที่เพิ่มไว้ด้านบน
                ถ้าไม่เพิ่มรายการใดเลย ระบบจะแสดงโมเดลทั้งหมดจาก Ollama โดยอัตโนมัติ
              </span>
            </div>
          </div>
          <button
            onClick={handleShowAddModel}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Add Model
          </button>
        </div>

        {showAddModel && (
          <div className="rounded-lg border bg-card p-4 mb-4">
            <div className="mb-3">
              <label className="text-sm font-medium mb-1 block">Select provider:</label>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={() => handleSelectModelSource('ollama')}
                  className={`px-3 py-1.5 text-sm rounded-md border ${addModelSource === 'ollama' ? 'bg-blue-50 border-blue-300 text-blue-700' : 'hover:bg-gray-50'}`}
                >
                  Ollama (Local)
                </button>
                {providers.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => handleSelectModelSource(p.id)}
                    className={`px-3 py-1.5 text-sm rounded-md border ${addModelSource === p.id ? 'bg-blue-50 border-blue-300 text-blue-700' : 'hover:bg-gray-50'}`}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>
            <div className="max-h-48 overflow-y-auto border rounded-md">
              {availableToAdd.length === 0 ? (
                <div className="px-3 py-4 text-sm text-gray-400 text-center">No models available to add</div>
              ) : (
                availableToAdd.map((m) => (
                  <button
                    key={m.name}
                    onClick={() => handleAddModel(m.name)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center justify-between border-b last:border-b-0"
                  >
                    <span className="truncate">{m.name}</span>
                    {m.size > 0 && (
                      <span className="text-xs text-gray-400 ml-2 shrink-0">{(m.size / 1e9).toFixed(1)}GB</span>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        )}

        {loadingAllowed ? (
          <div className="text-sm text-gray-400">Loading...</div>
        ) : allowedModels.length === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center text-sm text-gray-400">
            No models configured. Users will see all available Ollama models.
          </div>
        ) : (
          <div className="space-y-2">
            {allowedModels.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-lg border bg-card p-3">
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-gray-400" />
                  <span className="font-medium text-sm">{m.model_name}</span>
                  <span className="text-xs text-gray-400">({m.provider_name})</span>
                  {m.is_default && (
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">default</span>
                  )}
                </div>
                <button onClick={() => handleRemoveModel(m.id)} className="p-1 text-gray-400 hover:text-red-500 rounded">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <hr className="my-6" />

      {/* Fine-tuned Models Section */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold">Fine-tuned Models</h2>
          <p className="text-sm text-muted-foreground">Models fine-tuned on your approved Q&amp;A data</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowTrainConfig(!showTrainConfig)}
            className="p-2 border rounded-md hover:bg-gray-50"
            title="Training settings"
          >
            <Settings2 className="h-4 w-4" />
          </button>
          <button
            onClick={triggerTraining}
            disabled={training}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {training ? 'Training...' : 'Train New Model'}
          </button>
        </div>
      </div>

      <div className="flex items-start gap-2 mb-4 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-md text-xs text-blue-700 dark:text-blue-300">
        <Info className="h-4 w-4 shrink-0 mt-0.5" />
        <span>
          สร้างโมเดลเฉพาะทางจากข้อมูล Q&amp;A ที่ผ่านการอนุมัติแล้ว — เลือกวิธี train, base model, และเป้าหมาย deploy ได้จาก catalog
          ที่ตั้งค่าไว้ใน <a href="/settings/training" className="underline font-medium hover:text-blue-900 dark:hover:text-blue-100">Settings &gt; Training</a>
          {' '}(ต้องเพิ่มข้อมูลใน Training Catalog ก่อนจึงจะเลือกจาก dropdown ได้)
        </span>
      </div>

      {/* Training Config Panel */}
      {showTrainConfig && (
        <div className="mb-6 rounded-lg border bg-card p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-sm">Training Configuration</h3>
            {serverConfig?.device && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                Device: {serverConfig.device.device}
                {serverConfig.device.gpu_name && ` (${serverConfig.device.gpu_name})`}
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {/* Training Method */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Training Method — วิธีการ fine-tune</label>
              {serverConfig?.catalog.methods.length ? (
                <select
                  value={trainConfig.method_id}
                  onChange={(e) => {
                    const m = serverConfig.catalog.methods.find(m => m.id === e.target.value);
                    setTrainConfig({ ...trainConfig, method_id: e.target.value, method_key: m?.method_key || 'lora' });
                  }}
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  {serverConfig.catalog.methods.map((m) => (
                    <option key={m.id} value={m.id}>{m.name} ({m.method_key})</option>
                  ))}
                </select>
              ) : (
                <input type="text" value={trainConfig.method_key} onChange={(e) => setTrainConfig({ ...trainConfig, method_key: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" placeholder="lora" />
              )}
            </div>
            {/* Base Model */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Base Model — โมเดลพื้นฐานที่จะนำมา fine-tune</label>
              {serverConfig?.catalog.base_models.length ? (
                <select
                  value={trainConfig.base_model_id}
                  onChange={(e) => {
                    const bm = serverConfig.catalog.base_models.find(m => m.id === e.target.value);
                    setTrainConfig({ ...trainConfig, base_model_id: e.target.value, base_model_name: bm?.model_name || '' });
                  }}
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  {serverConfig.catalog.base_models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.display_name}{m.size_billion ? ` (${m.size_billion}B)` : ''}{m.recommended_ram_gb ? ` — ${m.recommended_ram_gb}GB RAM` : ''}
                    </option>
                  ))}
                </select>
              ) : (
                <input type="text" value={trainConfig.base_model_name} onChange={(e) => setTrainConfig({ ...trainConfig, base_model_name: e.target.value })} className="w-full px-3 py-2 border rounded-md text-sm" placeholder="HF model ID" />
              )}
            </div>
            {/* Deployment Target */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Deploy To — deploy โมเดลที่ train เสร็จไปที่ไหน</label>
              {serverConfig?.catalog.targets.length ? (
                <select
                  value={trainConfig.deployment_target_id}
                  onChange={(e) => setTrainConfig({ ...trainConfig, deployment_target_id: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md text-sm"
                >
                  <option value="">None (don&apos;t deploy)</option>
                  {serverConfig.catalog.targets.map((t) => (
                    <option key={t.id} value={t.id}>{t.name} ({t.target_key})</option>
                  ))}
                </select>
              ) : (
                <p className="text-xs text-muted-foreground pt-2">ยังไม่มี target — ไปเพิ่มได้ที่ <a href="/settings/training" className="underline hover:text-foreground">Settings &gt; Training &gt; Deployment Targets</a></p>
              )}
            </div>
            {/* Epochs */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Epochs — จำนวนรอบการ train (มาก = แม่นขึ้น แต่ช้า)</label>
              <input type="number" min={1} max={50} value={trainConfig.epochs} onChange={(e) => setTrainConfig({ ...trainConfig, epochs: parseInt(e.target.value) || 3 })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            {/* Learning Rate */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Learning Rate — ค่าเริ่มต้น 0.0002 เหมาะกับ LoRA</label>
              <input type="number" step={0.0001} min={0.00001} max={0.01} value={trainConfig.learning_rate} onChange={(e) => setTrainConfig({ ...trainConfig, learning_rate: parseFloat(e.target.value) || 2e-4 })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
            {/* Batch Size */}
            <div>
              <label className="text-sm text-muted-foreground block mb-1">Batch Size — RAM น้อยให้ลดค่านี้ (2-4)</label>
              <input type="number" min={1} max={64} value={trainConfig.batch_size} onChange={(e) => setTrainConfig({ ...trainConfig, batch_size: parseInt(e.target.value) || 4 })} className="w-full px-3 py-2 border rounded-md text-sm" />
            </div>
          </div>
          {serverConfig && (
            <p className="text-xs text-muted-foreground">
              Minimum {serverConfig.defaults.min_samples} approved Q&amp;A samples required.
              {!serverConfig.catalog.methods.length && ' Add training methods and base models in Settings > Training.'}
            </p>
          )}
        </div>
      )}

      {/* Training Progress */}
      {trainingJob && (
        <div className="mb-6 rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Training Job {trainingJob.id ? `(${trainingJob.id.slice(0, 8)})` : ''}</span>
            <span className={`text-sm px-2 py-0.5 rounded-full ${
              trainingJob.status === 'completed' ? 'bg-green-100 text-green-800' :
              trainingJob.status === 'failed' ? 'bg-red-100 text-red-800' :
              trainingJob.status === 'running' ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>{trainingJob.status}</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                trainingJob.status === 'failed' ? 'bg-red-500' : 'bg-primary'
              }`}
              style={{ width: `${trainingJob.progress}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground">
            {trainingJob.error || trainingJob.status_message || getProgressLabel(trainingJob.progress)}
          </p>
          {trainingJob.status === 'completed' && trainingJob.metrics && (
            <div className="mt-3 grid grid-cols-3 gap-3">
              {Object.entries(trainingJob.metrics).map(([key, value]) => (
                <div key={key} className="text-center p-2 bg-muted rounded-md">
                  <p className="text-xs text-muted-foreground uppercase">{key}</p>
                  <p className="text-lg font-bold">{typeof value === 'number' ? value.toFixed(3) : value}</p>
                </div>
              ))}
            </div>
          )}
          {trainingJob.status === 'completed' && trainingJob.deployed_to_target && (
            <p className="mt-2 text-sm text-green-600">Deployed as &quot;{trainingJob.model_name}&quot;</p>
          )}
        </div>
      )}

      {/* Trained Models List */}
      <div className="space-y-4">
        {trainedModels.length === 0 && !trainingJob && (
          <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400">
            No fine-tuned models yet. Click &quot;Train New Model&quot; to start training on your approved Q&amp;A data.
          </div>
        )}
        {trainedModels.map((model) => (
          <div key={model.id} className="rounded-lg border bg-card p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-lg">{model.name}</h3>
                <p className="text-sm text-muted-foreground">Base: {model.base_model} &middot; {new Date(model.created_at).toLocaleDateString()}</p>
              </div>
              <span className={`text-sm px-3 py-1 rounded-full ${
                model.status === 'ready' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>{model.status}</span>
            </div>
            {Object.keys(model.metrics).length > 0 && (
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(model.metrics).map(([key, value]) => (
                  <div key={key} className="text-center p-3 bg-muted rounded-md">
                    <p className="text-xs text-muted-foreground uppercase">{key}</p>
                    <p className="text-xl font-bold">{typeof value === 'number' ? value.toFixed(3) : value}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
