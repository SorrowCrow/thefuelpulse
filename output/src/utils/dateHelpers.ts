const LOCALES: Record<string, string> = { lv: 'lv-LV', en: 'en-US', ru: 'ru-RU' };
const toLocale = (lang: string) => LOCALES[lang] ?? 'en-US';

export function formatDateTime(isoString: string, lang: string): string {
  const date = new Date(isoString);
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    timeZone: 'Europe/Riga',
  };
  return new Intl.DateTimeFormat(toLocale(lang), options).format(date);
}

export function formatShortDate(isoString: string, lang: string): string {
  const date = new Date(isoString);
  const options: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
  };
  return new Intl.DateTimeFormat(toLocale(lang), options).format(date);
}
