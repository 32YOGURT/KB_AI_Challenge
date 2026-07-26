export function formatRate(min: number | null, max: number | null): string {
  if (min == null && max == null) return "-";
  if (min != null && max != null && min !== max) {
    return `연 ${min.toFixed(2)}~${max.toFixed(2)}%`;
  }
  return `연 ${(max ?? min)!.toFixed(2)}%`;
}
