import { SOURCES, stripHtml, dateOf } from '../sources.js'

import { Section, Facts, Chips, List, MiniTable, Imgs, Html, JsonBlock, Everything } from './Bits.jsx'
function Meta({ sourceKey, raw }) {
  const s = SOURCES.find((x) => x.key === sourceKey)
  return (
    <div className="panel__head">
      <span className="panel__name">{s.name}</span>
      <span className="meta">
        id: <b style={{ color: '#ede5d3', fontWeight: 500 }}>{raw.id ?? raw.slug ?? '—'}</b>
        {raw.fetched_at_utc ? ` · получено ${raw.fetched_at_utc.replace('T', ' ').slice(0, 16)} UTC` : ''}
        {raw.duration_s != null ? ` · ${raw.duration_s}s` : ''}
      </span>
    </div>
  )
}

function errNote(raw) {
  if (!raw.error) return null
  return (
    <div style={{ color: '#e5482e' }}>
      источник вернул ошибку: {String(raw.error).slice(0, 300)}
    </div>
  )
}

/* ------------------------------ AniList ------------------------------ */

export function AniListPanel({ raw }) {
  const m = raw
  return (
    <>
      <Meta sourceKey="anilist" raw={raw} />
      {errNote(raw)}

      <Section label="названия">
        <Facts
          items={[
            ['романдзи', m.title?.romaji],
            ['английское', m.title?.english],
            ['оригинал', m.title?.native],
            ['синонимы', m.synonyms],
            ['хэштег', m.hashtag],
            ['ссылка', m.siteUrl],
          ]}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['id AniList', m.id],
            ['id MAL', m.idMal],
            ['формат', m.format],
            ['тип', m.type],
            ['статус', m.status],
            ['эпизоды', m.episodes],
            ['длительность', m.duration != null ? `${m.duration} мин` : null],
            ['сезон', m.season && m.seasonYear ? `${m.season} ${m.seasonYear}` : m.seasonYear],
            ['страна', m.countryOfOrigin],
            ['взрослый', m.isAdult],
            ['лицензирован', m.isLicensed],
            ['источник', m.source],
            ['начало', dateOf(m.startDate)],
            ['конец', dateOf(m.endDate)],
            ['обновлено', m.updatedAt ? new Date(m.updatedAt * 1000).toISOString().slice(0, 10) : null],
          ]}
        />
      </Section>

      <Section label="рейтинги и активность">
        <Facts
          items={[
            ['averageScore', m.averageScore != null ? `${m.averageScore} / 100` : null],
            ['meanScore', m.meanScore != null ? `${m.meanScore} / 100` : null],
            ['popularity', m.popularity],
            ['favourites', m.favourites],
            ['trending', m.trending],
            ['nextAiringEpisode', m.nextAiringEpisode ? JSON.stringify(m.nextAiringEpisode) : null],
          ]}
        />
      </Section>

      <Section label="места в рейтингах">
        <MiniTable
          headers={['ранг', 'тип', 'год', 'сезон', 'все время', 'контекст']}
          rows={(m.rankings || []).map((r) => [
            `#${r.rank}`,
            r.type,
            r.year ?? '—',
            r.season ?? '—',
            r.allTime ? 'да' : '—',
            r.context ?? '—',
          ])}
        />
      </Section>

      <Section label="жанры">
        <Chips items={m.genres} hi />
      </Section>

      <Section label="теги (со спойлерами)">
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

      <Section label="студии">
        <Facts
          items={[
            [
              'студии',
              (m.studios?.edges || [])
                .map((e) => `${e.node?.name}${e.isMain ? ' (осн.)' : ''}`)
                .join(', '),
            ],
          ]}
        />
      </Section>

      <Section label="персонал">
        <MiniTable
          headers={['роль', 'имя', 'язык', 'занятость']}
          rows={(m.staff?.edges || []).map((e) => [
            e.role,
            `${e.node?.name?.full}${e.node?.name?.native ? ` (${e.node?.name?.native})` : ''}`,
            e.node?.language ?? '—',
            (e.node?.primaryOccupations || []).join(', ') || '—',
          ])}
        />
      </Section>

      <Section label="персонажи (с сэйю)">
        <MiniTable
          headers={['роль', 'персонаж', 'сэйю (яп.)']}
          rows={(m.characters?.edges || []).map((e) => [
            e.role,
            `${e.node?.name?.full}${e.node?.name?.native ? ` (${e.node?.name?.native})` : ''}`,
            (e.voiceActors || []).map((v) => v.name?.full).join(', ') || '—',
          ])}
        />
      </Section>

      <Section label="связанные работы">
        <MiniTable
          headers={['связь', 'работа', 'формат']}
          rows={(m.relations?.edges || []).map((e) => [
            e.relationType,
            e.node?.title?.romaji || e.node?.title?.english,
            e.node?.format ?? '—',
          ])}
        />
      </Section>

      <Section label="рекомендации">
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

      <Section label="стриминг-эпизоды">
        <MiniTable
          headers={['кадр', 'платформа', 'название', 'url']}
          rows={(m.streamingEpisodes || []).map((e) => [
            e.thumbnail ? (
              <img
                key={e.thumbnail}
                src={e.thumbnail}
                alt=""
                loading="lazy"
                referrerPolicy="no-referrer"
                style={{ width: 84, border: '1px solid var(--line-soft)' }}
              />
            ) : (
              '—'
            ),
            e.site,
            e.title,
            e.url ? (
              <a key={`${e.site}-${e.title}`} href={e.url} target="_blank" rel="noreferrer">
                смотреть
              </a>
            ) : (
              '—'
            ),
          ])}
        />
      </Section>

      <Section label="трейлер">
        {m.trailer?.id ? (
          <div>
            {m.trailer.thumbnail ? (
              <img
                src={m.trailer.thumbnail}
                alt=""
                loading="lazy"
                referrerPolicy="no-referrer"
                style={{ width: 240, border: '1px solid var(--line-soft)', marginBottom: 8 }}
              />
            ) : null}
            <br />
            <a
              href={`https://www.youtube.com/watch?v=${m.trailer.id}`}
              target="_blank"
              rel="noreferrer"
            >
              {m.trailer.site}: {m.trailer.id}
            </a>
          </div>
        ) : (
          '—'
        )}
      </Section>

      <Section label="обложки">
        {m.coverImage?.color ? (
          <p style={{ fontSize: 12, marginBottom: 8 }}>
            доминирующий цвет:{' '}
            <span
              style={{
                display: 'inline-block',
                width: 14,
                height: 14,
                background: m.coverImage.color,
                border: '1px solid var(--line)',
                verticalAlign: 'middle',
                margin: '0 6px',
              }}
            />{' '}
            <span className="e-plain">{m.coverImage.color}</span>
          </p>
        ) : null}
        <Imgs
          urls={[
            m.coverImage?.extraLarge,
            m.coverImage?.large,
            m.bannerImage,
          ].filter(Boolean)}
        />
      </Section>

      <Section label="описание">
        <p>{stripHtml(m.description)}</p>
      </Section>

      <Section label="рецензии сообщества">
        <MiniTable
          headers={['пользователь', 'рейтинг', 'резюме']}
          rows={(m.reviews?.nodes || []).map((r) => [
            r.user?.name ?? '—',
            r.rating,
            (r.summary || '').slice(0, 140),
          ])}
        />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={m}
          skip={[
            'id',
            'idMal',
            'title',
            'synonyms',
            'hashtag',
            'siteUrl',
            'format',
            'type',
            'status',
            'episodes',
            'duration',
            'season',
            'seasonYear',
            'countryOfOrigin',
            'isAdult',
            'isLicensed',
            'startDate',
            'endDate',
            'updatedAt',
            'averageScore',
            'meanScore',
            'popularity',
            'favourites',
            'trending',
            'nextAiringEpisode',
            'rankings',
            'genres',
            'tags',
            'studios',
            'staff',
            'characters',
            'relations',
            'recommendations',
            'externalLinks',
            'streamingEpisodes',
            'trailer',
            'coverImage',
            'bannerImage',
            'description',
            'reviews',
          ]}
        />
      </Section>

      <JsonBlock data={m} />
    </>
  )
}

