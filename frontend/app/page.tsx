import { Header } from "@/components/Header";
import { ProductTable } from "@/components/ProductTable";
import { fetchProducts } from "@/lib/api";

export default async function Home() {
  const products = await fetchProducts();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <p className="text-sm text-muted font-data">전 은행 상품 비교공시</p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">예금·적금·대출 상품 한눈에</h1>
          </div>
          <p className="max-w-xs text-right text-xs text-muted">
            공시 기준일 기준으로 제공되며 실제 조건은 각 은행 상품설명서를 따릅니다.
          </p>
        </div>
        <ProductTable products={products} />
      </main>
    </div>
  );
}
