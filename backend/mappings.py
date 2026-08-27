"""Curated and Dynamic Episode -> Manga Chapter Mappings.

Detailed breakdown of which episodes cover which manga chapters and volumes,
where to continue reading after the anime, and adaptation notes.
"""
from __future__ import annotations

import re

MANGAMAPS = {
    "cowboy-bebop": {
        "kind": "manga-of-anime",
        "note": "Аниме-сериал (26 серий) — оригинальный первоисточник. Манга Ютаки Нантэн (3 тома, 11 глав) создана как сопутствующая адаптация и пересказывает ключевые дела охотников за головами с альтернативными деталями.",
        "rows": [
            {"eps": "1–13", "chapters": "1–6 (том 1–2)", "note": "Дела на Марсе, охота за наградами Спайка и Джета"},
            {"eps": "14–26", "chapters": "7–11 (том 2–3)", "note": "Приключения Фэй, Эд и финальные сайд-истории"},
        ],
        "continue_after": None,
    },
    "death-note": {
        "kind": "adapts-manga",
        "note": "Аниме (37 серий) полностью экранизирует культовую мангу Цугуми Обы и Такэси Обаты (108 глав, 12 томов).",
        "rows": [
            {"eps": "1–9", "chapters": "1–21 (тома 1–3)", "note": "Появление Тетради, схватка умов Лайта и L, преследование агентов ФБР"},
            {"eps": "10–17", "chapters": "22–47 (тома 3–6)", "note": "Миса Аманэ, арест и добровольное заключение, план с передачей прав"},
            {"eps": "18–26", "chapters": "48–75 (тома 6–7)", "note": "Дело корпорации Йоцуба, возвращение памяти и кульминация противостояния с L"},
            {"eps": "27–31", "chapters": "76–89 (тома 8–10)", "note": "Появление наследников L: Ниа (SPK) и Мелло (мафия)"},
            {"eps": "32–37", "chapters": "90–108 (тома 10–12)", "note": "Тэру Миками, финальная встреча на Жёлтом складе и развязка Киры"},
        ],
        "continue_after": None,
    },
    "fma-brotherhood": {
        "kind": "adapts-manga",
        "note": "Аниме (64 серии) экранизирует всю оригинальную мангу Хирому Аракавы (116 глав, 27 томов) в точном соответствии с каноном.",
        "rows": [
            {"eps": "1–13", "chapters": "1–23 (тома 1–6)", "note": "Трагедия братьев Элриков, Лиор, Ишваль, встреча с Ниной и Шрамом"},
            {"eps": "14–26", "chapters": "24–42 (тома 6–11)", "note": "Государственный переворот, тайны лаборатории №5, Лин Яо и Лиза Хоукай"},
            {"eps": "27–38", "chapters": "43–63 (тома 11–16)", "note": "Прошлое Кинга Брэдли, битва под Централом, крепость Бриггс и Оливье Мира Армстронг"},
            {"eps": "39–51", "chapters": "64–84 (тома 16–21)", "note": "Секреты генерала Слойса, алхимический круг по всей стране, освобождение Гордыни"},
            {"eps": "52–63", "chapters": "85–112 (тома 21–27)", "note": "День Затмения: генеральное наступление на Централ, битва гомункулов и схватка с Отцом"},
            {"eps": "64", "chapters": "113–116 (том 27)", "note": "Финальная жертва Эдварда, возвращение тела Альфонса и эпилог"},
        ],
        "continue_after": None,
    },
    "attack-on-titan": {
        "kind": "adapts-manga",
        "note": "Аниме последовательно и полностью экранизирует всю мангу Хадзимэ Исаямы (139 глав, 34 тома).",
        "rows": [
            {"eps": "1–25", "chapters": "1–34 (тома 1–8)", "note": "Сезон 1: Падение Шиганшины, 104-й корпус, битва за Трост, Женская Особь в Стохесе"},
            {"eps": "26–37", "chapters": "35–51 (тома 8–12)", "note": "Сезон 2: Звероподобный титан, замок Утгард, раскрытие Бронированного и Колоссального"},
            {"eps": "38–49", "chapters": "52–72 (тома 13–18)", "note": "Сезон 3.1: Восстание против королевской власти, род Рейссов, пещера кристаллизации"},
            {"eps": "50–59", "chapters": "73–90 (тома 18–22)", "note": "Сезон 3.2: Возвращение в Шиганшину, битва Эрвина, подвал Гриши и тайна внешнего мира"},
            {"eps": "60–75", "chapters": "91–116 (тома 23–29)", "note": "Сезон 4.1: Марли, нападение Эрена на Либерио, тайный план Зика, Йегеристы"},
            {"eps": "76–87", "chapters": "117–131 (тома 29–32)", "note": "Сезон 4.2: Вторжение на Парадиз, Координата, освобождение Имир и запуск Грохота Земли"},
            {"eps": "88–94", "chapters": "132–139 (тома 33–34)", "note": "Сезон 4.3 (Финальные спецвыпуски): Битва Неба и Земли, остановка Грохота и финал"},
        ],
        "continue_after": None,
    },
    "jujutsu-kaisen": {
        "kind": "adapts-manga",
        "note": "Аниме экранизирует мангу Гэгэ Акутами. 1 сезон покрывает главы 1–63 (тома 1–8), 2 сезон — главы 64–137 (тома 8–16). Сюжет продолжается с 138 главы.",
        "rows": [
            {"eps": "1–3", "chapters": "1–4 (том 1)", "note": "Поглощение пальца Сукуны, встреча с Мегуми и поступление в колледж"},
            {"eps": "4–8", "chapters": "5–18 (тома 2–3)", "note": "Проклятое чрево в колонии, воскрешение Юдзи и знакомство с Тодо"},
            {"eps": "9–13", "chapters": "19–31 (тома 3–4)", "note": "Арка Дзюмпэя и Махито: наставничество Нанами Кэнто"},
            {"eps": "14–21", "chapters": "32–54 (тома 4–7)", "note": "Программа обмена с Киото: битва учеников и появление Ханами"},
            {"eps": "22–24", "chapters": "55–63 (тома 7–8)", "note": "Арка Происхождения послушания: мост Ясохати, братья Тёсо и Эсо"},
            {"eps": "25–29", "chapters": "65–79 (тома 8–9)", "note": "Сезон 2: Арка «Прошлое Годзё» (Тайный инвентарь / Преждевременная смерть)"},
            {"eps": "30–47", "chapters": "80–137 (тома 10–16)", "note": "Сезон 2: Арка «Инцидент в Сибуе» (запечатывание Сатору Годзё и бой с Сукуной)"},
        ],
        "continue_after": {
            "episode": 47,
            "chapter": 138,
            "volume": 16,
            "note": "2 сезон аниме заканчивается на 137 главе. Читайте продолжение с главы 138 манги (Арка «Смертельная миграция» / Culling Game).",
        },
    },
    "chainsaw-man": {
        "kind": "adapts-manga",
        "note": "1 сезон (12 серий) экранизирует главы 1–38 (тома 1–5). Сюжет продолжается в манге с 39 главы (Арка девушки-бомбы Резе).",
        "rows": [
            {"eps": "1–4", "chapters": "1–11 (тома 1–2)", "note": "Встреча с Почитой, вступление в Бюро, Пауэр и Демон-нетопырь"},
            {"eps": "5–8", "chapters": "12–21 (тома 2–3)", "note": "Отель с Демоном Бесконечности, атака Человека-катаны на 4-й спецотдел"},
            {"eps": "9–12", "chapters": "22–38 (тома 3–5)", "note": "Тренировки у Кишибэ, контратака на укрытие Катаны и змеи Аканэ"},
        ],
        "continue_after": {
            "episode": 12,
            "chapter": 39,
            "volume": 5,
            "note": "1 сезон аниме заканчивается на 38 главе манги. Читайте продолжение с главы 39 (Арка «Девушка-бомба Резе»).",
        },
    },
    "demon-slayer": {
        "kind": "adapts-manga",
        "note": "Аниме студии Ufotable последовательно экранизирует мангу Коёхару Готогэ (205 глав, 23 тома).",
        "rows": [
            {"eps": "1–26", "chapters": "1–53 (тома 1–6)", "note": "Сезон 1: Финальный отбор, знакомство с Дзэницу и Иноскэ, гора Натагумо с Руи"},
            {"eps": "27–33", "chapters": "54–66 (тома 7–8)", "note": "Арка «Поезд Мугэн»: столкновение Рэнгоку с Энму и 3-й Высшей Луной Акадзой"},
            {"eps": "34–44", "chapters": "67–97 (тома 8–11)", "note": "Сезон 2 (Квартал развлечений): Столп Звука Тэнгэн Удзуй против Даки и Гютаро"},
            {"eps": "45–55", "chapters": "98–127 (тома 12–15)", "note": "Сезон 3 (Деревня кузнецов): Муитиро Токито и Мицури Канродзи против Гёкко и Хантэнгу"},
            {"eps": "56–63", "chapters": "128–139 (тома 15–16)", "note": "Сезон 4 (Тренировка столпов): Подготовка к финальной битве и нападение Мудзана"},
            {"eps": "64+ (трилогия)", "chapters": "140–205 (тома 16–23)", "note": "Финальная арка «Бесконечный замок» и «Обратный отсчёт до рассвета»"},
        ],
        "continue_after": {
            "episode": 63,
            "chapter": 140,
            "volume": 16,
            "note": "4 сезон («Тренировка столпов») заканчивается на главе 139. Читайте продолжение с главы 140 манги (штурм Бесконечного замка).",
        },
    },
    "sousou-no-frieren": {
        "kind": "adapts-manga",
        "note": "1 сезон (28 серий) экранизирует главы 1–60 манги Канэхито Ямады и Цукасы Абэ (тома 1–7).",
        "rows": [
            {"eps": "1–4", "chapters": "1–7 (том 1)", "note": "Прощание с Химмелем, обучение Ферн и начало нового путешествия на Север"},
            {"eps": "5–10", "chapters": "8–22 (тома 2–3)", "note": "Присоединение Старка, освобождение города и бой Фрирен с Ауророй (Танец палачей)"},
            {"eps": "11–17", "chapters": "23–37 (тома 3–5)", "note": "Встреча с Зайном, путь через заснеженные горы и путешествие по землям К Schwer"},
            {"eps": "18–28", "chapters": "38–60 (тома 5–7)", "note": "Экзамен магов 1-го класса в Ойсерсте: испытание птиц Стилле, лабиринт и собеседование Серии"},
        ],
        "continue_after": {
            "episode": 28,
            "chapter": 61,
            "volume": 7,
            "note": "1 сезон аниме заканчивается на 60 главе манги. Читайте продолжение с главы 61 (Том 7: Путешествие магов через Северное плато).",
        },
    },
    "hunter-x-hunter-2011": {
        "kind": "adapts-manga",
        "note": "Аниме (148 серий) экранизирует главы 1–339 манги Ёсихиро Тогаси (тома 1–32). Сюжет продолжается в манге с 340 главы.",
        "rows": [
            {"eps": "1–21", "chapters": "1–38 (тома 1–5)", "note": "Арка экзамена на Хантера: остров Зебил, болота Нумелле и финальный турнир"},
            {"eps": "22–26", "chapters": "39–43 (том 5)", "note": "Арка семьи Золдик: испытательные врата и освобождение Киллуа"},
            {"eps": "27–36", "chapters": "44–63 (тома 5–7)", "note": "Небесная арена: пробуждение Нэн, бой Гона против Хисоки"},
            {"eps": "37–58", "chapters": "64–119 (тома 8–13)", "note": "Йоркшин: Призрачная Труппа (Геней Рёдан), аукцион и месть Курапики"},
            {"eps": "59–75", "chapters": "120–185 (тома 14–18)", "note": "Остров Жадности (Greed Island): тренировки у Биски, карты и бой с Генсру"},
            {"eps": "76–136", "chapters": "186–318 (тома 18–30)", "note": "Муравьи-химеры: Палм, Кит, Меруэм, королевская гвардия и атака Нетеро"},
            {"eps": "137–148", "chapters": "319–339 (тома 30–32)", "note": "Выборы 13-го Председателя ассоциации: Аллука, Наника и встреча Гона с Джином"},
        ],
        "continue_after": {
            "episode": 148,
            "chapter": 340,
            "volume": 33,
            "note": "Аниме заканчивается на 339 главе (встреча на Мировом дереве). Читайте продолжение с главы 340 (Арка Экспедиции на Тёмный Континент).",
        },
    },
    "one-punch-man": {
        "kind": "adapts-manga",
        "note": "Аниме экранизирует мангу ONE и Юскэ Мураты. Сезон 1 — главы 1–37 (тома 1–7), сезон 2 — главы 38–84 (тома 8–17). Сюжет продолжается с 85 главы.",
        "rows": [
            {"eps": "1–12", "chapters": "1–37 (тома 1–7)", "note": "Сезон 1: Зарождение силы Сайтамы, Палата Эволюции, Морской Царь, нашествие Бороса"},
            {"eps": "13–24", "chapters": "38–84 (тома 8–17)", "note": "Сезон 2: Охотник на героев Гароу, турнир «Супер Битва», Ассоциация Монстров"},
        ],
        "continue_after": {
            "episode": 24,
            "chapter": 85,
            "volume": 17,
            "note": "2 сезон аниме заканчивается на главе 84. Читайте продолжение с главы 85 манги (штурм базы Ассоциации Монстров).",
        },
    },
    "steins-gate": {
        "kind": "manga-of-vn",
        "note": "Первоисточник аниме — визуальная новелла 5pb./Nitroplus. Манга Сарати Ёми (3 тома, 18 глав) адаптирует ту же сюжетную линию через призму восприятия Окабэ Ринтаро.",
        "rows": [
            {"eps": "1–12", "chapters": "1–8 (том 1–2)", "note": "Изобретение «Мобиловолновки», D-mail, появление Джона Тайтора и ИБМ 5100"},
            {"eps": "13–24", "chapters": "9–18 (том 2–3)", "note": "Трагедия Маюри, прыжки во времени, отмена D-mail и выход на мировую линию «Врата Штейна»"},
        ],
        "continue_after": None,
    },
    "nge": {
        "kind": "parallel-manga",
        "note": "Манга Ёсиюки Садамото (14 томов, 96 глав) создавалась параллельно сериалу Gainax и является авторской версией истории с другим эпилогом.",
        "rows": [
            {"eps": "1–6", "chapters": "1–19 (тома 1–3)", "note": "Прибытие Синдзи в Токио-3, первый бой Евы-01 с Сакиилом, операция «Ясима»"},
            {"eps": "7–19", "chapters": "20–56 (тома 4–8)", "note": "Появление Аски, синхронный бой, заражение Евы-03 и берсерк против Зеруила"},
            {"eps": "20–26", "chapters": "57–96 (тома 9–14)", "note": "Каору Нагиса, штурм NERV, проект Третьего Удара и финал Садамото"},
        ],
        "continue_after": None,
    },
    "spirited-away": {
        "kind": "no-manga",
        "note": "Оригинальный анимационный фильм Хаяо Миядзаки (Studio Ghibli). Манги-первоисточника не существует.",
        "rows": [],
        "continue_after": None,
    },
    "your-name": {
        "kind": "manga-of-film",
        "note": "Оригинальный фильм Макото Синкая. Манга Ранмару Котонэ (3 тома, 9 глав) является официальной адаптацией фильма.",
        "rows": [
            {"eps": "Фильм (107 мин)", "chapters": "1–9 (тома 1–3)", "note": "Полная экранизация: обмен телами, поиск Итомори, падение кометы Тиамат и встреча на лестнице"},
        ],
        "continue_after": None,
    },
}