/* --------------------------- Jikan / MAL ---------------------------- */

export function JikanPanel({ raw }) {
  const d = raw?.data
  const ok = (x) => (x && !x.error ? x : null)
  const good = (a) => (Array.isArray(a) ? a.filter(Boolean) : [])
  const chars = ok(raw.characters)
  const staff = ok(raw.staff)
  const reco = ok(raw.recommendations)
  const stats = ok(raw.statistics)
  const themes = ok(raw.themes)
  const pics = ok(raw.pictures)
  const eps = ok(raw.episodes)
  const ext = ok(raw.external)
  const entryNames = (e) =>
    good(Array.isArray(e) ? e : [e])
      .map((x) => x.name)
      .join('; ')
  const subErrors = Object.entries(raw).filter(
    ([k, v]) =>
      v &&
      typeof v === 'object' &&
      (v.status || (v.data == null && v.error != null)) &&
      k !== 'data',
  )

  return (
    <>
      <Meta sourceKey="jikan_myanimelist" raw={raw} />
      {errNote(raw)}

      {!d ? (
        <div className="sec__body" style={{ color: '#6f6757' }}>
          MAL не отдал основное досье (таймаут / лимит запросов). См. ошибки подзапросов ниже и
          сырые данные.
        </div>
      ) : null}

      {subErrors.length ? (
        <Section label="ошибки подзапросов MAL">
          <List
            items={subErrors.map(
              ([k, v]) =>
                `${k}: ${v.status ? `HTTP ${v.status}` : ''} ${v.message ?? v.error ?? ''}`.trim(),
            )}
          />
        </Section>
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

      <Section label="все варианты названий (titles)">
        <MiniTable
          headers={['тип', 'название']}
          rows={good(d.titles).map((t) => [t.type, t.title])}
        />
      </Section>

      <Section label="постер">
        <Imgs
          urls={[d.images?.jpg?.large, d.images?.webp?.large, d.images?.jpg?.image_url].filter(
            Boolean,
          )}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['mal_id', d.mal_id],
            ['тип', d.type],
            ['источник', d.source],
            ['эпизоды', d.episodes],
            ['статус', d.status],
            ['выходит сейчас', d.airing],
            ['длительность', d.duration],
            ['рейтинг (MPA)', d.rating],
            ['сезон', d.season && d.year ? `${d.season} ${d.year}` : d.year],
            ['трансляция', d.broadcast?.string],
            ['airing-период', d.aired ? `${d.aired.from?.slice(0, 10) ?? '—'} → ${d.aired.to?.slice(0, 10) ?? '…'}` : null],
            ['synopsis url', d.synopsis_url],
          ]}
        />
      </Section>

      <Section label="рейтинг и статистика">
        <Facts
          items={[
            ['score', d.score != null ? `${d.score} / 10` : null],
            ['оценок', d.scored_by],
            ['ранг', d.rank],
            ['популярность', d.popularity],
            ['в списках (members)', d.members],
            ['в избранном', d.favorites],
          ]}
        />
      </Section>

      <Section label="команда">
        <Facts
          items={[
            ['студии', (d.studios || []).map((s) => s.name).join(', ')],
            ['продюсеры', (d.producers || []).map((s) => s.name).join(', ')],
            ['лицензиары', (d.licensors || []).map((s) => s.name).join(', ')],
          ]}
        />
      </Section>

      <Section label="жанры">
        <Chips items={(d.genres || []).map((g) => g.name)} hi />
      </Section>

      <Section label="эксплицитные жанры / темы / демографика">
        <Facts
          items={[
            ['explicit_genres', (d.explicit_genres || []).map((g) => g.name).join(', ')],
            ['темы', (d.themes || []).map((g) => g.name).join(', ')],
            ['демографика', (d.demographics || []).map((g) => g.name).join(', ')],
          ]}
        />
      </Section>

      <Section label="синопсис">
        <p>{d.synopsis}</p>
      </Section>

      <Section label="background">
        <p>{d.background}</p>
      </Section>

      <Section label="связанные работы">
        <MiniTable
          headers={['связь', 'работа', 'тип', 'url']}
          rows={(d.relations || []).map((r) => [
            r.relation,
            entryNames(r.entry),
            good(Array.isArray(r.entry) ? r.entry : [r.entry]).map((e) => e.type).join('; '),
            good(Array.isArray(r.entry) ? r.entry : [r.entry]).map((e) => e.url).join('; '),
          ])}
        />
      </Section>

      <Section label="opening / ending темы">
        <Facts
          items={[
            ['opening', themes?.data?.openings || []],
            ['ending', themes?.data?.endings || []],
          ]}
        />
      </Section>

      <Section label="внешние id (привязка между базами)">
        <MiniTable
          headers={['база', 'id', 'url']}
          rows={(ext?.data || []).map((e) => [e.name, e.mal_id ?? '—', e.url])}
        />
      </Section>

      <Section label="трейлер">
        {d.trailer ? (
          <div>
            {d.trailer.images?.maximum_image_url ? (
              <img
                src={d.trailer.images.maximum_image_url}
                alt=""
                loading="lazy"
                referrerPolicy="no-referrer"
                style={{ width: 240, border: '1px solid var(--line-soft)', marginBottom: 8 }}
              />
            ) : null}
            <br />
            {d.trailer.youtube_id ? (
              <a
                className="vid-link"
                href={`https://www.youtube.com/watch?v=${d.trailer.youtube_id}`}
                target="_blank"
                rel="noreferrer"
              >
                youtube: {d.trailer.youtube_id}
              </a>
            ) : null}
            {d.trailer.embed_url ? (
              <>
                <br />
                <a className="vid-link" href={d.trailer.embed_url} target="_blank" rel="noreferrer">
                  embed: {d.trailer.embed_url}
                </a>
              </>
            ) : null}
          </div>
        ) : (
          '—'
        )}
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

      <Section label="персонажи">
        <MiniTable
          headers={['роль', 'персонаж', 'сэйю']}
          rows={good(chars?.data).map((c) => [
            c.role,
            c.character?.name,
            (c.voice_actors || []).map((v) => v.name).join(', ') || '—',
          ])}
        />
      </Section>

      <Section label="персонал">
        <MiniTable
          headers={['роль', 'имя']}
          rows={good(staff?.data).map((s) => [s.positions?.join(', '), s.person?.name])}
        />
      </Section>

      <Section label="рекомендации">
        <MiniTable
          headers={['рекомендуют', 'эпизодов']}
          rows={(reco?.data || []).map((r) => [
            entryNames(r.entry) || (r.title ?? '—'),
            r.episodes ?? '—',
          ])}
        />
      </Section>

      <Section label="постеры и скриншоты">
        <Imgs
          urls={good(pics?.data)
            .map((p) => p.webp?.large || p.jpg?.large)
            .filter(Boolean)}
        />
      </Section>

      <Section label="эпизоды (страница 1)">
        <MiniTable
          headers={['№', 'название', 'дата']}
          rows={good(eps?.data).map((e) => [
            e.mal_id,
            e.title,
            e.aired?.slice(0, 10) ?? '—',
          ])}
        />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={d}
          skip={[
            'mal_id',
            'url',
            'images',
            'trailer',
            'approved',
            'titles',
            'title',
            'title_english',
            'title_japanese',
            'title_synonyms',
            'type',
            'source',
            'episodes',
            'status',
            'airing',
            'aired',
            'duration',
            'rating',
            'season',
            'year',
            'broadcast',
            'score',
            'scored_by',
            'rank',
            'popularity',
            'members',
            'favorites',
            'synopsis',
            'background',
            'producers',
            'licensors',
            'studios',
            'genres',
            'explicit_genres',
            'themes',
            'demographics',
            'relations',
            'synopsis_url',
          ]}
        />
        <Everything
          data={raw}
          skip={[
            'id',
            'data',
            'characters',
            'staff',
            'recommendations',
            'statistics',
            'themes',
            'pictures',
            'episodes',
            'external',
            'videos',
          ]}
        />
      </Section>
        </>
      ) : null}

      <JsonBlock data={raw} />
    </>
  )
}

