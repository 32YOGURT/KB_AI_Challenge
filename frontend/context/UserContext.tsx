"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { UserProfile } from "@/lib/types";
import { fetchUsers } from "@/lib/api";

const STORAGE_KEY = "finmark.activeUserId";

interface UserContextValue {
  users: UserProfile[];
  activeUser: UserProfile | null;
  setActiveUserId: (id: string) => void;
  loading: boolean;
}

const UserContext = createContext<UserContextValue | null>(null);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [activeUserId, setActiveUserIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsers()
      .then((fetched) => {
        setUsers(fetched);
        const stored = window.localStorage.getItem(STORAGE_KEY);
        const initial = fetched.find((u) => u.id === stored)?.id ?? fetched[0]?.id ?? null;
        setActiveUserIdState(initial);
      })
      .catch(() => setUsers([])) // 백엔드가 죽어있어도 unhandledRejection 대신 안내 화면으로
      .finally(() => setLoading(false));
  }, []);

  const setActiveUserId = (id: string) => {
    setActiveUserIdState(id);
    window.localStorage.setItem(STORAGE_KEY, id);
  };

  const activeUser = useMemo(
    () => users.find((u) => u.id === activeUserId) ?? null,
    [users, activeUserId],
  );

  return (
    <UserContext.Provider value={{ users, activeUser, setActiveUserId, loading }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}
