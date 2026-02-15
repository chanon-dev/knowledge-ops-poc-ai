"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Message } from "@/types";
import {
  ChevronDown,
  ChevronUp,
  Clock,
  Cpu,
  CheckCircle,
  XCircle,
  Loader2,
} from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  onStatusChange?: (messageId: string, newStatus: string) => void;
}

export function MessageBubble({ message, onStatusChange }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectInput, setShowRejectInput] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const isUser = message.role === "user";

  const handleApprove = async () => {
    if (!message.approval_id) return;
    setActionLoading(true);
    try {
      await api.post(`/approvals/${message.approval_id}/approve`, {});
      onStatusChange?.(message.id, "approved");
    } catch {
      // ignore
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!message.approval_id || !rejectReason.trim()) return;
    setActionLoading(true);
    try {
      await api.post(`/approvals/${message.approval_id}/reject`, {
        rejection_reason: rejectReason,
      });
      onStatusChange?.(message.id, "rejected");
      setShowRejectInput(false);
      setRejectReason("");
    } catch {
      // ignore
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        <div className="whitespace-pre-wrap text-sm">{message.content}</div>

        {!isUser && message.confidence !== undefined && (
          <div className="flex items-center gap-3 mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                message.confidence >= 0.8
                  ? "bg-green-100 text-green-700"
                  : message.confidence >= 0.5
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {Math.round(message.confidence * 100)}% confidence
            </span>
            {message.model_used && (
              <span className="flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {message.model_used}
              </span>
            )}
            {message.latency_ms && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {Math.round(message.latency_ms)}ms
              </span>
            )}
          </div>
        )}

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              {showSources ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              {message.sources.length} source{message.sources.length > 1 ? "s" : ""}
            </button>
            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((source, i) => (
                  <div key={i} className="bg-white rounded-lg p-2 text-xs border">
                    <div className="font-medium text-gray-700">{source.title}</div>
                    <div className="text-gray-500 mt-1 line-clamp-2">{source.chunk}</div>
                    <div className="text-gray-400 mt-1">Relevance: {Math.round(source.score * 100)}%</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Show approve/reject for all AI messages that haven't been reviewed yet */}
        {message.approval_id && message.status !== "approved" && message.status !== "rejected" && (
          <div className="mt-3 pt-2 border-t border-gray-200">
            {message.status === "pending_approval" && (
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded font-medium">
                  Pending human review
                </span>
              </div>
            )}
            {!showRejectInput ? (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleApprove}
                  disabled={actionLoading}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {actionLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle className="h-3 w-3" />}
                  Approve
                </button>
                <button
                  onClick={() => setShowRejectInput(true)}
                  disabled={actionLoading}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                >
                  <XCircle className="h-3 w-3" />
                  Reject
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  type="text"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Rejection reason..."
                  className="w-full text-xs border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-red-300"
                  onKeyDown={(e) => e.key === "Enter" && handleReject()}
                />
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleReject}
                    disabled={actionLoading || !rejectReason.trim()}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                  >
                    {actionLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <XCircle className="h-3 w-3" />}
                    Confirm Reject
                  </button>
                  <button
                    onClick={() => { setShowRejectInput(false); setRejectReason(""); }}
                    className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Already reviewed status badges */}
        {message.status === "approved" && (
          <div className="mt-2 flex items-center gap-1 text-xs text-green-600">
            <CheckCircle className="h-3 w-3" />
            Approved
          </div>
        )}
        {message.status === "rejected" && (
          <div className="mt-2 flex items-center gap-1 text-xs text-red-600">
            <XCircle className="h-3 w-3" />
            Rejected
          </div>
        )}
      </div>
    </div>
  );
}
