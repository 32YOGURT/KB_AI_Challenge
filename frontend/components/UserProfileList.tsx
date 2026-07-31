"use client";

import { useEffect, useState } from "react";
import { fetchUserSignals } from "@/lib/api";
import { useUser } from "@/context/UserContext";
import type { UserSignals } from "@/lib/types";

const won = (v: number) => `${Math.round(v).toLocaleString("ko-KR")}원`;

/** "20270101" -> "2027-01-01" */
const yyyymmdd = (v: string) =>
  /^\d{8}$/.test(v) ? `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6)}` : v;

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <span className="shrink-0 text-xs text-muted font-data">{label}</span>
      <span className="min-w-0 text-right text-sm text-ink">{value}</span>
    </div>
  );
}

function SignalDetail({ signals }: { signals: UserSignals | null | undefined }) {
  if (signals === undefined) {
    return <p className="py-4 text-sm text-muted font-data">마이데이터 조회 중…</p>;
  }
  if (signals === null) {
    return <p className="py-4 text-sm text-risk-red">신호를 불러오지 못했습니다.</p>;
  }

  const { liquidity: liq, asset_distribution: dist } = signals;

  return (
    <div className="mt-4 space-y-5">
      <section>
        <h3 className="mb-1 text-[11px] uppercase tracking-[0.15em] text-muted font-data">
          유동성
        </h3>
        <div className="divide-y divide-line border-y border-line">
          <Row label="총 잔액" value={won(liq.balance_amt)} />
          <Row label="출금 가능액" value={won(liq.withdrawable_amt)} />
          <Row
            label="최근 순현금흐름"
            value={
              <span className={liq.recent_net_cash_flow < 0 ? "text-risk-red" : "text-risk-green"}>
                {liq.recent_net_cash_flow >= 0 ? "+" : ""}
                {won(liq.recent_net_cash_flow)}
              </span>
            }
          />
          <Row label="거래 건수" value={`${liq.transaction_count}건`} />
        </div>
      </section>

      <section>
        <h3 className="mb-1 text-[11px] uppercase tracking-[0.15em] text-muted font-data">
          금융사별 자산
        </h3>
        <div className="divide-y divide-line border-y border-line">
          {dist.by_institution.length === 0 ? (
            <Row label="—" value={<span className="text-muted">연동된 예금·적금 없음</span>} />
          ) : (
            dist.by_institution.map((inst) => (
              <Row
                key={inst.org_code}
                label={inst.org_code}
                value={
                  <>
                    {won(inst.total_balance)}
                    {inst.is_over_protection_limit && (
                      <span className="ml-2 text-xs text-risk-red">예금자보호 한도 초과</span>
                    )}
                  </>
                }
              />
            ))
          )}
        </div>
      </section>

      <section>
        <h3 className="mb-1 text-[11px] uppercase tracking-[0.15em] text-muted font-data">
          만기 예정
        </h3>
        <div className="divide-y divide-line border-y border-line">
          {dist.upcoming_maturities.length === 0 ? (
            <Row label="—" value={<span className="text-muted">없음</span>} />
          ) : (
            dist.upcoming_maturities.map((m) => (
              <Row
                key={m.account_num}
                label={yyyymmdd(m.exp_date)}
                value={`${m.org_code} ${m.prod_name}`}
              />
            ))
          )}
        </div>
      </section>

      <section>
        <h3 className="mb-1 text-[11px] uppercase tracking-[0.15em] text-muted font-data">
          카드 실적 (카테고리별)
        </h3>
        <div className="divide-y divide-line border-y border-line">
          {signals.card_category.by_category.length === 0 ? (
            <Row label="—" value={<span className="text-muted">카드 승인내역 없음</span>} />
          ) : (
            signals.card_category.by_category.map((c) => (
              <Row key={c.category} label={c.category} value={`${c.count}건 · ${won(c.total_amt)}`} />
            ))
          )}
        </div>
      </section>
    </div>
  );
}

export function UserProfileList() {
  const { users, activeUser, setActiveUserId, loading } = useUser();
  const [signals, setSignals] = useState<Record<string, UserSignals | null>>({});

  useEffect(() => {
    if (users.length === 0) return;
    let cancelled = false;
    Promise.all(
      users.map((u) =>
        fetchUserSignals(u.id)
          .then((s) => [u.id, s] as const)
          .catch(() => [u.id, null] as const),
      ),
    ).then((entries) => {
      if (!cancelled) setSignals(Object.fromEntries(entries));
    });
    return () => {
      cancelled = true;
    };
  }, [users]);

  if (loading) {
    return <p className="text-sm text-muted font-data">체험 프로필 불러오는 중…</p>;
  }

  if (users.length === 0) {
    return (
      <p className="text-sm text-ink">
        체험 프로필을 불러오지 못했습니다. 백엔드 서버 상태를 확인해주세요.
      </p>
    );
  }

  return (
    <div className="grid gap-5 md:grid-cols-2">
      {users.map((u) => {
        const active = activeUser?.id === u.id;
        return (
          <section
            key={u.id}
            className={`rounded-sm border bg-panel p-6 transition-colors ${
              active ? "border-brand" : "border-line"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="text-lg font-semibold text-ink">{u.display_name}</h2>
                <p className="text-[11px] text-muted font-data">{u.id}</p>
              </div>
              {active ? (
                <span className="shrink-0 rounded-full bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
                  선택됨
                </span>
              ) : (
                <button
                  onClick={() => setActiveUserId(u.id)}
                  className="shrink-0 rounded-full border border-brand/30 px-3 py-1 text-xs font-semibold text-brand transition-colors hover:bg-brand/5"
                >
                  이 유저로 전환
                </button>
              )}
            </div>

            {u.description && (
              <p className="mt-3 text-sm leading-relaxed text-ink/80">{u.description}</p>
            )}

            <SignalDetail signals={signals[u.id]} />
          </section>
        );
      })}
    </div>
  );
}
