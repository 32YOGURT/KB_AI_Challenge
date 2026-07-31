"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useUser } from "@/context/UserContext";

export function UserSwitcher() {
  const { users, activeUser, setActiveUserId, loading } = useUser();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  if (loading) {
    return <div className="h-8 w-44 animate-pulse rounded-full bg-white/10" />;
  }

  return (
    <div ref={rootRef} className="relative shrink-0">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className="flex items-center gap-2 rounded-full border border-white/20 bg-white/5 py-1.5 pl-3 pr-2.5 transition-colors hover:bg-white/10"
      >
        <span className="text-[11px] tracking-wide text-white/50 font-data">체험 프로필</span>
        <span className="text-sm font-medium text-white">
          {activeUser?.display_name ?? "선택"}
        </span>
        <span className={`text-[10px] text-white/50 transition-transform ${open ? "rotate-180" : ""}`}>
          ▼
        </span>
      </button>

      {open && (
        <div
          role="listbox"
          className="animate-fade-in absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-sm border border-line bg-panel shadow-xl"
        >
          <ul className="divide-y divide-line">
            {users.map((u) => {
              const active = activeUser?.id === u.id;
              return (
                <li key={u.id}>
                  <button
                    role="option"
                    aria-selected={active}
                    onClick={() => {
                      setActiveUserId(u.id);
                      setOpen(false);
                    }}
                    className={`w-full px-4 py-3 text-left transition-colors ${
                      active ? "bg-brand/5" : "hover:bg-paper"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span
                        className={`text-sm font-semibold ${active ? "text-brand" : "text-ink"}`}
                      >
                        {u.display_name}
                      </span>
                      {active && <span className="text-xs text-brand">✓</span>}
                    </span>
                    {u.description && (
                      <span className="mt-0.5 block text-xs leading-relaxed text-muted">
                        {u.description}
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>

          <Link
            href="/user-profile"
            onClick={() => setOpen(false)}
            className="block border-t border-line bg-paper px-4 py-2.5 text-xs font-medium text-brand transition-colors hover:bg-[#E9ECF4]"
          >
            프로필 데이터 자세히 보기 →
          </Link>
        </div>
      )}
    </div>
  );
}
