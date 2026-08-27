export const SOURCES = [
  { key: 'anilist', name: 'AniList', short: 'AL', url: 'https://anilist.co/anime' },
  { key: 'shikimori', name: 'Shikimori', short: 'SHK', url: 'https://shikimori.one/animes' },
  { key: 'anime_themes', name: 'AnimeThemes', short: 'AT', url: 'https://animethemes.moe' },
  { key: 'manga', name: 'Manga', short: 'MN', url: 'https://mangadex.org' },
]

export const SOURCE_BY_KEY = Object.fromEntries(SOURCES.map((s) => [s.key, s]))

export function stripHtml(html = '') {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/\s+/g, ' ')
    .trim()
}

export function dateOf(obj) {
  if (!obj) return null
  if (obj.year == null) return null
  if (obj.month == null || obj.day == null) return String(obj.year)
  return `${String(obj.day).padStart(2, '0')}.${String(obj.month).padStart(2, '0')}.${obj.year}`
}

export function dateFrom(parts) {
  if (!parts) return null
  const { year, month, day } = parts
  if (!year) return null
  if (!month || !day) return String(year)
  return `${String(day).padStart(2, '0')}.${String(month).padStart(2, '0')}.${year}`
}

export function isoYear(iso) {
  return iso ? iso.slice(0, 4) : null
}

export function payloadOf(source) {
  const p = source
  if (!p) return null
  if (p.anime && Array.isArray(p.anime.animethemes)) return p.anime // anime_themes
  if (p.anime && Array.isArray(p.anime.genres)) return p.anime // shikimori
  return p
}

export function coverOf(source, sourceKey) {
  const p = payloadOf(source)
  if (!p) return null
  if (sourceKey === 'animan') return p.posters?.[0]?.url || null
  if (sourceKey === 'anilist') return p.coverImage?.extraLarge || p.coverImage?.large || null
  if (sourceKey === 'shikimori') return p.image?.original ? `https://shikimori.one${p.image.original}` : null
  if (sourceKey === 'manga') return p.parts?.anilist?.coverImage?.large || null
  return null
}

export function bannerOf(source, sourceKey) {
  const p = payloadOf(source)
  if (!p) return null
  if (sourceKey === 'animan') return p.banners?.[0]?.url || null
  if (sourceKey === 'anilist') return p.bannerImage || null
  return null
}
