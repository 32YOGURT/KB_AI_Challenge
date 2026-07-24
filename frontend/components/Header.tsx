import Link from "next/link";
import { UserSwitcher } from "./UserSwitcher";

export function Header() {
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
            <nav className="hidden gap-6 text-sm text-white/70 sm:flex">
              <span className="cursor-default text-white">예금·적금</span>
              <span className="cursor-default hover:text-white">대출</span>
              <span className="cursor-default hover:text-white">연금·보험</span>
              <span className="cursor-default hover:text-white">공시자료</span>
            </nav>
          </div>
          <UserSwitcher />
        </div>
      </div>
    </header>
  );
}
