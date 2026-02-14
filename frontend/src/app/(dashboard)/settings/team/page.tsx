"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { UserPlus } from "lucide-react";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  last_login_at: string | null;
  created_at: string;
}

export default function TeamPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [showInvite, setShowInvite] = useState(false);
  const [form, setForm] = useState({ email: "", full_name: "", role: "member", password: "changeme123" });

  useEffect(() => { loadUsers(); }, []);

  const loadUsers = async () => {
    try {
      const res = await api.get("/users");
      setUsers(res.data.data || []);
    } catch {}
  };

  const handleInvite = async () => {
    try {
      await api.post("/users", form);
      setShowInvite(false);
      setForm({ email: "", full_name: "", role: "member", password: "changeme123" });
      loadUsers();
    } catch {}
  };

  const roleColors: Record<string, string> = {
    owner: "bg-purple-100 text-purple-700",
    admin: "bg-blue-100 text-blue-700",
    member: "bg-gray-100 text-gray-700",
    viewer: "bg-green-100 text-green-700",
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Team</h2>
        <button onClick={() => setShowInvite(true)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
          <UserPlus className="h-4 w-4" /> Invite User
        </button>
      </div>

      {showInvite && (
        <div className="bg-white rounded-xl border p-6 mb-6">
          <h3 className="font-medium mb-4">Invite Team Member</h3>
          <div className="grid grid-cols-2 gap-4">
            <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="border rounded-lg px-3 py-2 text-sm" />
            <input placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} className="border rounded-lg px-3 py-2 text-sm" />
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="border rounded-lg px-3 py-2 text-sm">
              <option value="member">Member</option>
              <option value="admin">Admin</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleInvite} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Send Invite</button>
            <button onClick={() => setShowInvite(false)} className="px-4 py-2 bg-gray-100 rounded-lg text-sm">Cancel</button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 text-left text-sm text-gray-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Last Login</th>
              <th className="px-4 py-3">Joined</th>
            </tr>
          </thead>
          <tbody className="divide-y text-sm">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-4 py-3 font-medium">{user.full_name}</td>
                <td className="px-4 py-3 text-gray-500">{user.email}</td>
                <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs ${roleColors[user.role] || ""}`}>{user.role}</span></td>
                <td className="px-4 py-3 text-gray-500">{user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : "Never"}</td>
                <td className="px-4 py-3 text-gray-500">{new Date(user.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