/* ------------------------------ Kitsu ------------------------------- */

export function KitsuPanel({ raw }) {
  const a = raw.attributes
  const chars = raw.characters || []

  return (
    <>
      <Meta sourceKey="kitsu" raw={raw} />
      {errNote(raw)}

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
            ['id', raw.id],
            ['подтип', a.subtype],
            ['showType', a.showType],
            ['статус', a.status],
            ['tba', a.tba],
            ['начало', a.startDate],
            ['конец', a.endDate],
            ['эпизодов', a.episodeCount],
            ['длительность (эп.)', a.episodeLength != null ? `${a.episodeLength} мин` : null],
            ['суммарно', a.totalLength != null ? `${a.totalLength} мин` : null],
            ['возрастной рейтинг', a.ageRating],
            ['пояснение к рейтингу', a.ageRatingGuide],
            ['nsfw', a.nsfw],
            ['youtube video id', a.youtubeVideoId],
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

      <Section label="распределение оценок">
        {a.ratingFrequencies ? (
          <div>
            {Object.entries(a.ratingFrequencies).map(([k, v]) => (
              <div className="rating-bar-row" key={k}>
                <span style={{ minWidth: 34 }}>{k}</span>
                <span className="bar">
                  <i style={{ width: `${Math.min(100, Number(v) / 40)}%` }} />
                </span>
                <span>{v}</span>
              </div>
            ))}
          </div>
        ) : null}
      </Section>

      <Section label="категории">
        <Chips items={raw.categories?.map((c) => c.title).filter(Boolean)} hi />
      </Section>

      <Section label="жанры">
        <Chips items={raw.genres?.map((g) => g.title).filter(Boolean)} />
      </Section>

      <Section label="стриминг">
        <MiniTable
          headers={['сервис', 'url']}
          rows={(raw.streamingLinks || []).map((l) => [l.streamer, l.url])}
        />
      </Section>

      <Section label="связи медиа">
        <MiniTable
          headers={['роль', 'id', 'тип']}
          rows={(raw.mediaRelationships || []).map((m) => [
            m.role,
            m.media?.id,
            m.media?.type,
          ])}
        />
      </Section>

      <Section label="персонажи">
        <div className="cast-grid">
          {(chars || []).map((c) => {
            const rel = c.relationships || {}
            const charAttr = c.attributes || {}
            return (
              <div className="cast-item" key={c.id}>
                <b>{charAttr.name || '—'}</b>
                <span className="sub">{charAttr.role ?? (rel.role?.data || {}).id ? 'персонаж' : ''}</span>
              </div>
            )
          })}
        </div>
      </Section>

      <Section label="эпизоды (30)">
        <MiniTable
          headers={['№', 'название', 'дата']}
          rows={(raw.episodes || []).map((e) => [
            e.attributes?.number ?? e.attributes?.relativeNumber,
            e.attributes?.canonicalTitle ?? '—',
            e.attributes?.airdate ?? '—',
          ])}
        />
      </Section>

      <Section label="постеры / обложка">
        <Imgs
          urls={[a.posterImage?.original, a.posterImage?.large, a.coverImage?.original, a.coverImage?.large].filter(
            Boolean,
          )}
        />
      </Section>

      <Section label="синопсис">
        <p>{a.synopsis}</p>
      </Section>

      <Section label="вложенные языки">
        <List items={raw.languages?.map((l) => l.attributes?.name)} />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={raw}
          skip={[
            'id',
            'attributes',
            'characters',
            'character_included',
            'episodes',
            'languages',
            'categories',
            'genres',
            'streamingLinks',
            'mediaRelationships',
            'relationship_ids',
          ]}
        />
        <Everything
          data={a}
          skip={[
            'createdAt',
            'updatedAt',
            'slug',
            'synopsis',
            'description',
            'titles',
            'canonicalTitle',
            'abbreviatedTitles',
            'averageRating',
            'ratingFrequencies',
            'userCount',
            'favoritesCount',
            'startDate',
            'endDate',
            'nextRelease',
            'popularityRank',
            'ratingRank',
            'ageRating',
            'ageRatingGuide',
            'subtype',
            'status',
            'tba',
            'posterImage',
            'coverImage',
            'episodeCount',
            'episodeLength',
            'totalLength',
            'youtubeVideoId',
            'showType',
            'nsfw',
          ]}
        />
      </Section>

      <JsonBlock data={raw} />
    </>
  )
}

