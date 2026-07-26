import { notFound } from "next/navigation";
import { DetailField } from "@/components/DetailField";
import { Header } from "@/components/Header";
import { fetchSavingDetail } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function SavingDetailPage({
  params,
}: {
  params: Promise<{ finCoNo: string; finPrdtCd: string }>;
}) {
  const { finCoNo, finPrdtCd } = await params;
  const product = await fetchSavingDetail(finCoNo, finPrdtCd).catch(() => null);
  if (!product) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted font-data">{product.bank_name} · 적금</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">{product.product_name}</h1>
        <p className="mt-2 font-data text-lg font-semibold text-brand">
          {formatRate(product.min_rate, product.max_rate)}
        </p>
        <p className="mt-1 text-sm text-muted">{product.reserve_types.join(", ")}</p>

        <div className="mt-6 rounded-sm border border-line bg-panel p-6">
          <h2 className="mb-3 text-sm font-semibold text-ink">만기별 금리</h2>
          <ul className="space-y-1 text-sm text-muted font-data">
            {product.rate_options.map((o, i) => (
              <li key={i}>
                {o.term_months != null ? `${o.term_months}개월` : "-"} · 기본 {o.base_rate ?? "-"}% / 우대{" "}
                {o.preferential_rate ?? "-"}%
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-6 rounded-sm border border-line bg-panel px-6">
          <DetailField label="가입 방법" value={product.join_way} />
          <DetailField label="가입 대상" value={product.join_member} />
          <DetailField label="가입 제한" value={product.join_deny} />
          <DetailField label="우대조건" value={product.spcl_cnd} />
          <DetailField label="만기 후 이자율" value={product.mtrt_int} />
          <DetailField label="기타 유의사항" value={product.etc_note} />
        </div>
      </main>
    </div>
  );
}
