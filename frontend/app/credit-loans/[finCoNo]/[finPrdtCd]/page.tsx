import { notFound } from "next/navigation";
import { DetailField } from "@/components/DetailField";
import { Header } from "@/components/Header";
import { fetchCreditLoanDetail } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function CreditLoanDetailPage({
  params,
}: {
  params: Promise<{ finCoNo: string; finPrdtCd: string }>;
}) {
  const { finCoNo, finPrdtCd } = await params;
  const product = await fetchCreditLoanDetail(finCoNo, finPrdtCd).catch(() => null);
  if (!product) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted font-data">{product.bank_name} · 개인신용대출</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">{product.product_name}</h1>
        <p className="mt-2 font-data text-lg font-semibold text-brand">
          {formatRate(product.best_grade_rate, product.worst_grade_rate)}
        </p>
        <p className="mt-1 text-sm text-muted">
          {product.cb_name} · {product.crdt_lend_rate_type_nm}
        </p>

        <div className="mt-6 rounded-sm border border-line bg-panel p-6">
          <h2 className="mb-3 text-sm font-semibold text-ink">신용점수 구간별 금리</h2>
          <p className="mb-2 text-xs text-muted">
            구간이 가리키는 실제 점수 범위는 FSS 원본 문서 확인이 필요해 필드명 그대로 표시합니다.
          </p>
          <ul className="space-y-1 text-sm text-muted font-data">
            {product.grade_rates.map((g) => (
              <li key={g.field}>
                {g.field}: {g.rate}%
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-6 rounded-sm border border-line bg-panel px-6">
          <DetailField label="가입 방법" value={product.join_way} />
        </div>
      </main>
    </div>
  );
}