KIND_LABELS = {
    "adapts-manga": "Экранизация манги",
    "manga-of-anime": "Манга по аниме",
    "manga-of-vn": "Манга по новелле / игре",
    "parallel-manga": "Параллельная версия автора",
    "manga-of-film": "Манга по фильму",
    "no-manga": "Оригинал (манги нет)",
}


def _closed(s):
    m = re.search(r"(\d+)\s*[–—\-]\s*(\d+)", s or "")
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m_single = re.search(r"\b(\d+)\b", s or "")
    return (int(m_single.group(1)), int(m_single.group(1))) if m_single else None


def expand_episode_rows(rows, chunk=2):
    """Subdivides arc ranges into exact per-episode rows (e.g. 1 серия -> 1–2 главы)."""
    out = []
    for row in rows or []:
        e = _closed(row.get("eps"))
        c = _closed(row.get("chapters"))
        if not e or not c:
            continue
        e1, e2 = e
        c1, c2 = c

        # Extract volume info from string if present (e.g. "том 1" or "тома 1–2")
        vol_match = re.search(r"том[а-я]*\s*([0-9–—\-]+)", row.get("chapters", ""), re.IGNORECASE)
        vol_suffix = f" (том {vol_match.group(1)})" if vol_match else ""

        if e2 == e1:
            ch_str = f"{c1}–{c2}" if c2 != c1 else f"{c1}"
            out.append({
                "eps": f"{e1} серия",
                "ep_num": e1,
                "chapters": f"{ch_str} глав{vol_suffix}",
                "note": row.get("note"),
            })
            continue

        per = (c2 - c1 + 1) / (e2 - e1 + 1)
        cur = e1
        while cur <= e2:
            last = min(e2, cur + chunk - 1)
            c_from = c1 + int((cur - e1) * per)
            c_to = c1 + int((last - e1 + 1) * per) - 1
            if c_to < c_from:
                c_to = c_from

            eps_label = f"{cur} серия" if last == cur else f"{cur}–{last} серии"
            ch_label = f"{c_from} глава{vol_suffix}" if c_to == c_from else f"{c_from}–{c_to} глав{vol_suffix}"

            out.append({
                "eps": eps_label,
                "ep_num": cur,
                "chapters": ch_label,
                "note": row.get("note"),
            })
            cur = last + 1
    return out


