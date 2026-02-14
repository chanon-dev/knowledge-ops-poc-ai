"use client";

import Link from "next/link";
import { Building2, Key, Users, CreditCard, Palette, Webhook, Brain, Plug } from "lucide-react";

const settingsItems = [
  { href: "/settings/departments", label: "Departments", description: "Manage departments, configs, and members", icon: Building2 },
  { href: "/settings/api-keys", label: "API Keys", description: "Generate and manage API keys", icon: Key },
  { href: "/settings/team", label: "Team", description: "Invite and manage team members", icon: Users },
  { href: "/settings/billing", label: "Billing", description: "Subscription, usage, and invoices", icon: CreditCard },
  { href: "/settings/white-label", label: "White Label", description: "Customize branding, colors, and logo", icon: Palette },
  { href: "/settings/webhooks", label: "Webhooks", description: "Configure event notifications", icon: Webhook },
  { href: "/settings/models", label: "Models", description: "Fine-tuned model management", icon: Brain },
];

export default function SettingsPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Settings</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {settingsItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="bg-white rounded-xl border p-6 hover:border-blue-300 transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-blue-50 flex items-center justify-center">
                <item.icon className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-medium">{item.label}</h3>
                <p className="text-sm text-gray-500">{item.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
