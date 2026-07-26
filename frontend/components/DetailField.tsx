export function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-t border-line py-3 first:border-t-0">
      <p className="text-xs text-muted font-data">{label}</p>
      <p className="mt-1 whitespace-pre-line text-sm leading-relaxed text-ink">{value || "-"}</p>
    </div>
  );
}