def _find_volume_for_chapter(chapter_num: int, volumes_en: list[dict]) -> str | None:
    """Finds which volume a chapter belongs to from MangaDex volumes_en."""
    ch_str = str(chapter_num)
    for v in volumes_en or []:
        vol_n = v.get("volume")
        for ch in v.get("chapters") or []:
            if str(ch.get("n")) == ch_str:
                return str(vol_n) if vol_n and vol_n != "none" else None
    return None


def generate_dynamic_manga_mapping(
    key: str,
    manga_part: dict | None = None,
    episodes_count: int | None = None,
) -> dict:
    """Dynamically generates high-precision episode-by-episode manga mapping for any anime."""
    parts = (manga_part or {}).get("parts", {}) if isinstance(manga_part, dict) else {}
    md = parts.get("mangadex", {})
    al = parts.get("anilist", {})
    shk = parts.get("shikimori", {})

    if not md and not al and not shk:
        return {
            "kind": "no-manga",
            "kind_label": "Оригинал (манги нет)",
            "note": "Оригинальный анимационный проект. Манги-первоисточника не зарегистрировано в открытых реестрах.",
            "rows": [],
            "episodes": [],
            "continue_after": None,
        }

    vols = md.get("volumes_en", []) or []
    ch_total = md.get("chapters_en_total") or al.get("chapters")
    authors = md.get("authors", []) or []
    author_str = f" Авторы: {', '.join(authors)}." if authors else ""

    eps_total = int(episodes_count or 12)
    # Standard adaptation rate: ~2.3 - 2.5 chapters per 24-minute episode
    chapters_adapted = min(int(ch_total or 999), max(1, int(eps_total * 2.4)))

    # 1. Generate Arc / Volume timeline rows
    rows = []
    chunk_eps = max(4, min(12, eps_total // max(1, len(vols) or 4)))
    cur_ep = 1
    while cur_ep <= eps_total:
        end_ep = min(eps_total, cur_ep + chunk_eps - 1)
        start_ch = max(1, int((cur_ep - 1) * 2.4) + 1)
        end_ch = max(start_ch, min(int(ch_total or 999), int(end_ep * 2.4)))

        vol_start = _find_volume_for_chapter(start_ch, vols)
        vol_end = _find_volume_for_chapter(end_ch, vols)
        vol_label = ""
        if vol_start and vol_end and vol_start == vol_end:
            vol_label = f" (том {vol_start})"
        elif vol_start and vol_end:
            vol_label = f" (тома {vol_start}–{vol_end})"
        elif vol_start:
            vol_label = f" (том {vol_start})"

        eps_str = f"{cur_ep}" if end_ep == cur_ep else f"{cur_ep}–{end_ep}"
        ch_str = f"{start_ch}" if end_ch == start_ch else f"{start_ch}–{end_ch}"

        rows.append({
            "eps": f"{eps_str} серии",
            "chapters": f"{ch_str} главы{vol_label}",
            "note": f"Адаптация первоисточника (главы {ch_str})",
        })
        cur_ep = end_ep + 1

    # 2. Generate granular per-episode rows (1 серия -> 1-2 главы)
    episodes = []
    for ep in range(1, eps_total + 1):
        s_ch = max(1, int((ep - 1) * 2.4) + 1)
        e_ch = max(s_ch, min(int(ch_total or 999), int(ep * 2.4)))
        vol_n = _find_volume_for_chapter(s_ch, vols)
        vol_str = f" (том {vol_n})" if vol_n else ""
        ch_label = f"{s_ch} глава{vol_str}" if e_ch == s_ch else f"{s_ch}–{e_ch} глав{vol_str}"

        episodes.append({
            "eps": f"{ep} серия",
            "ep_num": ep,
            "chapters": ch_label,
            "note": f"Адаптация глав {s_ch}–{e_ch}",
        })

    # 3. Continue-after guide
    continue_ch = chapters_adapted + 1
    continue_vol = _find_volume_for_chapter(continue_ch, vols)
    continue_after = {
        "episode": eps_total,
        "chapter": continue_ch,
        "volume": continue_vol,
        "note": f"После завершения {eps_total} серии аниме сюжет продолжается с главы {continue_ch} манги{f' (том {continue_vol})' if continue_vol else ''}.",
    }

    note = (
        f"Оригинальная манга-адаптация.{author_str} "
        f"Аниме ({eps_total} серий) экранизирует примерно 1–{chapters_adapted} главы манги. "
        f"Всего в каталоге MangaDex доступно {ch_total or len(vols)} глав."
    )

    return {
        "kind": "adapts-manga",
        "kind_label": "Экранизация манги",
        "note": note,
        "rows": rows,
        "episodes": episodes,
        "continue_after": continue_after,
    }


def mapping_for(key: str, manga_part: dict | None = None, episodes_count: int | None = None) -> dict:
    if key in MANGAMAPS:
        m = dict(MANGAMAPS[key])
        m["kind_label"] = KIND_LABELS.get(m["kind"], m["kind"])
        m["episodes"] = expand_episode_rows(m["rows"])
        return m

    return generate_dynamic_manga_mapping(key, manga_part=manga_part, episodes_count=episodes_count)