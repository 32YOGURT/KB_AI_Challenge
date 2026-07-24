import Link from "next/link";
import { notFound } from "next/navigation";
import { Header } from "@/components/Header";
import { SignupFlow } from "@/components/SignupFlow";
import { fetchProduct } from "@/lib/api";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const product = await fetchProduct(id).catch(() => null);
  if (!product) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <Link href="/" className="text-sm text-muted hover:text-ink">
          ← 목록으로
        </Link>

        <div className="mt-4 rounded-sm border border-line bg-panel p-8">
          <p className="text-sm text-muted font-data">{product.bank} · {product.category}</p>
          <h1 className="mt-1 text-2xl font-semibold text-ink">{product.name}</h1>
          <p className="mt-2 text-sm text-muted">{product.description}</p>

          <div className="mt-6 grid grid-cols-3 gap-4 border-y border-line py-5">
            <div>
              <p className="text-xs text-muted font-data">기본금리</p>
              <p className="mt-1 text-lg font-semibold text-ink">연 {product.base_rate}%</p>
            </div>
            <div>
              <p className="text-xs text-muted font-data">최고 우대금리</p>
              <p className="mt-1 text-lg font-semibold text-brand">{product.headline_rate}</p>
            </div>
            <div>
              <p className="text-xs text-muted font-data">가입기간</p>
              <p className="mt-1 text-lg font-semibold text-ink">{product.min_period_months}개월</p>
            </div>
          </div>

          <p className="mt-5 text-xs leading-relaxed text-muted">
            우대금리는 은행이 정한 세부 조건 충족 시 적용되며, 중도해지 시 약정금리가 변경될 수
            있습니다. 자세한 사항은 상품설명서 및 약관을 참고하시기 바랍니다.
          </p>

          <div className="mt-7">
            <SignupFlow productId={product.id} />
          </div>
        </div>
      </main>
    </div>
  );
}
