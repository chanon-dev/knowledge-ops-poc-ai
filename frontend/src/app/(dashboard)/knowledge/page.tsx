"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Department, KnowledgeDoc } from "@/types";
import { DepartmentSelector } from "@/components/chat/DepartmentSelector";
import { Upload, Trash2, FileText, Loader2 } from "lucide-react";

export default function KnowledgePage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDoc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState("");

  useEffect(() => {
    api.get("/departments").then((res) => {
      const depts = res.data.data || [];
      setDepartments(depts);
      if (depts.length > 0) setSelectedDeptId(depts[0].id);
    }).catch(() => {});
  }, []);

  const loadDocuments = useCallback(async () => {
    if (!selectedDeptId) return;
    try {
      const res = await api.get(`/knowledge/${selectedDeptId}`);
      setDocuments(res.data.data || []);
    } catch {}
  }, [selectedDeptId]);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedDeptId || !title.trim()) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title);
      await api.post(`/knowledge/${selectedDeptId}/upload`, formData);
      setTitle("");
      loadDocuments();
    } catch {}
    setUploading(false);
  };

  const handleDelete = async (docId: string) => {
    if (!selectedDeptId || !confirm("Delete this document?")) return;
    try {
      await api.delete(`/knowledge/${selectedDeptId}/${docId}`);
      loadDocuments();
    } catch {}
  };

  const statusColor: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    processing: "bg-blue-100 text-blue-700",
    indexed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Knowledge Base</h2>
      <DepartmentSelector departments={departments} selectedId={selectedDeptId} onSelect={setSelectedDeptId} />

      {selectedDeptId && (
        <>
          <div className="mt-6 bg-white rounded-xl border p-6">
            <h3 className="font-medium mb-3">Upload Document</h3>
            <div className="flex gap-3">
              <input
                type="text"
                placeholder="Document title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="flex-1 border rounded-lg px-3 py-2 text-sm"
              />
              <label className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer ${uploading ? 'bg-gray-200' : 'bg-blue-600 text-white hover:bg-blue-700'}`}>
                {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                {uploading ? "Uploading..." : "Upload"}
                <input type="file" className="hidden" accept=".pdf,.docx,.txt,.md,.csv,.html" onChange={handleUpload} disabled={uploading || !title.trim()} />
              </label>
            </div>
          </div>

          <div className="mt-6 bg-white rounded-xl border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 text-left text-sm text-gray-500">
                <tr>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Chunks</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {documents.map((doc) => (
                  <tr key={doc.id} className="text-sm">
                    <td className="px-4 py-3 flex items-center gap-2">
                      <FileText className="h-4 w-4 text-gray-400" />
                      {doc.title}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{doc.source_type}</td>
                    <td className="px-4 py-3">{doc.chunk_count}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs ${statusColor[doc.status] || ""}`}>{doc.status}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <button onClick={() => handleDelete(doc.id)} className="text-red-500 hover:text-red-700">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
                {documents.length === 0 && (
                  <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No documents yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
