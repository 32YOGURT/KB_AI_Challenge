"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserSwitcher } from "./UserSwitcher";

const NAV_ITEMS = [
  { label: "예금", href: "/deposits" },
  { label: "적금", href: "/savings" },
  { label: "주택담보대출", href: "/mortgage-loans" },
  { label: "전세자금대출", href: "/rent-house-loans" },
  { label: "개인신용대출", href: "/credit-loans" },
  { label: "개인사업자대출", href: "/business-loans" },
  { label: "공시자료", href: "/disclosures" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="bg-brand text-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3 text-xs text-white/60 font-data">
        <span>전국은행연합회 · 금융상품통합비교공시</span>
        <span>고객센터 1577-0000</span>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-8">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              금융상품<span className="text-gold">한눈에</span>
            </Link>
            <nav className="hidden flex-wrap gap-x-5 gap-y-1 text-sm text-white/70 lg:flex">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={pathname === item.href ? "text-white" : "hover:text-white"}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <UserSwitcher />
        </div>
      </div>
    </header>
  );
}
