import { createElement } from 'react'
import { renderToString } from 'react-dom/server'
import fs from 'node:fs'
import path from 'node:path'
import IndexView from './src/components/IndexView.jsx'
import DetailView from './src/components/DetailView.jsx'
import MangaSection from './src/components/MangaSection.jsx'
import AnimanPanel from './src/components/AnimanPanel.jsx'
import {
  AniListPanel,
  JikanPanel,
  KitsuPanel,
  ShikimoriPanel,
  BangumiPanel,
  AnimePlanetPanel,
  AnimeThemesPanel,
} from './src/components/Panels.jsx'

const PANELS = {
  anilist: AniListPanel,
  jikan_myanimelist: JikanPanel,
  kitsu: KitsuPanel,
  shikimori: ShikimoriPanel,
  bangumi: BangumiPanel,
  anime_planet: AnimePlanetPanel,
  anime_themes: AnimeThemesPanel,
}

const db = JSON.parse(
  fs.readFileSync(path.resolve(process.cwd(), '../data/anime.json'), 'utf-8'),
)
const titles = db.titles
let fails = 0
let rendered = 0

for (const t of titles) {
  try {
    renderToString(createElement(IndexView, { titles: [t] }))
    rendered++
  } catch (e) {
    fails++
    console.error('INDEX FAIL', t.key, '::', e.message)
  }

  for (const [sk, raw] of Object.entries(t.sources)) {
    const Panel = PANELS[sk]
    if (!Panel) continue
    const tag = `${t.key}/${sk}`
    try {
      renderToString(createElement(Panel, { raw }))
      rendered++
    } catch (e) {
      fails++
      console.error('PANEL FAIL', tag, '::', e.message)
    }
  }

  try {
    renderToString(createElement(DetailView, { title: t }))
    rendered++
  } catch (e) {
    fails++
    console.error('DETAIL FAIL', t.key, '::', e.message)
  }

  try {
    renderToString(createElement(MangaSection, { title: t }))
    rendered++
  } catch (e) {
    fails++
    console.error('MANGA FAIL', t.key, '::', e.message)
  }

  try {
    renderToString(createElement(AnimanPanel, { panel: t.sources?.animan || {} }))
    rendered++
  } catch (e) {
    fails++
    console.error('ANIMAN FAIL', t.key, '::', e.message)
  }
}

console.log(`rendered ${rendered} views, ${fails} failures, titles=${titles.length}`)
process.exit(fails ? 1 : 0)