export function formatDateTime(isoString: string, lang: 'lv' | 'en'): string {
  const date = new Date(isoString);
  const locale = lang === 'lv' ? 'lv-LV' : 'en-US';
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false, // Use 24-hour format
  };
  return new Intl.DateTimeFormat(locale, options).format(date);
}

export function formatShortDate(isoString: string, lang: 'lv' | 'en'): string {
  const date = new Date(isoString);
  const locale = lang === 'lv' ? 'lv-LV' : 'en-US';
  const options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
  };
  return new Intl.DateTimeFormat(locale, options).format(date);
}
