import type { MachineStatus } from "../../types";
// CSS 可以選擇用 CSS Modules，或者直接沿用全域 CSS 但加上特定 Class
// 為了簡化展示，這裡假設樣式已在 App.css 定義，但這是一個獨立元件

interface Props {
  status: MachineStatus;
}

export function StatusBadge({ status }: Props) {
  return (
    <span className={`status-pill status-pill--${status}`}>
      {status}
    </span>
  );
}