import type { CatalogProduct } from "@/lib/types";
import { SignupFlow } from "./SignupFlow";

function groupBySubCategory(products: CatalogProduct[]): Map<string, CatalogProduct[]> {
  const groups = new Map<string, CatalogProduct[]>();
  for (const p of products) {
    const list = groups.get(p.sub_category) ?? [];
    list.push(p);
    groups.set(p.sub_category, list);
  }
  return groups;
}

export function CatalogList({ products }: { products: CatalogProduct[] }) {
  const groups = groupBySubCategory(products);

  return (
    <div className="space-y-10">
      {[...groups.entries()].map(([subCategory, items]) => (
        <section key={subCategory}>
          <h2 className="mb-3 text-lg font-semibold text-ink">{subCategory}</h2>
          <ul className="overflow-hidden rounded-sm border border-line bg-panel">
            {items.map((p, i) => (
              <li
                key={p.product_id}
                className={`flex items-center gap-4 px-5 py-4 ${i !== 0 ? "border-t border-line" : ""}`}
              >
                <a
                  href={p.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="min-w-0 flex-1 hover:underline"
                >
                  <span className="block font-medium text-ink">{p.name}</span>
                  <span className="mt-0.5 block text-sm text-muted">{p.bank}</span>
                </a>
                <SignupFlow productId={p.product_id} compact />
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