/* ---------------------------- Shikimori ----------------------------- */

export function ShikimoriPanel({ raw }) {
  const an = raw.anime
  const roles = raw.roles || []
  const img = (p) =>
    p && !p.includes('/assets/globals/missing_') ? `https://shikimori.one${p}` : null
  const chars = roles
    .filter((r) => r.character)
    .map((r) => ({
      ...r.character,
      _role: (r.roles_russian || r.roles || []).join(', '),
    }))
    .sort((a, b) => (a._role.includes('Main') ? -1 : b._role.includes('Main') ? 1 : 0))
  const staff = roles.filter((r) => r.person)

  return (
    <>
      <Meta sourceKey="shikimori" raw={raw} />
      {errNote(raw)}

      <Section label="названия">
        <Facts
          items={[
            ['основное', an.name],
            ['русское', an.russian],
            ['английское', an.english],
            ['японское', an.japanese],
            ['синонимы', an.synonyms],
            ['url', an.url],
          ]}
        />
      </Section>

      <Section label="факты">
        <Facts
          items={[
            ['id', an.id],
            ['id MAL', an.myanimelist_id],
            ['kind', an.kind],
            ['score', an.score != null ? `${an.score} / 10` : null],
            ['статус', an.status],
            ['эпизодов', an.episodes],
            ['вышло эпизодов', an.episodes_aired],
            ['премьера', an.aired_on],
            ['финал', an.released_on],
            ['возрастной рейтинг', an.rating],
            ['в избранном', an.favourites],
            ['лицензия (RU)', an.license_name_ru],
            ['франшиза', an.franchise],
            ['thread_id', an.thread_id],
            ['topic_id', an.topic_id],
            ['обновлено', an.updated_at?.slice(0, 16)],
            ['след. эпизод', an.next_episode_at],
            ['анонс', an.anons || null],
            ['онгоинг', an.ongoing || null],
            ['в избранном (favoured)', an.favoured || null],
          ]}
        />
      </Section>

      <Section label="зрители по статусам">
        <Facts
          items={(an.rates_statuses_stats || raw.statuses_stats || []).map((s) => [
            s.name ?? s.status,
            s.value ?? null,
          ])}
        />
      </Section>

      <Section label="распределение оценок (1–10)">
        {an.rates_scores_stats || an.scores_stats ? (
          <div>
            {(() => {
              const arr = an.rates_scores_stats || an.scores_stats
              const max = Math.max(1, ...arr.map((s) => (s.value != null ? s.value : s.count) || 0))
              return [...arr]
                .reverse()
                .map((s) => {
                  const score = s.name ?? s.value
                  const count = s.value ?? s.count
                  return (
                    <div className="rating-bar-row" key={typeof score === 'string' ? score : String(score)}>
                      <span style={{ minWidth: 28 }}>{score}</span>
                      <span className="bar">
                        <i style={{ width: `${Math.min(100, (count / max) * 100)}%` }} />
                      </span>
                      <span>{count}</span>
                    </div>
                  )
                })
            })()}
          </div>
        ) : null}
      </Section>

      <Section label="команда озвучки и лицензиары">
        <Facts
          items={[
            ['fansubbers', an.fansubbers],
            ['fandubbers', an.fandubbers],
            ['licensors', an.licensors],
          ]}
        />
      </Section>

      <Section label="жанры">
        <Chips
          items={an.genres?.map((g) => (g.russian ? `${g.name} / ${g.russian}` : g.name))}
          hi
        />
      </Section>

      <Section label="студии">
        <Chips items={an.studios?.map((s) => s.name)} />
      </Section>

      <Section label="описание">
        {an.description_html ? <Html html={an.description_html} /> : <p>{an.description}</p>}
      </Section>

      <Section label="видео / тизеры">
        <MiniTable
          headers={['кадр', 'тип', 'название', 'url']}
          rows={(an.videos || []).map((v, i) => [
            v.image_url ? (
              <img
                key={i}
                src={v.image_url}
                alt=""
                loading="lazy"
                referrerPolicy="no-referrer"
                style={{ width: 120, border: '1px solid var(--line-soft)' }}
              />
            ) : (
              '—'
            ),
            v.kind ?? 'video',
            v.name ?? '',
            <a key={v.url} href={v.url} target="_blank" rel="noreferrer">
              {v.url}
            </a>,
          ])}
        />
      </Section>

      <Section label="скриншоты">
        <Imgs urls={(an.screenshots || []).map((s) => img(s.original)).filter(Boolean)} />
      </Section>

      <Section label="роли (персонажи с фото)">
        <div className="cast-grid">
          {chars.map((c) => (
            <div className="cast-item" key={c.id}>
              {img(c.image?.preview || c.image?.original || c.image?.x96) ? (
                <img
                  src={img(c.image?.preview || c.image?.original || c.image?.x96)}
                  alt=""
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  style={{ width: 52, border: '1px solid var(--line-soft)' }}
                />
              ) : null}
              <b>{c.russian || c.name}</b>
              <span className="sub">{c.name}</span>
              <span className="sub">{c._role}</span>
              {c.url ? (
                <a
                  className="sub"
                  href={`https://shikimori.one${c.url}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  страница персонажа ↗
                </a>
              ) : null}
            </div>
          ))}
        </div>
      </Section>

      <Section label={`персонал (режиссёры, сценаристы и др.) · ${staff.length}`}>
        <MiniTable
          headers={['фото', 'имя', 'роль']}
          rows={staff.map((r) => [
            img(r.person.image?.preview || r.person.image?.original) ? (
              <img
                key={r.person.id}
                src={img(r.person.image?.preview || r.person.image?.original)}
                alt=""
                loading="lazy"
                referrerPolicy="no-referrer"
                style={{ width: 40, border: '1px solid var(--line-soft)' }}
              />
            ) : (
              '—'
            ),
            <span key={r.person.id}>
              <b>{r.person.russian || r.person.name}</b> <span className="sub">{r.person.name}</span>
            </span>,
            (r.roles_russian || r.roles || []).join(', '),
          ])}
        />
      </Section>

      <Section label="похожие">
        <List
          items={(raw.similar || []).map((s) => `${s.name}${s.russian ? ` / ${s.russian}` : ''} (score ${s.score})`)}
        />
      </Section>

      <Section label="связанные">
        <MiniTable
          headers={['связь', 'работа']}
          rows={(raw.related || []).map((r) => [
            r.relation,
            r.anime?.russian || r.anime?.name || r.manga?.russian || r.manga?.name || '—',
          ])}
        />
      </Section>

      <Section label="франшиза (узлы)">
        <MiniTable
          headers={['id', 'дата', 'название']}
          rows={(raw.franchise?.nodes || []).map((f) => [
            f.id,
            f.date ? new Date(f.date * 1000).toISOString().slice(0, 10) : '—',
            f.name ?? '—',
          ])}
        />
      </Section>

      <Section label="франшиза (связи)">
        <MiniTable
          headers={['source', 'target', 'вес']}
          rows={(raw.franchise?.links || []).map((l) => [
            `${l.source_id} (${l.source})`,
            `${l.target_id} (${l.target})`,
            l.weight ?? '—',
          ])}
        />
      </Section>

      <Section label="текущая медиа во франшизе">
        <p style={{ fontFamily: 'var(--mono)', fontSize: 12 }}>{raw.franchise?.current_id ?? '—'}</p>
      </Section>

      <Section label="внешние ссылки">
        <MiniTable
          headers={['тип', 'url']}
          rows={(raw.external_links || []).map((l) => [
            l.kind ?? l.label,
            l.url ? (
              <a key={l.url} href={l.url} target="_blank" rel="noreferrer">
                {l.url}
              </a>
            ) : (
              '—'
            ),
          ])}
        />
      </Section>

      <Section label="постер">
        <Imgs
          urls={[
            img(an.image?.original),
            img(an.image?.preview),
            img(an.image?.x96),
            img(an.image?.x48),
          ].filter(Boolean)}
        />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={raw}
          skip={[
            'id',
            'anime',
            'roles',
            'similar',
            'related',
            'franchise',
            'external_links',
          ]}
        />
        <Everything
          data={an}
          skip={[
            'id',
            'name',
            'russian',
            'image',
            'url',
            'kind',
            'score',
            'status',
            'episodes',
            'episodes_aired',
            'aired_on',
            'released_on',
            'rating',
            'english',
            'japanese',
            'synonyms',
            'license_name_ru',
            'duration',
            'description',
            'description_html',
            'description_source',
            'franchise',
            'favoured',
            'anons',
            'ongoing',
            'thread_id',
            'topic_id',
            'myanimelist_id',
            'rates_scores_stats',
            'rates_statuses_stats',
            'updated_at',
            'next_episode_at',
            'fansubbers',
            'fandubbers',
            'licensors',
            'genres',
            'studios',
            'videos',
            'screenshots',
            'user_rate',
          ]}
        />
      </Section>

      <JsonBlock data={raw} />
    </>
  )
}

/* ----------------------------- Bangumi ------------------------------ */

export function BangumiPanel({ raw }) {
  const s = raw.subject

  return (
    <>
      <Meta sourceKey="bangumi" raw={raw} />
      {errNote(raw)}

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
            ['эпизодов (инфобокс)', s.eps],
            ['эпизодов (всего)', s.total_episodes],
            ['версия', s.volumes ?? s.bns ?? null],
            ['series', s.series || null],
            ['locked', s.locked || null],
            ['nsfw', s.nsfw || null],
            ['type', s.type],
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
                    <i
                      style={{
                        width: `${Math.min(100, (v / Math.max(1, s.rating.total)) * 100)}%`,
                      }}
                    />
                  </span>
                  <span>{v}</span>
                </div>
              ))}
          </div>
        ) : null}
      </Section>

      <Section label="мета-теги">
        <Chips items={s.meta_tags} hi />
      </Section>

      <Section label="инфобокс (все поля)">
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

      <Section label="теги (с весом)">
        <div className="chips">
          {(s.tags || []).map((t) => (
            <span className="chip hi" key={t.name}>
              {t.name} · {t.count}
            </span>
          ))}
        </div>
      </Section>

      <Section label="описание">
        <p>{s.summary}</p>
      </Section>

      <Section label="персонажи">
        <div className="cast-grid">
          {(raw.characters || []).map((c) => (
            <div className="cast-item" key={c.id ?? c.name}>
              {c.images?.small || c.images?.grid ? (
                <img
                  src={c.images.small || c.images.grid}
                  alt=""
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  style={{ width: 44, border: '1px solid var(--line-soft)' }}
                />
              ) : null}
              <b>{c.name}</b>
              <span className="sub">{c.role ?? '—'}</span>
              <span className="sub">{(c.actors || []).map((a) => a.name).join(', ') || ''}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section label="люди / создатели">
        <MiniTable
          headers={['имя', 'роль']}
          rows={(raw.persons || []).map((p) => [p.name, p.role ?? '—'])}
        />
      </Section>

      <Section label="эпизоды">
        <MiniTable
          headers={['№', 'название', 'дата']}
          rows={(raw.episodes || []).map((e) => [
            e.ep,
            e.name || e.name_cn,
            e.airdate ?? '—',
          ])}
        />
      </Section>

      <Section label="обложки">
        <Imgs
          urls={[
            s.images?.large,
            s.images?.medium,
            s.images?.small,
            s.images?.grid,
            s.images?.common,
          ].filter(Boolean)}
        />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything data={raw} skip={['subject', 'characters', 'persons', 'episodes']} />
        <Everything
          data={s}
          skip={[
            'date',
            'platform',
            'images',
            'summary',
            'name',
            'name_cn',
            'tags',
            'infobox',
            'rating',
            'total_episodes',
            'collection',
            'id',
            'eps',
            'meta_tags',
            'volumes',
            'series',
            'locked',
            'nsfw',
            'type',
          ]}
        />
      </Section>

      <JsonBlock data={raw} />
    </>
  )
}

/* --------------------------- Anime-Planet --------------------------- */

export function AnimePlanetPanel({ raw }) {
  const p = raw
  return (
    <>
      <Meta sourceKey="anime_planet" raw={raw} />
      {errNote(raw)}

      <Section label="названия">
        <Facts
          items={[
            ['основное', p.title],
            ['альт. названия', p.alt_titles],
          ]}
        />
      </Section>

      <Section label="данные страницы">
        <Facts
          items={[
            ['entry bar', p.entry_bar],
            ['рейтинг', p.rating_text],
            ['пользователи', p.user_stats],
            ['url', p.url],
          ]}
        />
      </Section>

      <Section label="теги">
        <Chips items={p.tags} hi />
      </Section>

      <Section label="персонажи">
        <div className="cast-grid">
          {(p.characters || []).map((c) => (
            <div className="cast-item" key={c.character_id ?? c.name}>
              <b>{c.name}</b>
              {c.voice_actor ? <span>{c.voice_actor}</span> : null}
              <span className="sub">
                {c.comments ? `${c.comments} комм.` : ''} {c.url ? `· ${c.url.split('/').pop()}` : ''}
              </span>
              {c.image ? (
                <img src={c.image} alt="" loading="lazy" referrerPolicy="no-referrer" style={{ width: 60 }} />
              ) : null}
            </div>
          ))}
        </div>
      </Section>

      <Section label="персонал">
        <MiniTable
          headers={['имя', 'url']}
          rows={(p.staff || []).map((s) => [s.name, s.url ? s.url.split('/').pop() : '—'])}
        />
      </Section>

      <Section label="если нравится, понравится...">
        <MiniTable
          headers={['тайтл', 'рейтинг']}
          rows={(p.recommendations || []).map((r) => [r.title, r.rating ?? '—'])}
        />
      </Section>

      <Section label="связанные аниме">
        <MiniTable
          headers={['тайтл', 'мета']}
          rows={(p.related?.anime || []).map((r) => [r.title, r.meta])}
        />
      </Section>

      <Section label="связанная манга">
        <MiniTable
          headers={['тайтл', 'мета']}
          rows={(p.related?.manga || []).map((r) => [r.title, r.meta])}
        />
      </Section>

      <Section label="синопсис">
        <p>{p.synopsis}</p>
      </Section>

      <Section label="секции страницы">
        <List items={p.section_headers} />
      </Section>

      <Section label="скриншоты / кадры">
        <Imgs urls={(p.screenshots || []).filter(Boolean)} />
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything
          data={raw}
          skip={[
            'slug',
            'url',
            'title',
            'alt_titles',
            'synopsis',
            'entry_bar',
            'rating_text',
            'user_stats',
            'tags',
            'characters',
            'staff',
            'recommendations',
            'related',
            'screenshots',
            'section_headers',
          ]}
        />
      </Section>

      <JsonBlock data={raw} />
    </>
  )
}

/* ---------------------------- AnimeThemes --------------------------- */

export function AnimeThemesPanel({ raw }) {
  const a = raw.anime
  if (!a) {
    return (
      <>
        <Meta sourceKey="anime_themes" raw={raw} />
        <div style={{ color: '#6f6757' }}>{raw.error ?? 'нет данных'}</div>
      </>
    )
  }
  const themes = a.animethemes || []

  return (
    <>
      <Meta sourceKey="anime_themes" raw={raw} />
      {errNote(raw)}

      <Section label="факты">
        <Facts
          items={[
            ['название', a.name],
            ['формат', a.media_format],
            ['сезон', a.season],
            ['год', a.year],
            ['slug', a.slug],
            ['число тем', themes.length],
          ]}
        />
      </Section>

      <Section label="синопсис">
        <p>{a.synopsis}</p>
      </Section>

      <Section label="темы (все поля)">
        <div className="mini-scroll">
          <table className="mini">
            <thead>
              <tr>
                <th>тип</th>
                <th>группа</th>
                <th>песня</th>
                <th>исполнители</th>
                <th>эпизоды</th>
                <th>версия</th>
                <th>флаги</th>
                <th>видео</th>
              </tr>
            </thead>
            <tbody>
              {themes.flatMap((th) =>
                (th.animethemeentries || []).map((e, i) => (
                  <tr key={`${th.id}-${i}`}>
                    <td>
                      {th.type} {th.seq}
                    </td>
                    <td>{th.group ?? '—'}</td>
                    <td>
                      <b>{th.song?.title ?? '—'}</b>
                    </td>
                    <td>{(th.song?.artists || []).map((ar) => ar.name).join(', ') || '—'}</td>
                    <td>{e.episodes ?? '—'}</td>
                    <td>{e.version}</td>
                    <td>
                      {[
                        e.nsfw ? 'nsfw' : null,
                        e.spoiler ? 'spoiler' : null,
                        e.notes ? 'note' : null,
                      ]
                        .filter(Boolean)
                        .join(', ') || '—'}
                    </td>
                    <td>
                      {(e.videos || []).map((v) => (
                        <div key={v.id ?? v.basename}>
                          <a href={v.link} target="_blank" rel="noreferrer">
                            {v.filename || v.basename}
                          </a>{' '}
                          <span style={{ fontSize: 10.5, color: 'var(--faint)' }}>
                            [{v.resolution}p · {(v.size / 1048576).toFixed(1)} MB · {v.source} ·{' '}
                            {v.subbed ? 'sub' : ''}
                            {v.uncen ? '/uncen' : ''}
                            {v.nc ? '/nc' : ''}
                            {v.lyrics ? '/lyrics' : ''} · tags: {v.tags ?? '—'} · overlap:{' '}
                            {v.overlap}]
                          </span>
                        </div>
                      ))}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </Section>

      <Section label="все прочие поля (авто)">
        <Everything data={raw} skip={['id', 'slug', 'anime']} />
      </Section>

      <JsonBlock data={raw} />
    </>
  )
}
