"use client";

import { CreditCard, Check } from "lucide-react";

const plans = [
  { name: "Free", price: "$0", features: ["50 queries/day", "1 department", "5 users", "Community support"], current: false },
  { name: "Professional", price: "$499/mo", features: ["500 queries/day", "5 departments", "25 users", "Custom models", "Priority support"], current: true },
  { name: "Enterprise", price: "Custom", features: ["Unlimited queries", "Unlimited departments", "Unlimited users", "BYOD/On-premise", "Dedicated support", "SLA guarantee"], current: false },
];

export default function BillingPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Billing & Subscription</h2>

      <div className="bg-white rounded-xl border p-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium">Current Plan: Professional</h3>
            <p className="text-sm text-gray-500 mt-1">Billed monthly. Next invoice: March 1, 2026</p>
          </div>
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-gray-400" />
            <span className="text-sm text-gray-500">**** 4242</span>
          </div>
        </div>
        <div className="mt-4 bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span>Queries used today</span>
            <span className="font-medium">127 / 500</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-500 rounded-full h-2" style={{ width: "25.4%" }} />
          </div>
        </div>
      </div>

      <h3 className="font-medium mb-4">Plans</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {plans.map((plan) => (
          <div key={plan.name} className={`rounded-xl border p-6 ${plan.current ? "border-blue-300 ring-1 ring-blue-200" : ""}`}>
            {plan.current && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full mb-3 inline-block">Current</span>}
            <h4 className="text-lg font-bold">{plan.name}</h4>
            <p className="text-2xl font-bold mt-2">{plan.price}</p>
            <ul className="mt-4 space-y-2">
              {plan.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-green-500" />
                  {f}
                </li>
              ))}
            </ul>
            {!plan.current && (
              <button className="w-full mt-4 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg text-sm hover:bg-blue-50">
                {plan.name === "Enterprise" ? "Contact Sales" : "Upgrade"}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
