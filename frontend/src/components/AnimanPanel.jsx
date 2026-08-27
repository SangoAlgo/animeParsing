import { useState, useEffect } from 'react'
import { Facts, Chips, MiniTable, List } from './Bits.jsx'
import { AniKodikPlayer } from './AniKodikPlayer.jsx'

const LANG_LABEL = { en: 'EN', ja: 'JP', ru: 'RU', uk: 'UK', zh: 'ZH' }
const THEME_RU = { OP: 'ОПЕНИНГ', ED: 'ЭНДИНГ', INS: 'ВСТАВКА' }

function langBadge(lang) {
  return <span className={`chip lang-${lang || 'en'}`}>{LANG_LABEL[lang] || (lang ? lang.toUpperCase() : 'EN')}</span>
}

function chapterIdOf(md, n) {
  const s = String(n)
  for (const v of md?.volumes_en || []) {
    for (const c of v.chapters || []) {
      if (String(c.n) === s) return c.id || null
    }
  }
  return null
}

function chLink(md, n) {
  const id = chapterIdOf(md, n)
  return id ? `https://mangadex.org/chapter/${id}` : null
}

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

export default function AnimanPanel({ panel, title, titleKey, mangaMap }) {
  const a = panel
  const map = mangaMap || a.manga?.map || {}

  const [lightboxItem, setLightboxItem] = useState(null)
  const [videoModal, setVideoModal] = useState(null)

  return (
    <div className="animan-root">
      <AniHero
        titles={a.titles}
        posters={a.posters}
        banners={a.banners}
        facts={a.facts}
        scores={a.scores}
        trailer={a.trailer}
        nextAiring={a.episodes?.next_airing}
        onOpenImage={(item) => setLightboxItem(item)}
        onPlayTrailer={() => {
          if (a.trailer?.embed_url || a.trailer?.url) {
            setVideoModal({ title: 'Официальный трейлер', url: a.trailer.embed_url || a.trailer.url })
          }
        }}
      />

      {a.airing_schedule?.next_episode || a.airing_schedule?.is_airing ? (
        <section id="sec-airing">
          <AniAiringCard airing={a.airing_schedule} />
        </section>
      ) : null}

      <AniNav
        hasPlayer={Boolean(Object.keys(a.kodik || {}).length)}
        hasEpisodes={Boolean(a.episodes?.items?.length)}
        hasSakuga={Boolean(a.sakuga?.length)}
        hasOst={Boolean(a.discography)}
        hasWatchOrder={Boolean(a.watch_order)}
        hasVerdict={Boolean(a.verdict)}
        hasFaq={Boolean(a.faq?.length)}
      />

      {Object.keys(a.kodik || {}).length > 0 ? (
        <section id="sec-player">
          <AniKodikPlayer animan={a} title={title} titleKey={titleKey || a.key} />
        </section>
      ) : null}

      {a.verdict ? (
        <section id="sec-verdict">
          <AniVerdictBox verdict={a.verdict} />
        </section>
      ) : null}

      {a.awards?.length ? (
        <section id="sec-awards">
          <AniAwards awards={a.awards} />
        </section>
      ) : null}

      <section id="sec-scores">
        <AniScores scores={a.scores} contentGuide={a.content_guide} />
      </section>

      <section id="sec-desc">
        <AniDescription desc={a.description} facts={a.facts} />
      </section>

      {a.watch_order ? (
        <section id="sec-watchorder">
          <AniWatchOrderTimeline watchOrder={a.watch_order} />
        </section>
      ) : null}

      {a.faq?.length ? (
        <section id="sec-faq">
          <AniFAQ faq={a.faq} />
        </section>
      ) : null}

      {a.voiceover?.fandubbers?.length || a.voiceover?.licensors?.length ? (
        <section id="sec-voiceover">
          <AniVoiceover voiceover={a.voiceover} />
        </section>
      ) : null}

      <section id="sec-gallery">
        <AniVisualsVault
          posters={a.posters}
          banners={a.banners}
          gallery={a.gallery}
          promos={a.promo_videos}
          onOpenImage={(item) => setLightboxItem(item)}
          onOpenVideo={(v) => setVideoModal({ title: v.title, url: v.player_url || v.url })}
        />
      </section>

      {a.episodes?.items?.length ? (
        <section id="sec-episodes">
          <AniEpisodes episodes={a.episodes} fillers={a.fillers} />
        </section>
      ) : null}

      {a.sakuga?.length ? (
        <section id="sec-sakuga">
          <AniSakuga
            sakuga={a.sakuga}
            onPlayClip={(c) => setVideoModal({ title: `Сакуга · ${c.animators?.join(', ') || 'Ключевая анимация'}`, url: c.file_url, isVideoFile: true })}
          />
        </section>
      ) : null}

      <section id="sec-themes">
        <AniThemes themes={a.themes} discography={a.discography} />
      </section>

      <section id="sec-characters">
        <AniCharacters characters={a.characters} />
      </section>

      <section id="sec-staff">
        <AniStaff staff={a.staff} />
      </section>

      <section id="sec-manga">
        <AniManga manga={a.manga} mangaMap={map} />
      </section>

      <section id="sec-franchise">
        <AniFranchise franchise={a.franchise} />
      </section>

      <section id="sec-links">
        <AniExternal external={a.external_links} />
      </section>

      <section id="sec-names">
        <AniNames titles={a.titles} />
      </section>

      {/* Enhanced Lightbox Modal with Resolution Switcher */}
      {lightboxItem ? (
        <LightboxModal item={lightboxItem} onClose={() => setLightboxItem(null)} />
      ) : null}

      {/* Video Modal */}
      {videoModal ? (
        <div className="modal-overlay" onClick={() => setVideoModal(null)}>
          <div className="modal-content video-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span>{videoModal.title}</span>
              <button className="modal-close" onClick={() => setVideoModal(null)}>✕</button>
            </div>
            {videoModal.isVideoFile ? (
              <video
                src={videoModal.url}
                controls
                autoPlay
                className="modal-video-element"
              />
            ) : videoModal.url.includes('youtube.com') || videoModal.url.includes('youtu.be') ? (
              <iframe
                className="modal-iframe"
                src={videoModal.url.replace('watch?v=', 'embed/').split('&')[0]}
                title={videoModal.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div style={{ padding: 20, textAlign: 'center' }}>
                <a href={videoModal.url} target="_blank" rel="noreferrer" className="btn-read">
                  Открыть видео ↗
                </a>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Navigation Sticky Bar                                               */
/* ------------------------------------------------------------------ */

function AniNav({ hasPlayer, hasEpisodes, hasSakuga, hasOst: _hasOst, hasWatchOrder, hasVerdict, hasFaq }) {
  const links = [
    ...(hasPlayer ? [{ target: 'sec-player', label: '🎬 Смотреть онлайн' }] : []),
    ...(hasVerdict ? [{ target: 'sec-verdict', label: '💡 Экспресс-вердикт' }] : []),
    { target: 'sec-scores', label: 'Рейтинги' },
    { target: 'sec-desc', label: 'Описание' },
    ...(hasWatchOrder ? [{ target: 'sec-watchorder', label: '🗺️ Порядок просмотра' }] : []),
    ...(hasFaq ? [{ target: 'sec-faq', label: '❓ Вопросы и Ответы' }] : []),
    { target: 'sec-gallery', label: '📸 Постеры и Арт' },
    ...(hasEpisodes ? [{ target: 'sec-episodes', label: 'Эпизоды и Канон' }] : []),
    ...(hasSakuga ? [{ target: 'sec-sakuga', label: 'Сакуга' }] : []),
    { target: 'sec-themes', label: 'Музыка и OST' },
    { target: 'sec-characters', label: 'Персонажи и Сэйю' },
    { target: 'sec-staff', label: 'Создатели' },
    { target: 'sec-manga', label: 'Манга и Главы' },
    { target: 'sec-franchise', label: 'Франшиза' },
    { target: 'sec-links', label: 'Ссылки' },
  ]

  return (
    <nav className="inpage-nav">
      {links.map((l) => (
        <button
          key={l.target}
          type="button"
          onClick={() => scrollToSection(l.target)}
          className="inpage-nav__link"
        >
          {l.label}
        </button>
      ))}
    </nav>
  )
}

/* ------------------------------------------------------------------ */
/* Hero Header & Multi-Cover Switcher                                  */
/* ------------------------------------------------------------------ */

function AniHero({ titles, posters, banners, facts, scores, trailer, nextAiring, onOpenImage, onPlayTrailer }) {
  const t = titles?.main || {}
  const [selectedPosterIdx, setSelectedPosterIdx] = useState(0)

  const posterList = posters || []
  const currentPoster = posterList[selectedPosterIdx] || posterList[0]
  const posterUrl = currentPoster?.url
  const banner = banners?.[0]?.url
  const ruTitle = t.ru || t.en
  const avg = scores?.average

  return (
    <div className="hero-box">
      {banner ? (
        <div
          className="hero-backdrop"
          style={{ backgroundImage: `linear-gradient(180deg, rgba(17,14,10,.2) 0%, rgba(17,14,10,.95) 100%), url(${banner})` }}
        />
      ) : null}
      <div className="hero-content">
        {posterUrl ? (
          <div className="hero-poster-column">
            <div
              className="hero-poster-wrap"
              onClick={() => onOpenImage && onOpenImage({ url: posterUrl, title: currentPoster?.title || ruTitle, source: currentPoster?.source || 'Постер' })}
              title="Нажмите, чтобы открыть в полном размере"
            >
              <img src={posterUrl} alt={ruTitle} className="hero-poster-img" referrerPolicy="no-referrer" />
              <div className="poster-zoom-hint">🔍 Открыть</div>
            </div>

            {posterList.length > 1 ? (
              <div className="hero-poster-thumbs">
                {posterList.map((p, idx) => (
                  <button
                    key={p.url || idx}
                    type="button"
                    className={`poster-thumb-btn ${idx === selectedPosterIdx ? 'active' : ''}`}
                    onClick={() => setSelectedPosterIdx(idx)}
                    title={p.title || `Постер ${idx + 1}`}
                  >
                    <img src={p.url} alt="" className="poster-mini-thumb" />
                    <span className="poster-thumb-label">{p.source || (idx === 0 ? 'Аниме' : 'Манга')}</span>
                  </button>
                ))}
              </div>
            ) : null}

            {currentPoster?.resolutions ? (
              <div className="hero-poster-res-tiers">
                <span className="res-tiers-caption">Качество:</span>
                <div className="res-tiers-row">
                  {Object.entries(currentPoster.resolutions).map(([rKey, rUrl]) => {
                    const labels = {
                      extra_large: 'Ultra HD',
                      large: '500px',
                      medium: '250px',
                      original: 'Оригинал',
                      preview: '320px',
                      large_512: '512px',
                      thumb_256: '256px',
                      x96: '96px',
                      x48: '48px',
                    }
                    return (
                      <button
                        key={rKey}
                        type="button"
                        className="res-tier-pill"
                        onClick={() => onOpenImage && onOpenImage({
                          url: rUrl,
                          title: `${currentPoster.title} [${labels[rKey] || rKey}]`,
                          source: currentPoster.source,
                          resolutions: currentPoster.resolutions,
                        })}
                        title={`Открыть постер в разрешении ${labels[rKey] || rKey}`}
                      >
                        {labels[rKey] || rKey}
                      </button>
                    )
                  })}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        <div className="hero-main-info">
          <div className="badge-source">
            <span className="dot on" />
            ANIMAN · ЕДИНОЕ ДОСЬЕ ИЗ 4 ИСТОЧНИКОВ
          </div>
          <h1 className="hero-ru-title">{ruTitle}</h1>
          <div className="hero-subtitles">
            {t.en && t.en !== ruTitle ? <span className="sub-en">{t.en}</span> : null}
            {t.ja ? <span className="sub-ja">{t.ja}</span> : null}
            {t.romaji && t.romaji !== t.en ? <span className="sub-romaji">{t.romaji}</span> : null}
          </div>

          {nextAiring ? (
            <div className="next-airing-badge">
              <span className="pulse-dot" />
              <span>Серия {nextAiring.episode} выйдет через {Math.round(nextAiring.timeUntilAiring / 86400)} дн. ({new Date(nextAiring.airingAt * 1000).toLocaleDateString('ru-RU')})</span>
            </div>
          ) : null}

          <div className="facts-pill-row">
            {facts.format_ru ? <span className="pill pill--accent">{facts.format_ru}</span> : null}
            {facts.episodes_total != null ? (
              <span className="pill">{facts.episodes_total} эп.{facts.duration_min ? ` по ${facts.duration_min} мин` : ''}</span>
            ) : null}
            {facts.season ? <span className="pill">{facts.season}</span> : null}
            {facts.status_ru ? <span className="pill pill--status">{facts.status_ru}</span> : null}
            {facts.age_rating_ru ? <span className="pill pill--age">{facts.age_rating_ru}</span> : null}
            {facts.origin_ru ? <span className="pill">по {facts.origin_ru}</span> : null}
          </div>

          {facts.studios?.length ? (
            <div className="hero-studios">
              <span className="meta-label">Студия:</span>
              {facts.studios.map((st) => (
                <span key={st} className="studio-name">{st}</span>
              ))}
            </div>
          ) : null}

          <div className="hero-actions">
            {trailer ? (
              <button className="btn-action btn-action--primary" onClick={onPlayTrailer}>
                ▶ СМОТРЕТЬ ТРЕЙЛЕР
              </button>
            ) : null}
            <button type="button" onClick={() => scrollToSection('sec-episodes')} className="btn-action">
              📺 ЭПИЗОДЫ
            </button>
            <button type="button" onClick={() => scrollToSection('sec-sakuga')} className="btn-action">
              🎬 САКУГА
            </button>
            <button type="button" onClick={() => scrollToSection('sec-themes')} className="btn-action">
              🎵 МУЗЫКА И OST
            </button>
            <button type="button" onClick={() => scrollToSection('sec-manga')} className="btn-action">
              📖 МАНГА
            </button>
            {avg ? (
              <div className="hero-rating-badge" onClick={() => scrollToSection('sec-scores')} style={{ cursor: 'pointer' }}>
                <span className="star">★</span>
                <span className="score-val">{avg}</span>
                <span className="score-scale">/ 10</span>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Ratings & Content Guide                                             */
/* ------------------------------------------------------------------ */

function AniScores({ scores, contentGuide }) {
  const shk = scores?.shikimori || {}
  const al = scores?.anilist || {}
  const avg = scores?.average

  const shkStats = shk.rates_statuses_stats || []
  const alDist = al.score_distribution || []
  const rankings = al.rankings || []

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Рейтинги и статистика</span>
        <span className="meta">Сводка AniList + Shikimori</span>
      </div>

      <div className="scores-grid">
        <div className="score-card score-card--total">
          <div className="score-card__label">СВОДНЫЙ РЕЙТИНГ</div>
          <div className="score-card__value">
            <span className="num">{avg ?? '—'}</span>
            <span className="denom">/ 10</span>
          </div>
          <div className="score-card__sub">Рассчитан по базам AniList и Shikimori</div>
        </div>

        <div className="score-card">
          <div className="score-card__label">SHIKIMORI</div>
          <div className="score-card__value">
            <span className="num">{shk.score ?? '—'}</span>
            <span className="denom">/ 10</span>
          </div>
          {shkStats.length ? (
            <div className="status-bars">
              {shkStats.slice(0, 4).map((s) => (
                <div key={s.name} className="status-item">
                  <span className="status-name">{s.name}</span>
                  <span className="status-cnt">{s.value}</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="score-card">
          <div className="score-card__label">ANILIST</div>
          <div className="score-card__value">
            <span className="num">{al.score ? `${al.score}%` : '—'}</span>
          </div>
          <div className="anilist-meta-row">
            {al.popularity ? <span>Популярность: <b>{Number(al.popularity).toLocaleString()}</b></span> : null}
            {al.favourites ? <span>В избранном: <b>{Number(al.favourites).toLocaleString()}</b></span> : null}
          </div>
        </div>
      </div>

      {contentGuide?.warnings?.length ? (
        <div className="sec" style={{ marginTop: 16 }}>
          <div className="sec__label">Гид для зрителя и предупреждения о контенте</div>
          <div className="content-warnings-box">
            <div className="cw-rating-badge">Возраст: <b>{contentGuide.age_rating_ru}</b></div>
            <div className="cw-tags-row">
              {contentGuide.warnings.map((w) => (
                <span key={w} className="cw-pill">⚠️ {w}</span>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      {rankings.length ? (
        <div className="sec" style={{ marginTop: 16 }}>
          <div className="sec__label">Ранги и достижения (AniList)</div>
          <div className="chips">
            {rankings.map((r, i) => (
              <span key={i} className="chip hi">
                #{r.rank} {r.context || r.type} {r.all_time ? 'Всех времён' : r.year || ''}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {alDist.length ? (
        <div className="sec" style={{ marginTop: 16 }}>
          <div className="sec__label">Распределение оценок пользователей (AniList)</div>
          <div className="dist-chart">
            {alDist.map((d) => {
              const maxAmt = Math.max(...alDist.map((x) => x.amount || 1))
              const pct = Math.round(((d.amount || 0) / maxAmt) * 100)
              return (
                <div key={d.score} className="dist-col" title={`${d.score}%: ${d.amount} оценок`}>
                  <div className="dist-bar-wrap">
                    <div className="dist-bar" style={{ height: `${pct}%` }} />
                  </div>
                  <span className="dist-label">{d.score}</span>
                </div>
              )
            })}
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Description & Tags                                                  */
/* ------------------------------------------------------------------ */

function AniDescription({ desc, facts }) {
  const [tab, setTab] = useState('shikimori')

  let currentText = desc?.ru_shikimori || desc?.ru
  if (tab === 'google') currentText = desc?.ru_translated || desc?.ru
  if (tab === 'english') currentText = desc?.en || desc?.ru

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Описание и жанры</span>
        <div className="lang-switcher">
          {desc?.ru_shikimori ? (
            <button
              className={`tab-pill ${tab === 'shikimori' ? 'active' : ''}`}
              onClick={() => setTab('shikimori')}
            >
              🇷🇺 Русский (Shikimori)
            </button>
          ) : null}
          {desc?.ru_translated ? (
            <button
              className={`tab-pill ${tab === 'google' ? 'active' : ''}`}
              onClick={() => setTab('google')}
            >
              🌐 Перевод AniList (Google)
            </button>
          ) : null}
          {desc?.en ? (
            <button
              className={`tab-pill ${tab === 'english' ? 'active' : ''}`}
              onClick={() => setTab('english')}
            >
              🇬🇧 English (AniList)
            </button>
          ) : null}
        </div>
      </div>

      <div className="sec">
        <div className="desc-content">
          {currentText ? (
            currentText.split('\n').filter(Boolean).map((para, i) => (
              <p key={i} className="desc-para">{para}</p>
            ))
          ) : (
            <p className="muted">Описание отсутствует</p>
          )}
        </div>
      </div>

      {facts.genres?.length ? (
        <div className="sec">
          <div className="sec__label">Жанры</div>
          <div className="chips">
            {facts.genres.map((g) => (
              <span key={g} className="chip genre-chip">{g}</span>
            ))}
          </div>
        </div>
      ) : null}

      {facts.tags?.length ? (
        <div className="sec">
          <div className="sec__label">Тематические теги (AniList)</div>
          <div className="chips">
            {facts.tags.map((t) => (
              <span
                key={t.name}
                className={`chip ${t.is_spoiler ? 'chip-spoiler' : ''}`}
                title={`${t.category ? `[${t.category}] ` : ''}${t.description || ''}`}
              >
                {t.name}
                {t.rank ? <span className="tag-rank">{t.rank}%</span> : null}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Voiceover & Russian Dubbing Guide                                   */
/* ------------------------------------------------------------------ */

function AniVoiceover({ voiceover }) {
  const f = voiceover?.fandubbers || []
  const sub = voiceover?.fansubbers || []
  const lic = voiceover?.licensors || []

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Русская озвучка и дистрибуция</span>
        <span className="meta">Shikimori Localization Database</span>
      </div>

      {lic.length ? (
        <div className="sec">
          <div className="sec__label">Официальные лицензиаты и стриминг в РФ / СНГ</div>
          <div className="chips">
            {lic.map((l) => (
              <span key={l} className="chip hi">🎬 {l}</span>
            ))}
          </div>
        </div>
      ) : null}

      {f.length ? (
        <div className="sec">
          <div className="sec__label">Студии озвучки и команды дубляжа ({f.length})</div>
          <div className="fandub-tags-grid">
            {f.map((name) => (
              <div key={name} className="fandub-badge">
                <span className="fandub-icon">🎙️</span>
                <span className="fandub-name">{name}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {sub.length ? (
        <div className="sec">
          <div className="sec__label">Команды русских субтитров ({sub.length})</div>
          <div className="chips">
            {sub.map((s) => (
              <span key={s} className="chip">📝 {s}</span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Episodes List with Fillers & AniList Posters                        */
/* ------------------------------------------------------------------ */

function AniEpisodes({ episodes, fillers }) {
  const items = episodes?.items || []
  const [filter, setFilter] = useState('all')

  if (!items.length) return null

  const filtered = items.filter((ep) => {
    if (filter === 'canon') return ep.filler_type === 'canon' || ep.filler_type === 'anime_canon'
    if (filter === 'filler') return ep.filler_type === 'filler'
    return true
  })

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Список эпизодов и гид по канону</span>
        <div className="lang-switcher">
          <button
            className={`tab-pill ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            Все серии ({items.length})
          </button>
          <button
            className={`tab-pill ${filter === 'canon' ? 'active' : ''}`}
            onClick={() => setFilter('canon')}
          >
            🟢 Только канон
          </button>
          {fillers?.filler_count > 0 ? (
            <button
              className={`tab-pill ${filter === 'filler' ? 'active' : ''}`}
              onClick={() => setFilter('filler')}
            >
              🔴 Филлеры ({fillers.filler_count})
            </button>
          ) : null}
        </div>
      </div>

      {fillers?.note ? (
        <div className="filler-summary-bar">
          <span className="fs-badge">
            {fillers.filler_count === 0 ? '🟢 100% Канон (без филлеров)' : `⚠️ ${fillers.filler_percent}% филлеров`}
          </span>
          <span className="fs-note">{fillers.note}</span>
        </div>
      ) : null}

      <div className="episodes-cards-grid">
        {filtered.map((ep) => (
          <div key={ep.number} className={`ep-card ep-card--${ep.filler_type || 'canon'}`}>
            <div className="ep-poster-wrap">
              {ep.thumbnail ? (
                <img src={ep.thumbnail} alt={ep.title} className="ep-poster-img" loading="lazy" referrerPolicy="no-referrer" />
              ) : (
                <div className="ep-poster-placeholder">📺</div>
              )}
              <span className="ep-num-badge">Серия {ep.number}</span>
              <span className={`ep-filler-badge ep-filler--${ep.filler_type || 'canon'}`}>
                {ep.filler_label || 'Канон'}
              </span>
            </div>
            <div className="ep-card-body">
              <div className="ep-title">{ep.title_ru || ep.title}</div>
              {ep.title_en && ep.title_en !== (ep.title_ru || ep.title) ? (
                <div className="ep-subtitle-en">{ep.title_en}</div>
              ) : null}

              {ep.timestamps ? (
                <div className="ep-timestamps-row">
                  {ep.timestamps.op ? (
                    <span
                      className="ep-ts-pill ep-ts--op"
                      title={`Опенинг (OP): ${ep.timestamps.op.start_s}с (${ep.timestamps.op.start_fmt}) – ${ep.timestamps.op.end_s}с (${ep.timestamps.op.end_fmt}). Длительность: ${ep.timestamps.op.duration_s}с [AniSkip]`}
                    >
                      ⏩ OP: {ep.timestamps.op.start_fmt}–{ep.timestamps.op.end_fmt}
                    </span>
                  ) : (
                    <span className="ep-ts-pill ep-ts--noop" title="В этом эпизоде опенинг отсутствует">
                      🚫 Без OP
                    </span>
                  )}
                  {ep.timestamps.ed ? (
                    <span
                      className="ep-ts-pill ep-ts--ed"
                      title={`Эндинг (ED): ${ep.timestamps.ed.start_s}с (${ep.timestamps.ed.start_fmt}) – ${ep.timestamps.ed.end_s}с (${ep.timestamps.ed.end_fmt}). Длительность: ${ep.timestamps.ed.duration_s}с [AniSkip]`}
                    >
                      ⏩ ED: {ep.timestamps.ed.start_fmt}–{ep.timestamps.ed.end_fmt}
                    </span>
                  ) : null}
                  {ep.timestamps.recap ? (
                    <span
                      className="ep-ts-pill ep-ts--recap"
                      title={`Рекап: ${ep.timestamps.recap.start_s}с (${ep.timestamps.recap.start_fmt}) – ${ep.timestamps.recap.end_s}с (${ep.timestamps.recap.end_fmt})`}
                    >
                      ⏩ Рекап: {ep.timestamps.recap.start_fmt}–{ep.timestamps.recap.end_fmt}
                    </span>
                  ) : null}
                </div>
              ) : null}

              {ep.url ? (
                <a href={ep.url} target="_blank" rel="noreferrer" className="ep-watch-link">
                  ▶ Смотреть на {ep.site || 'Crunchyroll'} ↗
                </a>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Sakuga & Key Animation Highlights (Sakugabooru)                     */
/* ------------------------------------------------------------------ */

function AniSakuga({ sakuga, onPlayClip }) {
  if (!sakuga?.length) return null

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Сакуга · Шедевры ключевой анимации</span>
        <span className="meta">Sakugabooru.com ({sakuga.length} клипов)</span>
      </div>

      <div className="sakuga-grid">
        {sakuga.map((clip) => (
          <div
            key={clip.id}
            className="sakuga-card"
            onClick={() => onPlayClip(clip)}
          >
            <div className="sakuga-video-thumb">
              {clip.file_url ? (
                <video
                  src={clip.file_url}
                  muted
                  loop
                  onMouseOver={(e) => e.target.play().catch(() => {})}
                  onMouseOut={(e) => e.target.pause()}
                  className="sakuga-preview-video"
                />
              ) : (
                <img src={clip.preview_url} alt="Сакуга" className="sakuga-preview-img" referrerPolicy="no-referrer" />
              )}
              <div className="sakuga-play-btn">▶ Клик для просмотра</div>
            </div>
            <div className="sakuga-info">
              <div className="sakuga-animators">
                {clip.animators?.length ? `Художники: ${clip.animators.join(', ')}` : 'Выдающаяся экшен-анимация'}
              </div>
              {clip.source ? <div className="sakuga-source">{clip.source}</div> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Visuals Vault: All Posters, Covers, Banners, Stills & Videos       */
/* ------------------------------------------------------------------ */

function AniVisualsVault({ posters, banners, gallery, promos, onOpenImage, onOpenVideo }) {
  const [tab, setTab] = useState('all')

  const posterItems = (posters || []).map((p) => ({
    url: p.url,
    title: p.title || 'Официальный постер / обложка',
    source: p.source || 'Постер',
    type: 'poster',
    aspect: 'portrait',
  }))

  const bannerItems = (banners || []).map((b) => ({
    url: b.url,
    title: b.title || 'Широкоформатный арт-баннер',
    source: b.source || 'Баннер',
    type: 'banner',
    aspect: 'landscape',
  }))

  const screenshotItems = (gallery?.screenshots || []).map((s, idx) => ({
    url: s.original || s.preview,
    preview: s.preview || s.original,
    title: `Официальный кадр #${idx + 1}`,
    source: s.source || 'Shikimori',
    type: 'screenshot',
    aspect: 'landscape',
  }))

  const episodeStillItems = (gallery?.episode_stills || []).map((e, idx) => ({
    url: e.original,
    preview: e.preview || e.original,
    title: e.title || `Кадр эпизода #${idx + 1}`,
    source: e.source || 'Crunchyroll',
    type: 'episode_still',
    aspect: 'landscape',
  }))

  const allImages = [...posterItems, ...bannerItems, ...screenshotItems, ...episodeStillItems]

  if (!allImages.length && !promos?.length) return null

  const filteredImages = allImages.filter((img) => {
    if (tab === 'posters') return img.type === 'poster'
    if (tab === 'banners') return img.type === 'banner'
    if (tab === 'screenshots') return img.type === 'screenshot'
    if (tab === 'episodes') return img.type === 'episode_still'
    return true
  })

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Постеры, Баннеры и Арт-галерея</span>
        <div className="lang-switcher">
          <button
            className={`tab-pill ${tab === 'all' ? 'active' : ''}`}
            onClick={() => setTab('all')}
          >
            Все материалы ({allImages.length})
          </button>
          {posterItems.length ? (
            <button
              className={`tab-pill ${tab === 'posters' ? 'active' : ''}`}
              onClick={() => setTab('posters')}
            >
              🖼️ Постеры ({posterItems.length})
            </button>
          ) : null}
          {bannerItems.length ? (
            <button
              className={`tab-pill ${tab === 'banners' ? 'active' : ''}`}
              onClick={() => setTab('banners')}
            >
              🌄 Баннеры ({bannerItems.length})
            </button>
          ) : null}
          {screenshotItems.length ? (
            <button
              className={`tab-pill ${tab === 'screenshots' ? 'active' : ''}`}
              onClick={() => setTab('screenshots')}
            >
              📸 Кадры ({screenshotItems.length})
            </button>
          ) : null}
          {episodeStillItems.length ? (
            <button
              className={`tab-pill ${tab === 'episodes' ? 'active' : ''}`}
              onClick={() => setTab('episodes')}
            >
              🎬 Стиллы ({episodeStillItems.length})
            </button>
          ) : null}
          <button
            className={`tab-pill ${tab === 'matrix' ? 'active' : ''}`}
            onClick={() => setTab('matrix')}
          >
            📋 Таблица разрешений ({allImages.length})
          </button>
          {promos?.length ? (
            <button
              className={`tab-pill ${tab === 'promos' ? 'active' : ''}`}
              onClick={() => setTab('promos')}
            >
              🎥 Трейлеры ({promos.length})
            </button>
          ) : null}
        </div>
      </div>

      {tab === 'matrix' ? (
        <div className="sec">
          <div className="sec__label">Сводная таблица разрешений и прямых ссылок на оригиналы</div>
          <div className="sec__body">
            <MiniTable
              headers={['Превью', 'Материал', 'Источник', 'Доступные разрешения и ссылки']}
              rows={allImages.map((img, i) => [
                <img
                  key={i}
                  src={img.preview || img.url}
                  alt=""
                  style={{ width: 36, height: 50, objectFit: 'cover', border: '1px solid var(--line-soft)', cursor: 'pointer' }}
                  onClick={() => onOpenImage(img)}
                />,
                <div key={i} style={{ fontWeight: 600, color: 'var(--paper)', fontSize: 12 }}>
                  {img.title}
                </div>,
                <span key={i} className="chip">{img.source}</span>,
                <div key={i} className="matrix-res-links">
                  {img.resolutions && Object.keys(img.resolutions).length ? (
                    Object.entries(img.resolutions).map(([rK, rU]) => (
                      <a
                        key={rK}
                        href={rU}
                        target="_blank"
                        rel="noreferrer"
                        className="matrix-res-btn"
                        title={rU}
                      >
                        ⬇ {rK} ↗
                      </a>
                    ))
                  ) : (
                    <a href={img.url} target="_blank" rel="noreferrer" className="matrix-res-btn">
                      ⬇ Оригинал ↗
                    </a>
                  )}
                </div>,
              ])}
            />
          </div>
        </div>
      ) : tab === 'promos' && promos?.length ? (
        <div className="promos-grid">
          {promos.map((v, i) => (
            <div key={i} className="promo-card" onClick={() => onOpenVideo(v)}>
              <div className="promo-thumb">
                {v.thumbnail ? <img src={v.thumbnail} alt={v.title} loading="lazy" referrerPolicy="no-referrer" /> : null}
                <div className="play-button-overlay">▶</div>
              </div>
              <div className="promo-title">{v.title}</div>
              <div className="promo-meta">{v.hosting || 'Видео'}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="vault-masonry-grid">
          {filteredImages.map((img, i) => (
            <div
              key={i}
              className={`vault-card vault-card--${img.aspect}`}
            >
              <div className="vault-img-wrap" onClick={() => onOpenImage(img)}>
                <img
                  src={img.preview || img.url}
                  alt={img.title}
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  className="vault-img"
                />
                <span className="vault-badge">{img.source}</span>
                <div className="vault-hover-mask">
                  <span className="vault-hover-title">{img.title}</span>
                  <span className="vault-hover-cta">🔍 Просмотр в Lightbox</span>
                </div>
              </div>

              {img.resolutions && Object.keys(img.resolutions).length > 1 ? (
                <div className="vault-card-res-bar">
                  {Object.entries(img.resolutions).map(([rKey, rUrl]) => (
                    <button
                      key={rKey}
                      type="button"
                      className="vault-res-chip"
                      onClick={(e) => {
                        e.stopPropagation()
                        onOpenImage({
                          ...img,
                          url: rUrl,
                          title: `${img.title} [${rKey}]`,
                        })
                      }}
                      title={`Разрешение: ${rKey}`}
                    >
                      {rKey.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Themes & OST Discography                                            */
/* ------------------------------------------------------------------ */

function AniThemes({ themes, discography }) {
  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Музыка · Опенинги, Эндинги и OST</span>
        <span className="meta">AnimeThemes + Официальная дискография</span>
      </div>

      {discography ? (
        <div className="sec">
          <div className="ost-discography-card">
            <div className="ost-header">
              <span className="ost-label">ОФИЦИАЛЬНЫЙ САУНДТРЕК (OST)</span>
              <span className="ost-composers">Композиторы: <b>{discography.composers?.join(', ')}</b></span>
            </div>
            <p className="ost-desc">{discography.description}</p>
            {discography.albums?.length ? (
              <div className="ost-albums-grid">
                {discography.albums.map((alb, i) => (
                  <div key={i} className="ost-album-pill">
                    <span className="alb-title">💿 {alb.title}</span>
                    <span className="alb-meta">{alb.year} г. · {alb.tracks_count} треков ({alb.label})</span>
                  </div>
                ))}
              </div>
            ) : null}
            {discography.spotify_album_url ? (
              <div style={{ marginTop: 12 }}>
                <a
                  href={discography.spotify_album_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-read"
                  style={{ background: '#1db954', color: '#000', fontWeight: 700 }}
                >
                  🟢 Слушать полный OST на Spotify ↗
                </a>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      {themes?.length ? (
        <div className="sec">
          <div className="sec__label">Опенинги и Эндинги (AnimeThemes)</div>
          <div className="themes-list">
            {themes.map((th, i) => {
              const typeLabel = THEME_RU[th.type] || th.type
              const firstEntry = th.entries?.[0]
              const firstVideo = firstEntry?.videos?.[0]
              const audioUrl = firstVideo?.audio

              return (
                <div key={i} className="theme-track-item">
                  <div className="theme-header">
                    <span className={`theme-type-tag theme-type--${th.type}`}>
                      {typeLabel} {th.sequence ? `#${th.sequence}` : ''}
                    </span>
                    <span className="theme-song-title">{th.song || 'Без названия'}</span>
                    {th.artists?.length ? (
                      <span className="theme-artists">· {th.artists.join(', ')}</span>
                    ) : null}
                    {firstEntry?.episodes ? (
                      <span className="theme-episodes">эп. {firstEntry.episodes}</span>
                    ) : null}
                  </div>

                  {audioUrl ? (
                    <div className="theme-player-wrap">
                      <audio controls preload="none" src={audioUrl} className="custom-audio-player">
                        Ваш браузер не поддерживает аудио.
                      </audio>
                    </div>
                  ) : null}

                  {firstEntry?.videos?.length ? (
                    <div className="theme-video-links">
                      <span className="meta-label">Видеоклипы:</span>
                      {firstEntry.videos.map((v, vIdx) => (
                        <a
                          key={vIdx}
                          href={v.link}
                          target="_blank"
                          rel="noreferrer"
                          className="video-clip-btn"
                        >
                          📺 {v.resolution ? `${v.resolution}p` : 'Видео'} {v.nc ? 'Creditless (NC)' : ''} ↗
                        </a>
                      ))}
                    </div>
                  ) : null}
                </div>
              )
            })}
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Characters & Voice Actors                                           */
/* ------------------------------------------------------------------ */

function AniCharacters({ characters }) {
  const [filter, setFilter] = useState('all')

  if (!characters?.length) return null

  const filtered = characters.filter((c) => {
    if (filter === 'main') return c.role === 'главный'
    if (filter === 'supporting') return c.role === 'второстепенный'
    return true
  })

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Персонажи и Сэйю</span>
        <div className="lang-switcher">
          <button
            className={`tab-pill ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            Все ({characters.length})
          </button>
          <button
            className={`tab-pill ${filter === 'main' ? 'active' : ''}`}
            onClick={() => setFilter('main')}
          >
            Главные
          </button>
          <button
            className={`tab-pill ${filter === 'supporting' ? 'active' : ''}`}
            onClick={() => setFilter('supporting')}
          >
            Второстепенные
          </button>
        </div>
      </div>

      <div className="characters-grid">
        {filtered.map((c, i) => {
          const names = c.names || {}
          const ruName = names.ru || names.en
          const jaName = names.ja
          const enName = names.en
          const va = c.voice_actors?.[0]

          return (
            <div key={i} className="character-card">
              <div className="char-portrait">
                {c.image ? (
                  <img src={c.image} alt={ruName} loading="lazy" referrerPolicy="no-referrer" />
                ) : (
                  <div className="char-placeholder">👤</div>
                )}
                {c.role ? (
                  <span className={`char-role-badge char-role--${c.role}`}>
                    {c.role}
                  </span>
                ) : null}
              </div>

              <div className="char-details">
                <div className="char-ru-name">{ruName}</div>
                {enName && enName !== ruName ? <div className="char-en-name">{enName}</div> : null}
                {jaName ? <div className="char-ja-name">{jaName}</div> : null}

                {va ? (
                  <div className="char-va-block">
                    <div className="va-label">Японский сэйю:</div>
                    <div className="va-info">
                      {va.image ? (
                        <img src={va.image} alt={va.name_ru || va.name} className="va-avatar" referrerPolicy="no-referrer" />
                      ) : null}
                      <div className="va-names-col">
                        <span className="va-name">{va.name_ru || va.name}</span>
                        {va.name && va.name !== va.name_ru ? <span className="va-subname">{va.name} {va.native ? `(${va.native})` : ''}</span> : null}
                      </div>
                    </div>

                    {va.notable_roles?.length ? (
                      <div className="va-notable-roles">
                        <span className="va-roles-label">Другие культовые роли:</span>
                        <div className="va-roles-chips">
                          {va.notable_roles.map((nr, nrIdx) => (
                            <span key={nrIdx} className="va-role-chip" title={`${nr.character} в «${nr.anime}»`}>
                              {nr.icon} <b>{nr.character}</b> ({nr.anime})
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Staff & Creators                                                   */
/* ------------------------------------------------------------------ */

function AniStaff({ staff }) {
  if (!staff?.length) return null

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Создатели и Авторы</span>
        <span className="meta">{staff.length} человек</span>
      </div>

      <div className="staff-grid">
        {staff.slice(0, 16).map((s, i) => (
          <div key={i} className="staff-card">
            {s.image ? (
              <img src={s.image} alt={s.ru || s.name} className="staff-avatar" loading="lazy" referrerPolicy="no-referrer" />
            ) : (
              <div className="staff-avatar staff-avatar--placeholder">👤</div>
            )}
            <div className="staff-info">
              <div className="staff-name">{s.ru || s.name}</div>
              {s.native ? <div className="staff-native">{s.native}</div> : null}
              <div className="staff-roles">
                {s.roles?.join(' · ') || 'Создатель'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Manga Adaptation & Episode Mapping Section                         */
/* ------------------------------------------------------------------ */

function expand_episode_rows(rows, chunk = 2) {
  const out = []
  for (const row of rows || []) {
    const epMatch = (row.eps || '').match(/(\d+)\s*[–—\-]\s*(\d+)/) || (row.eps || '').match(/\b(\d+)\b/)
    const chMatch = (row.chapters || '').match(/(\d+)\s*[–—\-]\s*(\d+)/) || (row.chapters || '').match(/\b(\d+)\b/)
    if (!epMatch || !chMatch) {
      if (row.eps && row.chapters) {
        out.push({ eps: row.eps, chapters: row.chapters, note: row.note })
      }
      continue
    }
    const e1 = parseInt(epMatch[1], 10)
    const e2 = parseInt(epMatch[2] || epMatch[1], 10)
    const c1 = parseInt(chMatch[1], 10)
    const c2 = parseInt(chMatch[2] || chMatch[1], 10)

    const volMatch = (row.chapters || '').match(/том[а-я]*\s*([0-9–—\-]+)/i)
    const volSuffix = volMatch ? ` (том ${volMatch[1]})` : ''

    if (e2 === e1) {
      const chStr = c2 !== c1 ? `${c1}–${c2}` : `${c1}`
      out.push({
        eps: `${e1} серия`,
        ep_num: e1,
        chapters: `${chStr} глав${volSuffix}`,
        note: row.note,
      })
      continue
    }

    const per = (c2 - c1 + 1) / (e2 - e1 + 1)
    let cur = e1
    while (cur <= e2) {
      const last = Math.min(e2, cur + chunk - 1)
      let cFrom = c1 + Math.floor((cur - e1) * per)
      let cTo = c1 + Math.floor((last - e1 + 1) * per) - 1
      if (cTo < cFrom) cTo = cFrom

      const epsLabel = last === cur ? `${cur} серия` : `${cur}–${last} серии`
      const chLabel = cTo === cFrom ? `${cFrom} глава${volSuffix}` : `${cFrom}–${cTo} глав${volSuffix}`

      out.push({
        eps: epsLabel,
        ep_num: cur,
        chapters: chLabel,
        note: row.note,
      })
      cur = last + 1
    }
  }
  return out
}

function AniManga({ manga, mangaMap }) {
  const map = mangaMap || manga?.map || {}
  const rawSources = manga?.sources || manga?.parts || {}
  const ca = map.continue_after
  const [mangaTab, setMangaTab] = useState('episodes') // 'episodes' | 'arcs' | 'volumes'

  // Normalize manga sources whether passed as boolean, part objects, or unified objects
  const md = typeof rawSources.mangadex === 'object' && rawSources.mangadex !== null ? rawSources.mangadex : null
  const al = typeof rawSources.anilist === 'object' && rawSources.anilist !== null ? rawSources.anilist : null
  const shk = typeof rawSources.shikimori === 'object' && rawSources.shikimori !== null ? rawSources.shikimori : null

  const episodesList = map.episodes?.length ? map.episodes : (map.rows?.length ? expand_episode_rows(map.rows) : [])
  const hasAnyManga = Boolean(md || al || shk || map.rows?.length || episodesList.length || map.note)
  if (!hasAnyManga) return null

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Манга-первоисточник · Соответствие серий и глав</span>
        <div className="lang-switcher">
          {episodesList.length ? (
            <button
              type="button"
              className={`tab-pill ${mangaTab === 'episodes' ? 'active' : ''}`}
              onClick={() => setMangaTab('episodes')}
            >
              📋 Посерийно (1 серия = N глав)
            </button>
          ) : null}
          {map.rows?.length ? (
            <button
              type="button"
              className={`tab-pill ${mangaTab === 'arcs' ? 'active' : ''}`}
              onClick={() => setMangaTab('arcs')}
            >
              🗺️ Сюжетные арки
            </button>
          ) : null}
          {md?.volumes_en?.length ? (
            <button
              type="button"
              className={`tab-pill ${mangaTab === 'volumes' ? 'active' : ''}`}
              onClick={() => setMangaTab('volumes')}
            >
              📚 Тома MangaDex ({md.volumes_en.length})
            </button>
          ) : null}
        </div>
      </div>

      {map.note ? (
        <div className="sec">
          <div className="sec__label">Связь аниме и первоисточника</div>
          <div className="sec__body">
            <p className="manga-note-text">{map.note}</p>
          </div>
        </div>
      ) : null}

      {ca ? (
        <div className="sec">
          <div className="continue-reading-banner">
            <div className="cr-icon">📖</div>
            <div className="cr-content">
              <div className="cr-title">С какой главы читать мангу после аниме?</div>
              <div className="cr-desc">
                После завершения <b>{ca.episode ? `${ca.episode} серии` : 'аниме'}</b> сюжет продолжается с <b>главы {ca.chapter}</b>
                {ca.volume ? ` (том ${ca.volume})` : ''}.
              </div>
              <p style={{ marginTop: 4, fontSize: 12.5, color: 'var(--dim)' }}>{ca.note}</p>
              {md && ca.chapter ? (
                <a
                  href={chLink(md, ca.chapter) || md.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-read"
                  style={{ marginTop: 10, display: 'inline-block' }}
                >
                  Читать главу {ca.chapter} на MangaDex ↗
                </a>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}

      {/* 1. Granular Episode Table (1 серия -> 1-2 главы) */}
      {mangaTab === 'episodes' && episodesList.length ? (
        <div className="sec">
          <div className="sec__label">Посерийная сверка: какая серия какой главе и тому соответствует</div>
          <div className="sec__body">
            <div className="manga-episodes-table-wrap">
              <table className="manga-episodes-table">
                <thead>
                  <tr>
                    <th style={{ width: '15%' }}>Серия аниме</th>
                    <th style={{ width: '30%' }}>Главы и том манги</th>
                    <th>Сюжет / Описание арки</th>
                    <th style={{ width: '22%', textAlign: 'right' }}>Чтение</th>
                  </tr>
                </thead>
                <tbody>
                  {episodesList.map((e, idx) => {
                    const firstCh = (e.chapters || '').match(/\b\d+\b/)?.[0]
                    const link = md && firstCh ? (chLink(md, firstCh) || md.url) : md?.url
                    return (
                      <tr key={idx} className="manga-ep-row">
                        <td className="manga-ep-cell">
                          <span className="manga-ep-badge">📺 {e.eps?.includes('сери') ? e.eps : `${e.eps} серия`}</span>
                        </td>
                        <td className="manga-ch-cell">
                          <span className="manga-ch-badge">📖 {e.chapters}</span>
                        </td>
                        <td className="manga-note-cell">{e.note || 'Адаптация первоисточника'}</td>
                        <td className="manga-act-cell" style={{ textAlign: 'right' }}>
                          {link ? (
                            <a href={link} target="_blank" rel="noreferrer" className="btn-read-sm">
                              {firstCh ? `Глава ${firstCh} ↗` : 'MangaDex ↗'}
                            </a>
                          ) : (
                            <span style={{ color: 'var(--faint)' }}>—</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}

      {/* 2. Arcs Timeline */}
      {mangaTab === 'arcs' && map.rows?.length ? (
        <div className="sec">
          <div className="sec__label">Экранизация по сюжетным аркам</div>
          <div className="manga-arcs-timeline">
            {map.rows.map((r, i) => (
              <div key={i} className="manga-arc-card">
                <div className="manga-arc-badges">
                  <span className="arc-badge-ep">📺 {r.eps?.startsWith('Том') ? r.eps : (r.eps?.includes('сери') ? r.eps : `Серии ${r.eps}`)}</span>
                  <span className="arc-arrow">➔</span>
                  <span className="arc-badge-ch">📖 {r.chapters?.includes('глав') ? r.chapters : `Главы ${r.chapters}`}</span>
                </div>
                <div className="manga-arc-note">{r.note || '—'}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* 3. MangaDex Volumes & Chapters */}
      {mangaTab === 'volumes' && md?.volumes_en?.length ? (
        <div className="sec">
          <div className="sec__label">Оригинальные тома и главы на MangaDex</div>
          <div className="manga-volumes-grid">
            {md.volumes_en.map((vol, vIdx) => (
              <div key={vIdx} className="manga-volume-card">
                <div className="volume-card-head">
                  <b>{vol.volume && vol.volume !== 'none' ? `Том ${vol.volume}` : 'Сборник глав'}</b>
                  <span className="meta">{vol.count || vol.chapters?.length || 0} глав</span>
                </div>
                <div className="volume-chapters-chips">
                  {(vol.chapters || []).slice(0, 16).map((c, cIdx) => (
                    <a
                      key={cIdx}
                      href={c.id ? `https://mangadex.org/chapter/${c.id}` : md.url}
                      target="_blank"
                      rel="noreferrer"
                      className="manga-ch-chip"
                      title={`Читать главу ${c.n}`}
                    >
                      гл. {c.n}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Manga sources cards */}
      <div className="sec">
        <div className="sec__label">Издания первоисточника в базах данных</div>
        <div className="manga-cards-row">
          {shk ? (
            <div className="manga-src-card">
              {shk.cover ? <img src={shk.cover} alt={shk.title_ru} className="manga-card-cov" referrerPolicy="no-referrer" /> : null}
              <div className="manga-card-info">
                <b>Shikimori Manga</b>
                <div className="manga-card-title">{shk.title_ru || shk.title}</div>
                <div className="manga-card-meta">
                  Томов: {shk.volumes ?? '?'} · Глав: {shk.chapters ?? '?'} · {shk.status || ''} · Оценка: ★ {shk.score || '—'}
                </div>
                {shk.url ? <a href={shk.url} target="_blank" rel="noreferrer" className="lnk">Страница на Shikimori ↗</a> : null}
              </div>
            </div>
          ) : null}

          {al ? (
            <div className="manga-src-card">
              {al.cover ? <img src={al.cover} alt={al.title} className="manga-card-cov" referrerPolicy="no-referrer" /> : null}
              <div className="manga-card-info">
                <b>AniList Manga</b>
                <div className="manga-card-title">{al.title}</div>
                <div className="manga-card-meta">
                  Томов: {al.volumes ?? '?'} · Глав: {al.chapters ?? '?'} · Рейтинг: {al.score ? `${al.score}%` : '—'}
                </div>
                {al.url ? <a href={al.url} target="_blank" rel="noreferrer" className="lnk">Страница на AniList ↗</a> : null}
              </div>
            </div>
          ) : null}

          {md ? (
            <div className="manga-src-card">
              {md.cover ? <img src={md.cover} alt="MangaDex" className="manga-card-cov" referrerPolicy="no-referrer" /> : null}
              <div className="manga-card-info">
                <b>MangaDex (Главы и перевод)</b>
                <div className="manga-card-title">Каталог глав на MangaDex</div>
                <div className="manga-card-meta">
                  {md.chapters_en ? `${md.chapters_en} глав доступно в каталоге` : 'Каталог глав'}
                </div>
                {md.url ? <a href={md.url} target="_blank" rel="noreferrer" className="btn-read" style={{ marginTop: 6, display: 'inline-block' }}>Читать мангу на MangaDex ↗</a> : null}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Franchise Section (EXCLUSIVELY from Shikimori)                     */
/* ------------------------------------------------------------------ */

function AniFranchise({ franchise }) {
  const nodes = franchise?.nodes || []
  const related = franchise?.related || []
  const [sortOrder, setSortOrder] = useState('chrono')

  if (!nodes.length && !related.length) return null

  const sortedNodes = [...nodes].sort((a, b) => {
    if (sortOrder === 'chrono') return (a.year || 9999) - (b.year || 9999) || (a.date || 0) - (b.date || 0)
    return (b.year || 0) - (a.year || 0) || (b.date || 0) - (a.date || 0)
  })

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Франшиза и Связанные тайтлы</span>
        <div className="lang-switcher">
          <button
            className={`tab-pill ${sortOrder === 'chrono' ? 'active' : ''}`}
            onClick={() => setSortOrder('chrono')}
          >
            ⏳ Хронологический порядок
          </button>
          <button
            className={`tab-pill ${sortOrder === 'release' ? 'active' : ''}`}
            onClick={() => setSortOrder('release')}
          >
            📅 По дате выхода
          </button>
        </div>
      </div>

      {nodes.length > 1 ? (
        <div className="sec">
          <div className="sec__label">Хронология франшизы ({nodes.length} тайтлов)</div>
          <div className="franchise-timeline-grid">
            {sortedNodes.map((n) => (
              <div
                key={n.id}
                className={`franchise-node-card ${n.is_current ? 'franchise-node--current' : ''}`}
              >
                {n.image ? (
                  <img src={n.image} alt={n.name} className="franchise-node-cov" loading="lazy" referrerPolicy="no-referrer" />
                ) : (
                  <div className="franchise-node-cov franchise-node-cov--placeholder">🎬</div>
                )}
                <div className="franchise-node-info">
                  {n.is_current ? (
                    <span className="current-title-badge">★ Текущий тайтл</span>
                  ) : null}
                  <div className="franchise-node-title">{n.name}</div>
                  <div className="franchise-node-meta">
                    {n.year ? `${n.year} г.` : ''} {n.kind ? `· ${n.kind}` : ''}
                  </div>
                  {n.url ? (
                    <a href={n.url} target="_blank" rel="noreferrer" className="lnk" style={{ fontSize: 11 }}>
                      Shikimori ↗
                    </a>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {related.length ? (
        <div className="sec">
          <div className="sec__label">Прямые связи произведения (Shikimori)</div>
          <div className="related-grid">
            {related.map((r, i) => (
              <div key={i} className="related-card">
                {r.image ? (
                  <img src={r.image} alt={r.title} className="related-cov" loading="lazy" referrerPolicy="no-referrer" />
                ) : (
                  <div className="related-cov related-cov--placeholder">🎬</div>
                )}
                <div className="related-info">
                  <span className="related-rel-tag">{r.relation}</span>
                  <div className="related-title">{r.title}</div>
                  <div className="related-format">
                    {r.kind || r.format} {r.score ? `· ★ ${r.score}` : ''}
                  </div>
                  {r.url ? (
                    <a href={r.url} target="_blank" rel="noreferrer" className="lnk" style={{ fontSize: 11 }}>
                      Перейти на Shikimori ↗
                    </a>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* External Links                                                      */
/* ------------------------------------------------------------------ */

function AniExternal({ external }) {
  if (!external?.length) return null

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Официальные ресурсы и базы данных</span>
      </div>

      <div className="sec">
        <div className="external-links-grid">
          {external.map((l, i) => (
            <a
              key={i}
              href={l.url}
              target="_blank"
              rel="noreferrer"
              className="ext-link-card"
              style={l.color ? { borderColor: l.color } : {}}
            >
              <span className="ext-link-icon">{l.icon || '🔗'}</span>
              <span className="ext-link-site">{l.site || 'Ссылка'}</span>
              <span className="ext-link-kind">({l.kind || 'official'}) ↗</span>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* All Title Variants                                                  */
/* ------------------------------------------------------------------ */

function AniNames({ titles }) {
  const all = titles?.all || []
  if (!all.length) return null

  return (
    <div className="panel">
      <div className="panel__head">
        <span className="panel__name">Все варианты названий</span>
        <span className="meta">{all.length} записей</span>
      </div>
      <div className="sec">
        <div className="sec__body">
          <MiniTable
            headers={['Язык', 'Название', 'Источник']}
            rows={all.map((n, i) => [
              langBadge(n.lang),
              n.name,
              <span key={i} style={{ color: 'var(--faint)', fontSize: 11 }}>
                {n.from}
              </span>,
            ])}
          />
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Lightbox Modal with Interactive Resolution Switcher                */
/* ------------------------------------------------------------------ */

function LightboxModal({ item, onClose }) {
  const [selectedResUrl, setSelectedResUrl] = useState(null)

  useEffect(() => {
    setSelectedResUrl(null)
  }, [item])

  if (!item) return null

  const resolutions = item.resolutions || {}
  const resEntries = Object.entries(resolutions)
  const currentUrl = selectedResUrl || item.url

  const labels = {
    extra_large: 'Ultra HD (1000px)',
    large: 'High-Res (500px)',
    medium: 'Medium (250px)',
    original: 'Оригинал (Max)',
    preview: 'Превью (320px)',
    large_512: '512px',
    thumb_256: '256px',
    x96: '96px',
    x48: '48px',
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content lightbox-modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="lightbox-header-info">
            <span className="lightbox-type-badge">{item.source || 'Изображение'}</span>
            <span className="lightbox-title-text">{item.title}</span>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {resEntries.length > 1 ? (
          <div className="lightbox-res-bar">
            <span className="res-bar-label">Доступные разрешения:</span>
            <div className="res-pill-row">
              {resEntries.map(([resKey, resUrl]) => {
                const isCur = currentUrl === resUrl
                return (
                  <button
                    key={resKey}
                    type="button"
                    className={`res-pill-btn ${isCur ? 'active' : ''}`}
                    onClick={() => setSelectedResUrl(resUrl)}
                  >
                    {labels[resKey] || resKey}
                  </button>
                )
              })}
            </div>
          </div>
        ) : null}

        <div className="lightbox-image-wrap">
          <img src={currentUrl} alt={item.title} className="modal-img" referrerPolicy="no-referrer" />
        </div>

        <div className="lightbox-footer">
          <div className="lightbox-footer-info">
            <span className="res-active-badge">
              Разрешение: {Object.keys(resolutions).find(k => resolutions[k] === currentUrl) || 'оригинал'}
            </span>
          </div>
          <a href={currentUrl} target="_blank" rel="noreferrer" className="btn-read" style={{ fontSize: 11 }}>
            Открыть в исходном разрешении ↗
          </a>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Airing Schedule & Live Broadcast Engine                            */
/* ------------------------------------------------------------------ */

function AniAiringCard({ airing }) {
  if (!airing) return null
  const next = airing.next_episode

  return (
    <div className="panel airing-schedule-panel">
      <div className="airing-banner-content">
        <div className="airing-main-col">
          <div className="airing-status-tag">
            <span className="pulse-dot on" />
            <span>ОНГОИНГ · РАСПИСАНИЕ ЭФИРА</span>
          </div>
          {next ? (
            <div className="airing-countdown-box">
              <div className="airing-ep-target">
                Следующая <b>Серия {next.episode}</b> выйдет через:
              </div>
              <div className="airing-timer-digits">
                ⏳ {next.countdown_text}
              </div>
              <div className="airing-date-sub">
                Дата эфира: <b>{next.airing_at_formatted}</b> (Япония / МСК)
              </div>
            </div>
          ) : (
            <div className="airing-countdown-box">
              <div className="airing-ep-target">Тайтл находится в активной трансляции</div>
            </div>
          )}
        </div>

        <div className="airing-side-col">
          <div className="airing-net-info">
            <span className="meta-label">ТВ-вещание в Японии:</span>
            <span className="airing-net-val">📡 {airing.broadcast_networks || 'Tokyo MX, BS11, AT-X'}</span>
          </div>
          <div className="airing-streams-wrap">
            <span className="meta-label">Стриминговые сервисы:</span>
            <div className="airing-streams-grid">
              {(airing.simulcast_services || []).map((srv, idx) => (
                <div key={idx} className="airing-srv-chip">
                  <span>{srv.icon}</span>
                  <span className="srv-name">{srv.name}</span>
                  <span className="srv-type">({srv.type})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Review Highlights & Verdict ("Кому понравится")                    */
/* ------------------------------------------------------------------ */

function AniVerdictBox({ verdict }) {
  if (!verdict) return null

  return (
    <div className="panel verdict-panel">
      <div className="panel__head">
        <span className="panel__name">💡 Экспресс-вердикт и Резюме критиков</span>
        <span className="verdict-score-badge">{verdict.score_verdict}</span>
      </div>

      <div className="verdict-body">
        <p className="verdict-summary-text">{verdict.summary}</p>

        <div className="verdict-cols-grid">
          <div className="verdict-col verdict-col--pros">
            <div className="v-col-head">🟢 Главные достоинства</div>
            <ul className="v-list">
              {(verdict.pros || []).map((p, idx) => (
                <li key={idx} className="v-item v-item--pro">
                  <span className="v-icon">✓</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="verdict-col verdict-col--cons">
            <div className="v-col-head">⚠️ Особенности и нюансы</div>
            <ul className="v-list">
              {(verdict.cons || []).map((c, idx) => (
                <li key={idx} className="v-item v-item--con">
                  <span className="v-icon">!</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {verdict.audience_match ? (
          <div className="verdict-audience-card">
            <span className="aud-label">🎯 Кому обязательно смотреть:</span>
            <span className="aud-text">{verdict.audience_match}</span>
          </div>
        ) : null}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Awards & Hall of Fame Accolades                                    */
/* ------------------------------------------------------------------ */

function AniAwards({ awards }) {
  if (!awards?.length) return null

  return (
    <div className="panel awards-panel">
      <div className="panel__head">
        <span className="panel__name">🏆 Награды и Исторические достижения</span>
        <span className="meta">{awards.length} наград</span>
      </div>

      <div className="awards-grid">
        {awards.map((aw, idx) => (
          <div key={idx} className="award-card">
            <span className="award-icon">{aw.icon || '🏆'}</span>
            <div className="award-content">
              <div className="award-title">{aw.award} ({aw.year})</div>
              <div className="award-cat">{aw.category}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Interactive Watch Order & Franchise Roadmap                        */
/* ------------------------------------------------------------------ */

function AniWatchOrderTimeline({ watchOrder }) {
  if (!watchOrder) return null

  return (
    <div className="panel watchorder-panel">
      <div className="panel__head">
        <span className="panel__name">🗺️ {watchOrder.title || 'Порядок просмотра франшизы'}</span>
        <span className="meta">Пошаговый путеводитель</span>
      </div>

      <div className="sec">
        {watchOrder.description ? (
          <p className="watchorder-desc-note">{watchOrder.description}</p>
        ) : null}

        <div className="watchorder-timeline">
          {(watchOrder.steps || []).map((step, idx) => (
            <div key={idx} className="wo-step-card">
              <div className="wo-step-num-col">
                <span className="wo-step-num">#{step.step}</span>
                {idx < (watchOrder.steps.length - 1) ? <div className="wo-connector-line" /> : null}
              </div>

              <div className="wo-step-body">
                <div className="wo-step-header">
                  <span className="wo-step-title">{step.title}</span>
                  <span className="wo-step-ep-badge">{step.episodes}</span>
                  <span className={`wo-canon-badge wo-canon--${step.canon_level}`}>
                    {step.canon_label}
                  </span>
                </div>
                {step.note ? <p className="wo-step-note">{step.note}</p> : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/* Curated FAQ Accordion                                               */
/* ------------------------------------------------------------------ */

function AniFAQ({ faq }) {
  const [openItems, setOpenItems] = useState({})
  const [unmaskedSpoilers, setUnmaskedSpoilers] = useState({})
  const [selectedCat, setSelectedCat] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const faqItems = faq || []
  const categories = ['all', ...Array.from(new Set(faqItems.map((item) => item.category).filter(Boolean)))]

  const filtered = faqItems.filter((item) => {
    const matchesCat = selectedCat === 'all' || item.category === selectedCat
    const qLower = searchQuery.toLowerCase().trim()
    const matchesSearch =
      !qLower ||
      item.question.toLowerCase().includes(qLower) ||
      item.answer.toLowerCase().includes(qLower) ||
      (item.category && item.category.toLowerCase().includes(qLower))
    return matchesCat && matchesSearch
  })

  const toggleOpen = (id) => {
    setOpenItems((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const toggleSpoiler = (id, e) => {
    e.stopPropagation()
    setUnmaskedSpoilers((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="panel faq-panel">
      <div className="panel__head">
        <div className="faq-head-left">
          <span className="panel__name">❓ Частые вопросы и Ответы (FAQ)</span>
          <span className="meta">{faqItems.length} проверенных ответов</span>
        </div>
        <div className="faq-search-wrap">
          <input
            type="text"
            className="faq-search-input"
            placeholder="🔍 Поиск по вопросам..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="sec">
        {/* Categories Bar */}
        {categories.length > 2 ? (
          <div className="faq-cat-bar">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`faq-cat-btn ${selectedCat === cat ? 'active' : ''}`}
                onClick={() => setSelectedCat(cat)}
              >
                {cat === 'all' ? `Все (${faqItems.length})` : cat}
              </button>
            ))}
          </div>
        ) : null}

        {/* FAQ Accordion List */}
        <div className="faq-list">
          {filtered.length ? (
            filtered.map((item, idx) => {
              const itemId = item.id || `faq-${idx}`
              const isOpen = openItems[itemId] ?? true
              const isUnmasked = unmaskedSpoilers[itemId]

              return (
                <div key={itemId} className={`faq-item-card ${isOpen ? 'open' : ''}`}>
                  <div className="faq-item-question-row" onClick={() => toggleOpen(itemId)}>
                    <div className="faq-q-left">
                      <span className="faq-q-icon">Q</span>
                      <span className="faq-q-text">{item.question}</span>
                      {item.badge ? (
                        <span className={`faq-badge ${item.is_spoiler ? 'faq-badge--spoiler' : ''}`}>
                          {item.badge}
                        </span>
                      ) : null}
                    </div>
                    <span className="faq-toggle-arrow">{isOpen ? '▲' : '▼'}</span>
                  </div>

                  {isOpen ? (
                    <div className="faq-item-answer-body">
                      <span className="faq-a-icon">A</span>
                      <div className="faq-a-content">
                        {item.is_spoiler && !isUnmasked ? (
                          <div className="faq-spoiler-mask" onClick={(e) => toggleSpoiler(itemId, e)}>
                            <div className="faq-spoiler-blur-text">{item.answer}</div>
                            <button type="button" className="faq-reveal-btn">
                              👁️ Внимание, спойлер! Нажмите, чтобы прочитать
                            </button>
                          </div>
                        ) : (
                          <div className="faq-a-text">
                            {item.answer}
                            {item.is_spoiler ? (
                              <button
                                type="button"
                                className="faq-hide-spoiler-btn"
                                onClick={(e) => toggleSpoiler(itemId, e)}
                              >
                                [Скрыть спойлер]
                              </button>
                            ) : null}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : null}
                </div>
              )
            })
          ) : (
            <div className="faq-empty-state">По вашему запросу ничего не найдено.</div>
          )}
        </div>
      </div>
    </div>
  )
}