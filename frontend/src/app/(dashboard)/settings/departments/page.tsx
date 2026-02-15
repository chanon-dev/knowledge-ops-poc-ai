"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Department } from "@/types";
import { Plus, Edit2, Trash2 } from "lucide-react";

const emptyForm = { name: "", slug: "", icon: "📁", description: "" };

export default function DepartmentSettingsPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);

  useEffect(() => { loadDepartments(); }, []);

  const loadDepartments = async () => {
    try {
      const res = await api.get("/departments");
      setDepartments(res.data.data || []);
    } catch {}
  };

  const resetForm = () => {
    setForm(emptyForm);
    setShowForm(false);
    setEditingId(null);
  };

  const handleCreate = async () => {
    try {
      await api.post("/departments", form);
      resetForm();
      loadDepartments();
    } catch {}
  };

  const handleEdit = (dept: Department) => {
    setEditingId(dept.id);
    setForm({
      name: dept.name,
      slug: dept.slug,
      icon: dept.icon || "📁",
      description: dept.description || "",
    });
    setShowForm(true);
  };

  const handleUpdate = async () => {
    if (!editingId) return;
    try {
      await api.put(`/departments/${editingId}`, {
        name: form.name,
        description: form.description,
        icon: form.icon,
      });
      resetForm();
      loadDepartments();
    } catch {}
  };

  const handleSubmit = () => {
    if (editingId) {
      handleUpdate();
    } else {
      handleCreate();
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Archive this department?")) return;
    try {
      await api.delete(`/departments/${id}`);
      loadDepartments();
    } catch {}
  };

  const handleNameChange = (value: string) => {
    const update: typeof form = { ...form, name: value };
    if (!editingId) {
      update.slug = value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    }
    setForm(update);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Departments</h2>
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
        >
          <Plus className="h-4 w-4" /> New Department
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <h3 className="font-medium mb-4">{editingId ? "Edit Department" : "Create Department"}</h3>
          <div className="grid grid-cols-2 gap-4">
            <input placeholder="Name" value={form.name} onChange={(e) => handleNameChange(e.target.value)} className="border rounded-lg px-3 py-2 text-sm" />
            <input
              placeholder="Slug (e.g. it-ops)"
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              className="border rounded-lg px-3 py-2 text-sm"
              disabled={!!editingId}
            />
            <input placeholder="Icon emoji" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} className="border rounded-lg px-3 py-2 text-sm" />
            <input placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">
              {editingId ? "Save" : "Create"}
            </button>
            <button onClick={resetForm} className="px-4 py-2 bg-gray-100 rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {departments.map((dept) => (
          <div key={dept.id} className="bg-white rounded-xl border p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{dept.icon}</span>
              <div>
                <h3 className="font-medium">{dept.name}</h3>
                <p className="text-sm text-gray-500">{dept.description || dept.slug}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => handleEdit(dept)} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"><Edit2 className="h-4 w-4" /></button>
              <button onClick={() => handleDelete(dept.id)} className="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-50"><Trash2 className="h-4 w-4" /></button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
