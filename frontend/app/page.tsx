import Link from "next/link";
import { Header } from "@/components/Header";
import { fetchCatalog } from "@/lib/api";
import { CATEGORY_SLUGS } from "@/lib/categories";

const SLUG_BY_CATEGORY = Object.fromEntries(
  Object.entries(CATEGORY_SLUGS).map(([slug, category]) => [category, slug]),
);

export default async function Home() {
  const products = await fetchCatalog();
  const counts = new Map<string, number>();
  for (const p of products) {
    counts.set(p.category, (counts.get(p.category) ?? 0) + 1);
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <p className="text-sm text-muted font-data">전 은행 상품 비교공시</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">예금·적금 상품 한눈에</h1>
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
          {[...counts.entries()].map(([category, count]) => (
            <Link
              key={category}
              href={`/products/${SLUG_BY_CATEGORY[category] ?? encodeURIComponent(category)}`}
              className="rounded-sm border border-line bg-panel p-6 transition-colors hover:bg-[#F7F8FB]"
            >
              <p className="text-lg font-semibold text-ink">{category}</p>
              <p className="mt-1 text-sm text-muted">{count}개 상품</p>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
