/**
 * ISO 8601形式の日時文字列を日本語形式で表示
 * @param isoString ISO 8601形式の日時文字列
 * @returns 日本語形式の日時文字列（例: "2024年12月29日 15:30:45"）
 */
export function formatDateTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * ISO 8601形式の日時文字列を日本語の日付形式で表示
 * @param isoString ISO 8601形式の日時文字列
 * @returns 日本語形式の日付文字列（例: "2024年12月29日"）
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Unixタイムスタンプ（秒）を日本語形式で表示
 * @param timestamp Unixタイムスタンプ（秒）
 * @returns 日本語形式の日時文字列（例: "2024年12月29日 15:30:45"）
 */
export function formatUnixTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}