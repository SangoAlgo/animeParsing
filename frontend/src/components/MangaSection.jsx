import { Section, Facts, Chips, List, MiniTable, Imgs, Html, JsonBlock, Everything } from './Bits.jsx'
import { stripHtml, dateOf } from '../sources.js'

/* ------------------------------------------------------------------ */
/* Manga: per-source cards + episode->chapter mapping table            */
/* ------------------------------------------------------------------ */

const PART_META = {
  anilist: { name: 'AniList', url: (p) => p.siteUrl || `https://anilist.co/manga/${p.id}` },
  jikan_myanimelist: {
    name: 'MyAnimeList',
    url: (p) => (p.data?.url) || `https://myanimelist.net/manga/${p.id}`,
  },
  shikimori: { name: 'Shikimori', url: (p) => p.manga?.url || `https://shikimori.one/mangas/${p.id}` },
  kitsu: { name: 'Kitsu', url: (p) => `https://kitsu.app/manga/${p.attributes?.slug || p.id}` },
  bangumi: { name: 'Bangumi', url: (p) => `https://bgm.tv/subject/${p.id}` },
  mangadex: { name: 'MangaDex', url: (p) => `https://mangadex.org/title/${p.id}` },
  anime_planet: { name: 'Anime-Planet', url: (p) => p.url },
}

function snapshot(partKey, part) {
  switch (partKey) {
    case 'anilist':
      return {
        cover: part.coverImage?.large || null,
        caption: `гл. ${part.chapters ?? '?'} · т. ${part.volumes ?? '?'} · ${part.status ?? ''}`.trim(),
      }
    case 'jikan_myanimelist': {
      const d = part.data
      return {
        cover: d?.images?.webp?.large || d?.images?.jpg?.large || null,
        caption: d
          ? `гл. ${d.chapters ?? '?'} · т. ${d.volumes ?? '?'} · ${d.status ?? ''}`.trim()
          : null,
      }
    }
    case 'shikimori': {
      const m = part.manga
      return {
        cover: m?.image?.original ? `https://shikimori.one${m.image.original}` : null,
        caption: m ? `гл. ${m.chapters ?? '?'} · т. ${m.volumes ?? '?'} · ${m.status ?? ''}`.trim() : null,
      }
    }
    case 'kitsu': {
      const a = part.attributes
      return {
        cover: a?.posterImage?.large || a?.posterImage?.original || null,
        caption: `гл. ${a?.chapterCount ?? '?'} · т. ${a?.volumeCount ?? '?'} · ${a?.status ?? ''}`.trim(),
      }
    }
    case 'bangumi': {
      const s = part.subject
      return { cover: s?.images?.large || s?.images?.common || null, caption: null }
    }
    case 'mangadex':
      return { cover: part.cover_url || null, caption: null }
    case 'anime_planet':
      return { cover: null, caption: null }
    default:
      return { cover: null, caption: null }
  }
}

function chapterIdOf(mdPart, n) {
  const s = String(n)
  for (const v of mdPart?.volumes_en || []) {
    for (const c of v.chapters || []) {
      if (String(c.n) === s) return c.id || null
    }
  }
  return null
}

function chLink(mdPart, n) {
  const id = chapterIdOf(mdPart, n)
  return id ? `https://mangadex.org/chapter/${id}` : null
}

function compactRanges(nums) {
  const arr = nums
    .map(Number)
    .filter(Number.isFinite)
    .sort((a, b) => a - b)
  if (!arr.length) return ''
  const out = []
  let start = arr[0]
  let prev = arr[0]
  for (const n of arr.slice(1)) {
    if (n === prev + 1) {
      prev = n
      continue
    }
    out.push(start === prev ? `${start}` : `${start}–${prev}`)
    start = prev = n
  }
  out.push(start === prev ? `${start}` : `${start}–${prev}`)
  return out.join(', ')
}

