"use client";

import { Department } from "@/types";

interface DepartmentSelectorProps {
  departments: Department[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function DepartmentSelector({
  departments,
  selectedId,
  onSelect,
}: DepartmentSelectorProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2">
      {departments.map((dept) => (
        <button
          key={dept.id}
          onClick={() => onSelect(dept.id)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium whitespace-nowrap transition-colors ${
            selectedId === dept.id
              ? "bg-blue-50 border-blue-300 text-blue-700"
              : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
          }`}
        >
          <span>{dept.icon}</span>
          <span>{dept.name}</span>
        </button>
      ))}
    </div>
  );
}
