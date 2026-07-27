import { notFound } from "next/navigation";
import { CatalogList } from "@/components/CatalogList";
import { Header } from "@/components/Header";
import { fetchCatalog } from "@/lib/api";

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ category: string }>;
}) {
  const { category } = await params;
  const products = await fetchCatalog(category);
  if (products.length === 0) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-6 text-2xl font-semibold text-ink">{category}</h1>
        <CatalogList products={products} />
      </main>
    </div>
  );
}
