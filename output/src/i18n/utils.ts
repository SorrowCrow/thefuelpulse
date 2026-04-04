import { translations } from './translations';
import type { Language } from '@/types';

export function getTranslation(lang: Language, key: string): string {
  return translations[key]?.[lang] || key;
}

export function getCurrentLang(url: URL): Language {
  const pathname = url.pathname;
  if (pathname.startsWith('/en')) {
    return 'en';
  }
  return 'lv';
}

export function getLocalizedPath(path: string, lang: Language): string {
  if (lang === 'en') {
    return `/en${path}`;
  }
  return path;
}

export function getAlternateLanguage(currentLang: Language): Language {
  return currentLang === 'lv' ? 'en' : 'lv';
}

export function getAlternatePath(currentPath: string, currentLang: Language): string {
  if (currentLang === 'lv') {
    return `/en${currentPath}`;
  }
  return currentPath.replace(/^\/en/, '') || '/';
}
