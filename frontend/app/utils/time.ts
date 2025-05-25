export const formatTime = (date: Date): string =>
  date.toLocaleTimeString("ja-JP", { hour: "2-digit", minute: "2-digit" });
