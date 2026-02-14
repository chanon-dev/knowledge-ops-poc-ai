"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Department } from "@/types";
import { DepartmentSelector } from "@/components/chat/DepartmentSelector";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { Plus } from "lucide-react";

export default function ChatPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();

  useEffect(() => {
    api.get("/departments").then((res) => {
      const depts = res.data.data || [];
      setDepartments(depts);
      if (depts.length > 0) setSelectedDeptId(depts[0].id);
    }).catch(() => { });
  }, []);

  const handleNewConversation = () => {
    setConversationId(undefined);
  };

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <DepartmentSelector
          departments={departments}
          selectedId={selectedDeptId}
          onSelect={(id) => {
            setSelectedDeptId(id);
            setConversationId(undefined);
          }}
        />
        <button
          onClick={handleNewConversation}
          className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {selectedDeptId ? (
        <div className="flex-1 bg-white rounded-xl border shadow-sm overflow-hidden">
          <ChatWindow
            departmentId={selectedDeptId}
            conversationId={conversationId}
            onConversationCreated={(id) => setConversationId(id)}
          />
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          Select a department to start chatting
        </div>
      )}
    </div>
  );
}
