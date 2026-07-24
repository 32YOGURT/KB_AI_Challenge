"use client";

import { useUser } from "@/context/UserContext";

function won(n: number) {
  return `${Math.round(n / 10000).toLocaleString("ko-KR")}만원`;
}

export function UserSwitcher() {
  const { users, activeUser, setActiveUserId, loading } = useUser();

  if (loading) {
    return <div className="h-16 w-64 animate-pulse rounded bg-white/10" />;
  }

  return (
    <div className="flex flex-col items-end gap-1.5">
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
      {activeUser && (
        <p className="text-[11px] text-white/45 font-data">
          비상금 {won(activeUser.emergency_fund)} · 월 대중교통 {activeUser.monthly_transit_count}회
        </p>
      )}
    </div>
  );
}
