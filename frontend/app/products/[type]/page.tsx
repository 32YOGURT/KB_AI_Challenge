import { notFound } from "next/navigation";
import { CatalogList } from "@/components/CatalogList";
import { Header } from "@/components/Header";
import { fetchCatalog } from "@/lib/api";
import { PRODUCT_TYPE_SLUGS } from "@/lib/categories";

export default async function ProductTypePage({
  params,
}: {
  params: Promise<{ type: string }>;
}) {
  const { type: slug } = await params;
  const productType = PRODUCT_TYPE_SLUGS[slug];
  if (!productType) notFound();

  const products = await fetchCatalog(productType);
  if (products.length === 0) notFound();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-6 text-2xl font-semibold text-ink">{productType}</h1>
        <CatalogList products={products} />
      </main>
    </div>
  );
}
