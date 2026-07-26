import { Header } from "@/components/Header";
import { RateProductList } from "@/components/RateProductList";
import { fetchSavings } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function SavingsPage() {
  const savings = await fetchSavings();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h2 className="mb-3 text-lg font-semibold text-ink">적금</h2>
        <RateProductList
          rows={savings.map((p) => ({
            key: `${p.fin_co_no}-${p.fin_prdt_cd}`,
            href: `/savings/${encodeURIComponent(p.fin_co_no)}/${encodeURIComponent(p.fin_prdt_cd)}`,
            bank: p.bank_name,
            name: p.product_name,
            note: p.reserve_types.join(", "),
            rate: formatRate(p.min_rate, p.max_rate),
          }))}
        />
      </main>
    </div>
  );
}
