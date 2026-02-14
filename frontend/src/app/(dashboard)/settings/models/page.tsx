'use client';

import { useState, useEffect } from 'react';

interface Model {
  id: string;
  name: string;
  base_model: string;
  status: string;
  metrics: Record<string, number>;
  created_at: string;
}

export default function ModelManagement() {
  const [models, setModels] = useState<Model[]>([]);
  const [training, setTraining] = useState(false);
  const [trainingStatus, setTrainingStatus] = useState<any>(null);

  useEffect(() => {
    // Mock data
    setModels([
      {
        id: '1', name: 'lora-it-ops-v2', base_model: 'Mistral-7B',
        status: 'ready', metrics: { rougeL: 0.72, bleu: 0.45, eval_loss: 0.34 },
        created_at: '2026-02-10T10:00:00Z',
      },
      {
        id: '2', name: 'lora-hr-v1', base_model: 'Mistral-7B',
        status: 'ready', metrics: { rougeL: 0.68, bleu: 0.41, eval_loss: 0.38 },
        created_at: '2026-02-08T14:00:00Z',
      },
    ]);
  }, []);

  const triggerTraining = async () => {
    setTraining(true);
    setTrainingStatus({ status: 'queued', progress: 0 });

    // Simulate training progress
    const steps = [
      { status: 'running', progress: 10, step: 'Exporting training data...' },
      { status: 'running', progress: 30, step: 'Preparing dataset...' },
      { status: 'running', progress: 50, step: 'Training LoRA adapter...' },
      { status: 'running', progress: 80, step: 'Evaluating model...' },
      { status: 'completed', progress: 100, step: 'Training complete!' },
    ];

    for (const step of steps) {
      await new Promise((r) => setTimeout(r, 1500));
      setTrainingStatus(step);
    }
    setTraining(false);
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Model Management</h1>
          <p className="text-muted-foreground">Fine-tuned LoRA models for your departments</p>
        </div>
        <button
          onClick={triggerTraining}
          disabled={training}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
        >
          {training ? 'Training...' : 'Train New Model'}
        </button>
      </div>

      {/* Training Status */}
      {trainingStatus && (
        <div className="mb-6 rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">Training Job</span>
            <span className={`text-sm px-2 py-0.5 rounded-full ${
              trainingStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
              trainingStatus.status === 'running' ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>{trainingStatus.status}</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden mb-2">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${trainingStatus.progress}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground">{trainingStatus.step || 'Waiting...'}</p>
        </div>
      )}

      {/* Models List */}
      <div className="space-y-4">
        {models.map((model) => (
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

            <div className="grid grid-cols-3 gap-4">
              {Object.entries(model.metrics).map(([key, value]) => (
                <div key={key} className="text-center p-3 bg-muted rounded-md">
                  <p className="text-xs text-muted-foreground uppercase">{key}</p>
                  <p className="text-xl font-bold">{typeof value === 'number' ? value.toFixed(3) : value}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
