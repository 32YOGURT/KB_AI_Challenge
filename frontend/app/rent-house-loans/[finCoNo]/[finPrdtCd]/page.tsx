import { notFound } from "next/navigation";
import { DetailField } from "@/components/DetailField";
import { Header } from "@/components/Header";
import { fetchRentHouseLoanDetail } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function RentHouseLoanDetailPage({
  params,
}: {
  params: Promise<{ finCoNo: string; finPrdtCd: string }>;
}) {
  const { finCoNo, finPrdtCd } = await params;
  const product = await fetchRentHouseLoanDetail(finCoNo, finPrdtCd).catch(() => null);
  if (!product) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted font-data">{product.bank_name} · 전세자금대출</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">{product.product_name}</h1>
        <p className="mt-2 font-data text-lg font-semibold text-brand">
          {formatRate(product.min_rate, product.max_rate)}
        </p>

        <div className="mt-6 rounded-sm border border-line bg-panel p-6">
          <h2 className="mb-3 text-sm font-semibold text-ink">상환방식·금리유형별 금리</h2>
          <ul className="space-y-1 text-sm text-muted font-data">
            {product.rate_options.map((o, i) => (
              <li key={i}>
                {o.repay_type_nm} · {o.lend_rate_type_nm} — {o.lend_rate_min}~{o.lend_rate_max}%
                {o.lend_rate_avg != null ? ` (평균 ${o.lend_rate_avg}%)` : ""}
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-6 rounded-sm border border-line bg-panel px-6">
          <DetailField label="가입 방법" value={product.join_way} />
          <DetailField label="대출 한도" value={product.loan_limit} />
          <DetailField label="중도상환수수료" value={product.early_repay_fee} />
          <DetailField label="부대비용" value={product.loan_inci_expn} />
          <DetailField label="연체이자율" value={product.dly_rate} />
        </div>
      </main>
    </div>
  );
}