export default function MangaSection({ title }) {
  const m = title.sources?.manga
  const parts = (m && typeof m === 'object' && m.parts) || {}
  const errs = (m && typeof m === 'object' && m.errors) || {}
  const map = title.manga_map || {}
  const ca = map.continue_after
  const mdPart = parts.mangadex
  const partKeys = Object.keys(parts)

  return (
    <div style={{ marginTop: 44 }}>
      <div className="section-label">МАНГА · ЭПИЗОДЫ → ГЛАВЫ</div>

      <div className="panel">
        <div className="panel__head" style={{ borderBottom: '1px solid var(--line-soft)' }}>
          <span className="panel__name">
            {title.names.en}
            <span className="chip hi" style={{ marginLeft: 10 }}>
              {map.kind_label ?? 'манги нет'}
            </span>
          </span>
          <span className="meta">
            {partKeys.length ? `источников ответили: ${partKeys.length} из 7` : 'источники не нашли мангу'}
          </span>
          {mdPart ? (
            <a
              className="btn-read"
              href={PART_META.mangadex.url(mdPart)}
              target="_blank"
              rel="noreferrer"
            >
              ЧИТАТЬ НА MANGADEX ↗
            </a>
          ) : null}
        </div>

        <div className="sec">
          <div className="sec__label">что это за манга</div>
          <div className="sec__body">
            <p style={{ maxWidth: 860 }}>{map.note ?? '—'}</p>
            <p className="muted" style={{ fontSize: 11.5 }}>
              маппинг курируемый, границы сезонов/арок приблизительные (±1–2 главы)
            </p>
          </div>
        </div>

        {map.rows?.length ? (
          <div className="sec">
            <div className="sec__label">какие главы какими эпизодами охвачены</div>
            <div className="sec__body">
              <MiniTable
                headers={['эпизоды аниме', 'главы манги', 'примечание']}
                rows={map.rows.map((r) => [r.eps, r.chapters, r.note ?? '—'])}
              />
            </div>
          </div>
        ) : null}

        {map.episodes?.length ? (
          <div className="sec">
            <div className="sec__label">детально: эпизоды → главы</div>
            <div className="sec__body">
              <MiniTable
                headers={['эпизоды аниме', 'главы манги', 'читать']}
                rows={map.episodes.map((r) => {
                  const first = Number(String(r.chapters).split(/[–—-]/)[0])
                  const url =
                    mdPart && Number.isFinite(first) ? chLink(mdPart, first) : null
                  return [
                    r.eps,
                    r.chapters,
                    url ? (
                      <a
                        key={url}
                        className="src-link"
                        href={url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        гл. {first} ↗
                      </a>
                    ) : (
                      '—'
                    ),
                  ]
                })}
              />
            </div>
          </div>
        ) : null}

        {ca ? (
          <div className="sec">
            <div className="sec__label">начать читать после аниме</div>
            <div className="sec__body">
              <div className="manga-continue">
                <b>
                  после эпизода {ca.episode} → читать с главы {ca.chapter}
                  {ca.volume ? ` · том ${ca.volume}` : ''}
                </b>
                {ca.note ? <div>{ca.note}</div> : null}
                <div style={{ marginTop: 8 }}>
                  {mdPart ? (
                    chLink(mdPart, ca.chapter) ? (
                      <a
                        className="src-link"
                        href={chLink(mdPart, ca.chapter)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        читать с главы {ca.chapter} на MangaDex ↗
                      </a>
                    ) : (
                      <a
                        className="src-link"
                        href={PART_META.mangadex.url(mdPart)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        MangaDex ↗
                      </a>
                    )
                  ) : null}
                  {parts.anilist ? (
                    <a
                      className="src-link"
                      href={PART_META.anilist.url(parts.anilist)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      AniList ↗
                    </a>
                  ) : null}
                  {parts.shikimori ? (
                    <a
                      className="src-link"
                      href={PART_META.shikimori.url(parts.shikimori)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Shikimori ↗
                    </a>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {Object.keys(errs).length ? (
          <div className="sec">
            <div className="sec__label">ошибки подзапросов</div>
            <div className="sec__body">
              {Object.entries(errs).map(([k, e]) => (
                <div key={k} style={{ color: '#e5482e', fontSize: 12.5 }}>
                  {k}: {e.message || e.type} <span style={{ color: 'var(--faint)' }}>({e.type})</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {partKeys.length ? (
          <div className="sec">
            <div className="sec__label">досье по источникам · обложки</div>
            <div className="sec__body">
              <div className="manga-covers">
                {partKeys.map((k) => {
                  const s = snapshot(k, parts[k])
                  if (!s.cover) return null
                  return (
                    <div className="manga-cover" key={k}>
                      <a href={PART_META[k].url(parts[k])} target="_blank" rel="noreferrer">
                        <img src={s.cover} alt="" loading="lazy" referrerPolicy="no-referrer" />
                      </a>
                      <b>{PART_META[k].name}</b>
                      {s.caption ? <span>{s.caption}</span> : null}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        ) : null}

        <div className="sec">
          <div className="sec__label">ссылки</div>
          <div className="sec__body">
            {partKeys.map((k) => (
              <a key={k} className="src-link" href={PART_META[k].url(parts[k])} target="_blank" rel="noreferrer">
                {PART_META[k].name} ↗
              </a>
            ))}
          </div>
        </div>
      </div>

      {partKeys.map((k) => (
        <MangaSourcePanel key={k} partKey={k} part={parts[k]} />
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* One card per manga source                                          */
/* ------------------------------------------------------------------ */

function MangaSourcePanel({ partKey, part }) {
  const meta = PART_META[partKey]
  return (
    <div className="panel" style={{ marginTop: 16 }}>
      <div className="panel__head">
        <span className="panel__name">
          {meta.name} <span className="sub">манга</span>
        </span>
        <span className="meta">
          id: <b style={{ color: '#ede5d3', fontWeight: 500 }}>{part.id ?? part.slug ?? '—'}</b>
          <a className="src-link" style={{ marginLeft: 10 }} href={meta.url(part)} target="_blank" rel="noreferrer">
            страница ↗
          </a>
        </span>
      </div>
      {mangaSections(partKey, part)}
    </div>
  )
}

function mangaSections(partKey, part) {
  switch (partKey) {
    case 'anilist':
      return <MangaAniList part={part} />
    case 'jikan_myanimelist':
      return <MangaJikan part={part} />
    case 'shikimori':
      return <MangaShikimori part={part} />
    case 'kitsu':
      return <MangaKitsu part={part} />
    case 'bangumi':
      return <MangaBangumi part={part} />
    case 'mangadex':
      return <MangaDex part={part} />
    case 'anime_planet':
      return <MangaPlanet part={part} />
    default:
      return <Everything data={part} />
  }
}

function MangaAniList({ part }) {
  const m = part
  return (
    <>
      <Section label="названия и факты">
        <Facts
          items={[
            ['романдзи', m.title?.romaji],
            ['английское', m.title?.english],
            ['оригинал', m.title?.native],
            ['синонимы', m.synonyms],
            ['id AniList / MAL', m.id != null ? `${m.id} / ${m.idMal}` : null],
            ['формат', m.format],
            ['статус', m.status],
            ['главы / тома', m.chapters != null ? `${m.chapters} / ${m.volumes ?? '?'}` : null],
            ['страна', m.countryOfOrigin],
            ['начало', dateOf(m.startDate)],
            ['конец', dateOf(m.endDate)],
            ['взрослый', m.isAdult],
            ['лицензирован', m.isLicensed],
            ['ссылка', m.siteUrl],
          ]}
        />
      </Section>

      <Section label="рейтинги">
        <Facts
          items={[
            ['averageScore', m.averageScore != null ? `${m.averageScore} / 100` : null],
            ['meanScore', m.meanScore != null ? `${m.meanScore} / 100` : null],
            ['popularity', m.popularity],
            ['favourites', m.favourites],
            ['trending', m.trending],
            ['ранги', (m.rankings || []).map((r) => `#${r.rank} ${r.type}${r.context ? ` (${r.context})` : ''}`)],
          ]}
        />
      </Section>

      <Section label="жанры">
        <Chips items={m.genres} hi />
      </Section>

      <Section label="теги">
        <MiniTable
          headers={['тег', 'ранг', 'категория', 'спойлер']}
          rows={(m.tags || []).map((t) => [
            `${t.name}${t.isMediaSpoiler || t.isGeneralSpoiler ? ' ⚠' : ''}`,
            t.rank,
            t.category ?? '—',
            t.isGeneralSpoiler ? 'общий' : t.isMediaSpoiler ? 'по тайтлу' : '—',
          ])}
        />
      </Section>

      <Section label="авторы и персонал">
        <MiniTable
          headers={['роль', 'имя', 'язык']}
          rows={(m.staff?.edges || []).map((e) => [
            e.role,
            `${e.node?.name?.full}${e.node?.name?.native ? ` (${e.node?.name?.native})` : ''}`,
            e.node?.language ?? '—',
          ])}
        />
      </Section>

      <Section label="персонажи">
        <MiniTable
          headers={['роль', 'персонаж']}
          rows={(m.characters?.edges || []).map((e) => [
            e.role,
            `${e.node?.name?.full}${e.node?.name?.native ? ` (${e.node?.name?.native})` : ''}`,
          ])}
        />
      </Section>

      <Section label="связи и рекомендации">
        <MiniTable
          headers={['связь', 'работа', 'формат']}
          rows={(m.relations?.edges || []).map((e) => [
            e.relationType,
            e.node?.title?.romaji || e.node?.title?.english || '—',
            e.node?.format ?? '—',
          ])}
        />
        <MiniTable
          headers={['рейтинг', 'рекомендуют']}
          rows={(m.recommendations?.nodes || []).map((n) => [
            n.rating,
            n.mediaRecommendation?.title?.romaji || n.mediaRecommendation?.title?.english || '—',
          ])}
        />
      </Section>

      <Section label="внешние ссылки">
        <List
          items={(m.externalLinks || []).map(
            (l) => `${l.site} (${l.type ?? 'link'}${l.language ? `, ${l.language}` : ''}) — ${l.url}`,
          )}
        />
      </Section>

      <Section label="обложки">
        <Imgs
          urls={[m.coverImage?.extraLarge, m.coverImage?.large, m.bannerImage].filter(Boolean)}
        />
      </Section>

      <Section label="описание">
        <p>{stripHtml(m.description)}</p>
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={m}
          skip={[
            'id', 'idMal', 'title', 'synonyms', 'siteUrl', 'format', 'status', 'chapters',
            'volumes', 'countryOfOrigin', 'isAdult', 'isLicensed', 'startDate', 'endDate',
            'averageScore', 'meanScore', 'popularity', 'favourites', 'trending', 'rankings',
            'genres', 'tags', 'staff', 'characters', 'relations', 'recommendations',
            'externalLinks', 'coverImage', 'bannerImage', 'description',
          ]}
        />
      </Section>

      <JsonBlock data={m} />
    </>
  )
}

function MangaJikan({ part }) {
  const d = part.data
  const ok = (x) => (x && !x.error ? x : null)
  const good = (a) => (Array.isArray(a) ? a.filter(Boolean) : [])
  const chars = ok(part.characters)
  const stats = ok(part.statistics)
  const pics = ok(part.pictures)
  const reco = ok(part.recommendations)
  const ext = ok(part.external)

  return (
    <>
      {!d ? (
        <div className="sec__body" style={{ color: 'var(--faint)' }}>
          MAL не отдал досье при сборе (лимит/504). См. ошибки выше.
        </div>
      ) : null}

      {d ? (
        <>
          <Section label="названия">
            <Facts
              items={[
                ['основное', d.title],
                ['английское', d.title_english],
                ['японское', d.title_japanese],
                ['синонимы', d.title_synonyms],
                ['url MAL', d.url],
              ]}
            />
          </Section>

          <Section label="факты">
            <Facts
              items={[
                ['mal_id', d.mal_id],
                ['тип / статус', `${d.type ?? '—'} · ${d.status ?? '—'}`],
                ['главы / тома', d.chapters != null ? `${d.chapters} / ${d.volumes ?? '?'}` : null],
                ['выход', d.published?.string],
                ['score', d.score != null ? `${d.score} / 10` : null],
                ['оценок', d.scored_by],
                ['ранг', d.rank],
                ['популярность', d.popularity],
                ['members / favorites', d.members != null ? `${d.members} / ${d.favorites}` : null],
              ]}
            />
          </Section>

          <Section label="авторы">
            <MiniTable
              headers={['имя', 'роль']}
              rows={good(d.authors).map((a) => [a.name, a.role ?? '—'])}
            />
          </Section>

          <Section label="жанры / темы / демографика">
            <Facts
              items={[
                ['жанры', (d.genres || []).map((g) => g.name)],
                ['темы', (d.themes || []).map((g) => g.name)],
                ['демографика', (d.demographics || []).map((g) => g.name)],
                ['сериализация', (d.serializations || []).map((s) => s.name)],
              ]}
            />
          </Section>

          <Section label="распределение оценок (1–10)">
            {stats?.data?.scores ? (
              <div>
                {[...stats.data.scores].reverse().map((s) => (
                  <div className="rating-bar-row" key={s.score}>
                    <span style={{ minWidth: 28 }}>{s.score}</span>
                    <span className="bar">
                      <i style={{ width: `${Math.min(100, (s.votes / Math.max(1, stats.data.scores[9].votes)) * 100)}%` }} />
                    </span>
                    <span>{s.votes}</span>
                  </div>
                ))}
              </div>
            ) : (
              '—'
            )}
          </Section>

          <Section label="синопсис">
            <p>{d.synopsis}</p>
          </Section>

          <Section label="background">
            <p>{d.background}</p>
          </Section>

          <Section label="персонажи">
            <MiniTable
              headers={['роль', 'персонаж']}
              rows={good(chars?.data).map((c) => [c.role, c.character?.name])}
            />
          </Section>

          <Section label="рекомендации">
            <MiniTable
              headers={['рекомендуют', 'глав']}
              rows={good(reco?.data).map((r) => [
                (Array.isArray(r.entry) ? r.entry : [r.entry]).filter(Boolean).map((e) => e.name).join('; ') || (r.title ?? '—'),
                r.chapters ?? '—',
              ])}
            />
          </Section>

          <Section label="внешние id">
            <MiniTable
              headers={['база', 'id', 'url']}
              rows={good(ext?.data).map((e) => [e.name, e.mal_id ?? '—', e.url])}
            />
          </Section>

          <Section label="обложки и изображения">
            <Imgs
              urls={[
                d.images?.webp?.large,
                d.images?.jpg?.large,
                ...good(pics?.data).map((p) => p.webp?.large || p.jpg?.large),
              ].filter(Boolean)}
            />
          </Section>

          <Section label="все прочие поля (авто)">
            <Everything
              data={d}
              skip={[
                'mal_id', 'url', 'images', 'titles', 'title', 'title_english', 'title_japanese',
                'title_synonyms', 'type', 'status', 'chapters', 'volumes', 'published', 'score',
                'scored_by', 'rank', 'popularity', 'members', 'favorites', 'synopsis', 'background',
                'authors', 'genres', 'themes', 'demographics', 'serializations',
              ]}
            />
            <Everything data={part} skip={['id', 'data', 'characters', 'statistics', 'pictures', 'recommendations', 'external']} />
          </Section>

          <JsonBlock data={part} />
        </>
      ) : null}
    </>
  )
}

function MangaShikimori({ part }) {
  const m = part.manga
  const img = (p) =>
    p && !p.includes('/assets/globals/missing_') ? `https://shikimori.one${p}` : null
  const roles = Array.isArray(part.roles) ? part.roles : []
  const chars = roles
    .filter((r) => r.character)
    .map((r) => [r.character?.russian || r.character?.name, (r.roles_russian || []).join(', ')])
  const staff = roles.filter((r) => r.person)
  const similar = Array.isArray(part.similar) ? part.similar : []
  const related = Array.isArray(part.related) ? part.related : []
  const extLinks = Array.isArray(part.external_links) ? part.external_links : []

  return (
    <>
      <Section label="названия">
        <Facts
          items={[
            ['основное', m.name],
            ['русское', m.russian],
            ['английское', m.english],
            ['японское', m.japanese],
            ['синонимы', m.synonyms],
            ['url', m.url],
          ]}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['id', m.id],
            ['id MAL', m.myanimelist_id],
            ['тип', m.kind],
            ['статус', m.status],
            ['главы / тома', m.chapters != null ? `${m.chapters} / ${m.volumes}` : null],
            ['премьера', m.aired_on],
            ['финал', m.released_on],
            ['score', m.score != null ? `${m.score} / 10` : null],
            ['издатели', (m.publishers || []).map((p) => p.name)],
            ['лицензии (RU)', m.license_name_ru],
            ['франшиза', m.franchise],
            ['онгоинг', m.ongoing || null],
            ['анонс', m.anons || null],
            ['обновлено', m.updated_at?.slice(0, 16)],
          ]}
        />
      </Section>

      <Section label="распределение оценок">
        <MiniTable
          headers={['оценка', 'кол-во']}
          rows={(m.rates_scores_stats || []).map((s) => [s.name, s.value])}
        />
      </Section>

      <Section label="жанры">
        <Chips
          items={m.genres?.map((g) => (g.russian ? `${g.name} / ${g.russian}` : g.name))}
          hi
        />
      </Section>

      <Section label="описание">
        {m.description_html ? <Html html={m.description_html} /> : <p>{m.description}</p>}
      </Section>

      {chars.length ? (
        <Section label="роли (персонажи)">
          <MiniTable headers={['персонаж', 'роль']} rows={chars} />
        </Section>
      ) : null}

      {staff.length ? (
        <Section label={`персонал · ${staff.length}`}>
          <MiniTable
            headers={['фото', 'имя', 'роль']}
            rows={staff.map((r) => [
              img(r.person?.image?.preview || r.person?.image?.original) ? (
                <img
                  key={r.person.id}
                  src={img(r.person.image.preview || r.person.image.original)}
                  alt=""
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  style={{ width: 40, border: '1px solid var(--line-soft)' }}
                />
              ) : (
                '—'
              ),
              <b key={r.person.id}>{r.person?.russian || r.person?.name}</b>,
              (r.roles_russian || r.roles || []).join(', '),
            ])}
          />
        </Section>
      ) : null}

      <Section label="похожие">
        <List
          items={similar.map((s) => `${s.name}${s.russian ? ` / ${s.russian}` : ''} (score ${s.score})`)}
        />
      </Section>

      <Section label="связанные">
        <MiniTable
          headers={['связь', 'работа']}
          rows={related.map((r) => [
            r.relation,
            r.anime?.russian || r.anime?.name || r.manga?.russian || r.manga?.name || '—',
          ])}
        />
      </Section>

      <Section label="внешние ссылки">
        <MiniTable
          headers={['тип', 'url']}
          rows={extLinks.map((l) => [
            l.kind ?? l.label ?? '—',
            l.url ? <a key={l.url} href={l.url} target="_blank" rel="noreferrer">{l.url}</a> : '—',
          ])}
        />
      </Section>

      <Section label="обложки">
        <Imgs urls={[img(m.image?.original), img(m.image?.preview)].filter(Boolean)} />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything data={part} skip={['id', 'manga', 'roles', 'similar', 'related', 'external_links']} />
        <Everything
          data={m}
          skip={[
            'id', 'name', 'russian', 'english', 'japanese', 'synonyms', 'url', 'image', 'kind',
            'status', 'chapters', 'volumes', 'aired_on', 'released_on', 'score', 'publishers',
            'license_name_ru', 'franchise', 'ongoing', 'anons', 'updated_at', 'rates_scores_stats',
            'rates_statuses_stats', 'description', 'description_html', 'description_source',
            'genres', 'myanimelist_id', 'favoured', 'thread_id', 'topic_id', 'user_rate',
          ]}
        />
      </Section>

      <JsonBlock data={part} />
    </>
  )
}

function MangaKitsu({ part }) {
  const a = part.attributes
  return (
    <>
      <Section label="названия">
        <Facts
          items={[
            ['каноническое', a.canonicalTitle],
            ['en_jp', a.titles?.en_jp],
            ['en_us', a.titles?.en_us],
            ['ja_jp', a.titles?.ja_jp],
            ['сокращения', a.abbreviatedTitles],
            ['slug', a.slug],
          ]}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['id', part.id],
            ['подтип', a.subtype],
            ['тип манги', a.mangaType],
            ['статус', a.status],
            ['главы / тома', a.chapterCount != null ? `${a.chapterCount} / ${a.volumeCount ?? '?'}` : null],
            ['начало', a.startDate],
            ['конец', a.endDate],
            ['tba', a.tba],
            ['возрастной рейтинг', a.ageRating],
            ['сериализация', a.serialization],
            ['создано', a.createdAt?.slice(0, 10)],
            ['обновлено', a.updatedAt?.slice(0, 10)],
          ]}
        />
      </Section>

      <Section label="активность">
        <Facts
          items={[
            ['averageRating', a.averageRating != null ? `${a.averageRating} / 100` : null],
            ['пользователей', a.userCount],
            ['в избранном', a.favoritesCount],
            ['место по популярности', a.popularityRank],
            ['место по рейтингу', a.ratingRank],
            ['следующий выпуск', a.nextRelease?.slice(0, 10)],
          ]}
        />
      </Section>

      <Section label="жанры">
        <Chips items={part.genres?.map((g) => g.title).filter(Boolean)} hi />
      </Section>

      <Section label="синопсис">
        <p>{a.synopsis}</p>
      </Section>

      <Section label="персонажи">
        <List items={(part.characters || []).map((c) => c.attributes?.name)} />
      </Section>

      <Section label="обложки">
        <Imgs urls={[a.posterImage?.original, a.posterImage?.large, a.coverImage?.original].filter(Boolean)} />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={part}
          skip={['id', 'attributes', 'characters', 'genres', 'categories', 'mediaRelationships', 'relationship_ids']}
        />
        <Everything
          data={a}
          skip={[
            'createdAt', 'updatedAt', 'slug', 'synopsis', 'description', 'titles', 'canonicalTitle',
            'abbreviatedTitles', 'averageRating', 'ratingFrequencies', 'userCount', 'favoritesCount',
            'startDate', 'endDate', 'nextRelease', 'popularityRank', 'ratingRank', 'ageRating',
            'ageRatingGuide', 'subtype', 'mangaType', 'status', 'tba', 'posterImage', 'coverImage',
            'chapterCount', 'volumeCount', 'serialization',
          ]}
        />
      </Section>

      <JsonBlock data={part} />
    </>
  )
}

function MangaBangumi({ part }) {
  const s = part.subject
  return (
    <>
      <Section label="названия">
        <Facts
          items={[
            ['оригинальное', s.name],
            ['китайское', s.name_cn],
            ['id bgm', s.id],
          ]}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['дата', s.date],
            ['платформа', s.platform],
            ['тип', s.type],
            ['эпизодов (инфобокс) / всего', s.eps != null ? `${s.eps} / ${s.total_episodes}` : null],
            ['томов', s.volumes ?? null],
            ['series', s.series || null],
            ['rank', s.rating?.rank],
            ['score', s.rating?.score != null ? `${s.rating.score} / 10` : null],
            ['оценок', s.rating?.total],
            [
              'коллекции',
              s.collection
                ? `wish ${s.collection.wish}, doing ${s.collection.doing}, collect ${s.collection.collect}, on_hold ${s.collection.on_hold}, dropped ${s.collection.dropped}`
                : null,
            ],
          ]}
        />
      </Section>

      <Section label="распределение оценок (1–10)">
        {s.rating?.count ? (
          <div>
            {Object.entries(s.rating.count)
              .sort(([a], [b]) => b - a)
              .map(([k, v]) => (
                <div className="rating-bar-row" key={k}>
                  <span style={{ minWidth: 28 }}>{k}</span>
                  <span className="bar">
                    <i style={{ width: `${Math.min(100, (v / Math.max(1, s.rating.total)) * 100)}%` }} />
                  </span>
                  <span>{v}</span>
                </div>
              ))}
          </div>
        ) : (
          '—'
        )}
      </Section>

      <Section label="мета-теги">
        <Chips items={s.meta_tags} hi />
      </Section>

      <Section label="теги (с весом)">
        <div className="chips">
          {(s.tags || []).map((t) => (
            <span className="chip hi" key={t.name}>
              {t.name} · {t.count}
            </span>
          ))}
        </div>
      </Section>

      <Section label="инфобокс">
        <Facts
          items={(s.infobox || [])
            .map((r) => [
              String(r.key),
              Array.isArray(r.value)
                ? r.value.map((x) => (typeof x === 'string' ? x : x.v)).join('; ')
                : String(r.value),
            ])
            .filter(([, v]) => v)}
        />
      </Section>

      <Section label="описание">
        <p>{s.summary}</p>
      </Section>

      <Section label="люди / создатели">
        <MiniTable
          headers={['имя', 'роль']}
          rows={(part.persons || []).map((p) => [p.name, p.role ?? '—'])}
        />
      </Section>

      <Section label="персонажи">
        <MiniTable
          headers={['персонаж', 'роль']}
          rows={(part.characters || []).map((c) => [c.name, c.role ?? '—'])}
        />
      </Section>

      <Section label="обложки">
        <Imgs urls={[s.images?.large, s.images?.medium, s.images?.small, s.images?.common].filter(Boolean)} />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything data={part} skip={['id', 'subject', 'persons', 'characters']} />
        <Everything
          data={s}
          skip={[
            'date', 'platform', 'images', 'summary', 'name', 'name_cn', 'tags', 'infobox',
            'rating', 'total_episodes', 'collection', 'id', 'eps', 'meta_tags', 'volumes',
            'series', 'locked', 'nsfw', 'type',
          ]}
        />
      </Section>

      <JsonBlock data={part} />
    </>
  )
}

function MangaDex({ part }) {
  const a = part.attributes
  const vols = part.volumes_en || []
  const alt = (a.altTitles || []).flatMap((t) => Object.values(t)).slice(0, 8)
  return (
    <>
      <Section label="названия">
        <Facts
          items={[
            ['английское', a.title?.en],
            ['альт. названия', alt],
            ['ссылка', `https://mangadex.org/title/${part.id}`],
          ]}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['статус', a.status],
            ['state', a.state],
            ['год', a.year],
            ['демографика', a.publicationDemographic],
            ['оригинальный язык', a.originalLanguage],
            ['контент-рейтинг', a.contentRating],
            ['последняя глава', a.lastChapter],
            ['последний том', a.lastVolume],
            ['глав в EN переводе', part.chapters_en_total],
            ['глав в оригинале (по статусу)', a.lastChapter ?? null],
            ['links (внешние базы)', a.links ? JSON.stringify(a.links) : null],
            ['official links', a.officialLinks],
            ['обновлено', a.updatedAt?.slice(0, 10)],
          ]}
        />
      </Section>

      <Section label="теги">
        <Chips items={(a.tags || []).map((t) => t.attributes?.name?.en).filter(Boolean)} hi />
      </Section>

      <Section label="авторы / художники">
        <Facts
          items={[
            ['авторы', part.authors],
            ['художники', part.artists],
          ]}
        />
      </Section>

      <Section label={`главы по томам (EN) · всего ${part.chapters_en_total}`}>
        <MiniTable
          headers={['том', 'глав', 'главы']}
          rows={vols.map((v) => [v.volume ?? '—', v.count, compactRanges(v.chapters) || '—'])}
        />
      </Section>

      <Section label="обложка">
        {part.cover_url ? (
          <Imgs urls={[part.cover_url]} />
        ) : (
          '—'
        )}
      </Section>

      <Section label="описание (EN)">
        <p>{stripHtml(a.description?.en)}</p>
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={part}
          skip={['id', 'attributes', 'cover_url', 'authors', 'artists', 'volumes_en', 'chapters_en_total']}
        />
        <Everything
          data={a}
          skip={[
            'title', 'altTitles', 'description', 'links', 'officialLinks', 'status', 'state',
            'publicationDemographic', 'contentRating', 'tags', 'originalLanguage', 'year',
            'lastChapter', 'lastVolume', 'latestUploadedChapter', 'chapterNumbersResetOnNewVolume',
            'availableTranslatedLanguages', 'createdAt', 'updatedAt',
          ]}
        />
      </Section>

      <JsonBlock data={part} />
    </>
  )
}

function MangaPlanet({ part }) {
  const p = part
  return (
    <>
      <Section label="названия">
        <Facts
          items={[
            ['основное', p.title],
            ['альт. названия', p.alt_titles],
            ['url', p.url],
          ]}
        />
      </Section>

      <Section label="данные страницы">
        <Facts
          items={[
            ['entry bar', p.entry_bar],
            ['рейтинг', p.rating_text],
            ['пользователи', p.user_stats],
          ]}
        />
      </Section>

      <Section label="теги">
        <Chips items={p.tags} hi />
      </Section>

      <Section label="персонал">
        <List items={(p.staff || []).map((s) => s.name)} />
      </Section>

      <Section label="персонажи">
        <MiniTable
          headers={['персонаж', 'мета']}
          rows={(p.characters || []).map((c) => [c.name, c.meta ?? '—'])}
        />
      </Section>

      <Section label="связанное">
        <MiniTable
          headers={['связь', 'тайтл', 'мета']}
          rows={[
            ...(p.related?.anime || []).map((r) => ['аниме', r.title, r.meta ?? '—']),
            ...(p.related?.manga || []).map((r) => ['манга', r.title, r.meta ?? '—']),
          ]}
        />
      </Section>

      <Section label="синопсис">
        <p>{p.synopsis}</p>
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={p}
          skip={[
            'slug', 'url', 'title', 'alt_titles', 'synopsis', 'entry_bar', 'rating_text',
            'user_stats', 'tags', 'staff', 'characters', 'related',
          ]}
        />
      </Section>

      <JsonBlock data={p} />
    </>
  )
}