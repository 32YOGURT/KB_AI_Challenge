import { Header } from "@/components/Header";
import { RateProductList } from "@/components/RateProductList";
import { fetchMortgageLoans } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function MortgageLoansPage() {
  const loans = await fetchMortgageLoans();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h2 className="mb-3 text-lg font-semibold text-ink">주택담보대출</h2>
        <RateProductList
          rows={loans.map((p) => ({
            key: `${p.fin_co_no}-${p.fin_prdt_cd}`,
            bank: p.bank_name,
            name: p.product_name,
            note: p.repay_types.join(", "),
            rate: formatRate(p.min_rate, p.max_rate),
          }))}
        />
      </main>
    </div>
  );
}
