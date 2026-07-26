import { notFound } from "next/navigation";
import { DetailField } from "@/components/DetailField";
import { Header } from "@/components/Header";
import { fetchBusinessLoanDetail } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function BusinessLoanDetailPage({
  params,
}: {
  params: Promise<{ finCoNo: string; finPrdtCd: string }>;
}) {
  const { finCoNo, finPrdtCd } = await params;
  const product = await fetchBusinessLoanDetail(finCoNo, finPrdtCd).catch(() => null);
  if (!product) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted font-data">{product.bank_name} · 개인사업자대출</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">{product.product_name}</h1>
        <p className="mt-2 font-data text-lg font-semibold text-brand">
          {formatRate(product.min_rate, product.max_rate)}
        </p>
        <p className="mt-1 text-sm text-muted">
          {product.fin_prdt_type_nm} · {product.loan_type} · {product.use_way}
        </p>

        <div className="mt-6 rounded-sm border border-line bg-panel px-6">
          <DetailField label="가입 방법" value={product.join_way} />
          <DetailField label="대출 한도" value={product.loan_limit} />
          <DetailField label="대출 한도 상세" value={product.loan_limit_detl} />
          <DetailField label="대출 제한 상세" value={product.join_deny_detl ?? ""} />
          <DetailField label="대출 기간" value={product.loan_term} />
          <DetailField label="중도상환수수료" value={product.early_repay_fee} />
          <DetailField label="부대비용" value={product.loan_inci_expn} />
          <DetailField label="연체이자율" value={product.dly_rate} />
        </div>
      </main>
    </div>
  );
}
