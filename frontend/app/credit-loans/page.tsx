import { Header } from "@/components/Header";
import { RateProductList } from "@/components/RateProductList";
import { fetchCreditLoans } from "@/lib/api";
import { formatRate } from "@/lib/format";

export default async function CreditLoansPage() {
  const loans = await fetchCreditLoans();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h2 className="mb-3 text-lg font-semibold text-ink">개인신용대출</h2>
        <RateProductList
          rows={loans.map((p) => ({
            key: `${p.fin_co_no}-${p.fin_prdt_cd}`,
            bank: p.bank_name,
            name: p.product_name,
            note: p.cb_name,
            rate: formatRate(p.best_grade_rate, p.worst_grade_rate),
          }))}
        />
      </main>
    </div>
  );
}
