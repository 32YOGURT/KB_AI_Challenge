"use client";

import { useUser } from "@/context/UserContext";

export function UserSwitcher() {
  const { users, activeUser, setActiveUserId, loading } = useUser();

  if (loading) {
    return <div className="h-8 w-56 animate-pulse rounded-full bg-white/10" />;
  }

  return (
    <div className="flex items-center gap-1 rounded-full border border-white/20 bg-white/5 p-1">
      <span className="px-2 text-[11px] tracking-wide text-white/50 font-data">
        체험 프로필
      </span>
      {users.map((u) => (
        <button
          key={u.id}
          onClick={() => setActiveUserId(u.id)}
          className={`rounded-full px-3 py-1 text-sm font-medium transition-colors ${
            activeUser?.id === u.id
              ? "bg-gold text-white"
              : "text-white/70 hover:text-white"
          }`}
        >
          {u.display_name}
        </button>
      ))}
    </div>
  );
}
