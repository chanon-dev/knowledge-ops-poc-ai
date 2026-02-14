"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { History, MessageSquare, Trash2 } from "lucide-react";

interface ConversationItem {
  id: string;
  title: string | null;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  status: string;
}

interface ConversationListProps {
  departmentId: string;
  activeConversationId?: string;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
  refreshKey?: number;
}

export function ConversationList({
  departmentId,
  activeConversationId,
  onSelect,
  onDelete,
  refreshKey,
}: ConversationListProps) {
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
  }, [departmentId, refreshKey]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const res = await api.get("/conversations", {
        params: { department_id: departmentId, limit: 50 },
      });
      setConversations(res.data.data || res.data || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const deleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    try {
      await api.delete(`/conversations/${id}`);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      onDelete?.(id);
    } catch {
      // ignore
    }
  };

  const handleSelect = (id: string) => {
    onSelect(id);
    setOpen(false);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1 px-3 py-2 text-sm border rounded-lg hover:bg-gray-50 text-gray-700"
      >
        <History className="h-4 w-4" />
        History
        {conversations.length > 0 && (
          <span className="ml-1 text-xs bg-gray-200 text-gray-600 rounded-full px-1.5">
            {conversations.length}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-white rounded-xl border shadow-lg z-50 overflow-hidden">
          <div className="max-h-96 overflow-y-auto">
            {loading && conversations.length === 0 ? (
              <div className="p-4 text-xs text-gray-400 text-center">
                Loading...
              </div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-xs text-gray-400 text-center">
                No conversations yet
              </div>
            ) : (
              <div className="py-1">
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => handleSelect(conv.id)}
                    className={`group flex items-start gap-2 px-3 py-2.5 text-left text-sm transition-colors w-full ${
                      activeConversationId === conv.id
                        ? "bg-blue-50 text-blue-700"
                        : "text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    <MessageSquare className="h-4 w-4 mt-0.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="truncate font-medium">
                        {conv.title || "Untitled conversation"}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <span>{conv.message_count} msgs</span>
                        <span>{formatDate(conv.last_message_at || conv.created_at)}</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => deleteConversation(conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 hover:text-red-500 transition-opacity"
                      title="Delete conversation"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
