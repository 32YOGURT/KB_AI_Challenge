import { Header } from "@/components/Header";
import { fetchCompanies } from "@/lib/api";

export default async function DisclosuresPage() {
  const companies = await fetchCompanies();

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h2 className="mb-3 text-lg font-semibold text-ink">공시 금융회사</h2>
        <ul className="overflow-hidden rounded-sm border border-line bg-panel">
          {companies.map((c, i) => (
            <li
              key={c.fin_co_no}
              className={`grid grid-cols-[10rem_1fr_10rem] items-center gap-4 px-5 py-4 ${
                i !== 0 ? "border-t border-line" : ""
              }`}
            >
              <span className="font-medium text-ink">{c.bank_name}</span>
              <span className="text-sm text-muted">
                {c.areas.length > 0 ? c.areas.join(", ") : "전국"}
              </span>
              <span className="text-right text-sm text-muted font-data">{c.call_center}</span>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
