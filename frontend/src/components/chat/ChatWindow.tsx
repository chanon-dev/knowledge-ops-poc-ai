"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Message } from "@/types";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";

interface ChatWindowProps {
  departmentId: string;
  conversationId?: string;
  onConversationCreated?: (id: string) => void;
}

export function ChatWindow({
  departmentId,
  conversationId,
  onConversationCreated,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentConvId, setCurrentConvId] = useState(conversationId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCurrentConvId(conversationId);
  }, [conversationId]);

  useEffect(() => {
    if (currentConvId) {
      loadMessages(currentConvId);
    } else {
      setMessages([]);
    }
  }, [currentConvId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadMessages = async (convId: string) => {
    try {
      const res = await api.get(`/conversations/${convId}`);
      setMessages(res.data.messages || []);
    } catch {
      // ignore
    }
  };

  const sendMessage = async (text: string, image?: File) => {
    const userMessage: Message = {
      id: String(Date.now()),
      conversation_id: currentConvId || "",
      role: "user",
      content: text,
      status: "completed",
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await api.post("/query", {
        text,
        department_id: departmentId,
        conversation_id: currentConvId || undefined,
      }, { timeout: 120_000 });

      const data = res.data;

      if (!currentConvId && data.conversation_id) {
        setCurrentConvId(data.conversation_id);
        onConversationCreated?.(data.conversation_id);
      }

      const aiMessage: Message = {
        id: data.message_id,
        conversation_id: data.conversation_id || currentConvId || "",
        role: "assistant",
        content: data.answer,
        confidence: data.confidence,
        sources: data.sources,
        model_used: data.model_used,
        latency_ms: data.latency_ms,
        status: data.needs_approval ? "pending_approval" : "completed",
        approval_id: data.approval_id || undefined,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Unknown error";
      const errorMessage: Message = {
        id: String(Date.now() + 1),
        conversation_id: currentConvId || "",
        role: "assistant",
        content: `Sorry, I encountered an error processing your request: ${detail}`,
        status: "error",
        created_at: new Date().toISOString(),
      };
      console.error("Chat error:", err?.response?.data || err);
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Ask a question to get started</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            onStatusChange={(msgId, newStatus) => {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === msgId ? { ...m, status: newStatus } : m
                )
              );
            }}
          />
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-gray-400 p-4">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <span className="text-sm">Thinking...</span>
          </div>
        )}
        <div ref={scrollRef} />
      </div>
      <ChatInput onSend={sendMessage} disabled={loading} />
    </div>
  );
}
