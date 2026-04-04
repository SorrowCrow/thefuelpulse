import type { Language } from '@/types';
import en from './en.json';
import lv from './lv.json';
import ru from './ru.json';

const translations: Record<Language, Record<string, string>> = { en, lv, ru };

export function t(lang: Language, key: string): string {
  return translations[lang]?.[key] ?? translations['en']?.[key] ?? key;
}

/** Strip locale prefix from a URL pathname to get the canonical path. */
export function getCanonicalPath(pathname: string): string {
  const match = pathname.match(/^\/(en|ru)(\/|$)(.*)/);
  if (match) {
    const rest = match[3];
    return rest ? `/${rest}` : '/';
  }
  return pathname;
}

/** Build a locale-prefixed path. lv is the default locale (no prefix). */
export function localePath(canonicalPath: string, lang: Language): string {
  if (lang === 'lv') return canonicalPath;
  if (canonicalPath === '/') return `/${lang}/`;
  return `/${lang}${canonicalPath}`;
}

/** Detect language from URL pathname. */
export function getLangFromUrl(url: URL): Language {
  const [, prefix] = url.pathname.split('/');
  if (prefix === 'en') return 'en';
  if (prefix === 'ru') return 'ru';
  return 'lv';
}
