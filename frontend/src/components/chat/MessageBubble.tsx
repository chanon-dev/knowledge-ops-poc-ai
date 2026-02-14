"use client";

import { useState } from "react";
import { Message } from "@/types";
import { ChevronDown, ChevronUp, Clock, Cpu } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === "user";

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

        {message.status === "pending_approval" && (
          <div className="mt-2 text-xs bg-yellow-50 text-yellow-700 px-2 py-1 rounded">
            Pending human review
          </div>
        )}
      </div>
    </div>
  );
}
