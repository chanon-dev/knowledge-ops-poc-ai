"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Approval } from "@/types";
import { CheckCircle, XCircle, Clock } from "lucide-react";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editedAnswer, setEditedAnswer] = useState("");
  const [rejectReason, setRejectReason] = useState("");

  useEffect(() => { loadApprovals(); }, []);

  const loadApprovals = async () => {
    try {
      const res = await api.get("/approvals?status=pending");
      setApprovals(res.data.data || []);
    } catch {}
  };

  const handleApprove = async (id: string) => {
    try {
      await api.post(`/approvals/${id}/approve`, {
        approved_answer: editedAnswer || undefined,
      });
      loadApprovals();
      setSelectedId(null);
    } catch {}
  };

  const handleReject = async (id: string) => {
    if (!rejectReason.trim()) return;
    try {
      await api.post(`/approvals/${id}/reject`, {
        rejection_reason: rejectReason,
      });
      loadApprovals();
      setSelectedId(null);
      setRejectReason("");
    } catch {}
  };

  const selected = approvals.find((a) => a.id === selectedId);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Approvals</h2>
        <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
          {approvals.length} pending
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          {approvals.map((approval) => (
            <div
              key={approval.id}
              onClick={() => {
                setSelectedId(approval.id);
                setEditedAnswer(approval.original_answer ?? approval.original_content);
              }}
              className={`bg-white rounded-xl border p-4 cursor-pointer transition-colors ${
                selectedId === approval.id ? "border-blue-300 ring-1 ring-blue-200" : "hover:border-gray-300"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-yellow-500" />
                <span className={`px-2 py-0.5 rounded-full text-xs ${approval.priority === "urgent" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>
                  {approval.priority}
                </span>
                <span className="text-xs text-gray-400 ml-auto">
                  {new Date(approval.created_at).toLocaleString()}
                </span>
              </div>
              <p className="text-sm text-gray-700 line-clamp-3">{approval.original_answer}</p>
            </div>
          ))}
          {approvals.length === 0 && (
            <div className="text-center text-gray-400 py-12">No pending approvals</div>
          )}
        </div>

        {selected && (
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-medium mb-4">Review Answer</h3>
            <textarea
              value={editedAnswer}
              onChange={(e) => setEditedAnswer(e.target.value)}
              rows={8}
              className="w-full border rounded-lg p-3 text-sm mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => handleApprove(selected.id)}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
              >
                <CheckCircle className="h-4 w-4" /> Approve
              </button>
              <button
                onClick={() => {
                  const reason = prompt("Rejection reason:");
                  if (reason) {
                    setRejectReason(reason);
                    handleReject(selected.id);
                  }
                }}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
              >
                <XCircle className="h-4 w-4" /> Reject
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
