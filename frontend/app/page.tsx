import Link from "next/link";
import { Header } from "@/components/Header";
import { fetchCatalog } from "@/lib/api";
import { SLUG_BY_PRODUCT_TYPE } from "@/lib/categories";

export default async function Home() {
  const products = await fetchCatalog();
  const counts = new Map<string, number>();
  for (const p of products) {
    counts.set(p.product_type, (counts.get(p.product_type) ?? 0) + 1);
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <p className="text-sm text-muted font-data">전 은행 상품 비교공시</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">예금·적금 상품 한눈에</h1>
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
          {[...counts.entries()].map(([productType, count]) => (
            <Link
              key={productType}
              href={`/products/${SLUG_BY_PRODUCT_TYPE[productType] ?? encodeURIComponent(productType)}`}
              className="rounded-sm border border-line bg-panel p-6 transition-colors hover:bg-[#F7F8FB]"
            >
              <p className="text-lg font-semibold text-ink">{productType}</p>
              <p className="mt-1 text-sm text-muted">{count}개 상품</p>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
