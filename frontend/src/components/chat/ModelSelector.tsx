"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Cpu } from "lucide-react";

interface Model {
  name: string;
  size: number;
  provider_name?: string;
}

interface ModelSelectorProps {
  models: Model[];
  selectedModel: string | null;
  onSelect: (model: string) => void;
}

export function ModelSelector({ models, selectedModel, onSelect }: ModelSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selected = models.find((m) => m.name === selectedModel);
  const displayName = selected
    ? `${selected.name.split(":")[0]}${selected.provider_name && selected.provider_name !== "Ollama" ? ` (${selected.provider_name})` : ""}`
    : "Select model";

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 px-2 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
      >
        <Cpu className="h-3.5 w-3.5" />
        <span className="max-w-[160px] truncate">{displayName}</span>
        <ChevronDown className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute bottom-full left-0 mb-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-48 overflow-y-auto">
          {models.map((m) => (
            <button
              key={m.name}
              onClick={() => { onSelect(m.name); setOpen(false); }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center justify-between ${
                selectedModel === m.name ? "bg-blue-50 text-blue-700" : "text-gray-700"
              }`}
            >
              <div className="flex flex-col min-w-0">
                <span className="truncate">{m.name}</span>
                {m.provider_name && (
                  <span className="text-xs text-gray-400">{m.provider_name}</span>
                )}
              </div>
              {m.size > 0 && (
                <span className="text-xs text-gray-400 ml-2 shrink-0">
                  {(m.size / 1e9).toFixed(1)}GB
                </span>
              )}
            </button>
          ))}
          {models.length === 0 && (
            <div className="px-3 py-2 text-sm text-gray-400">No models available</div>
          )}
        </div>
      )}
    </div>
  );
}
