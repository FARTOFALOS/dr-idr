# design/ — исходники экранов DR Lab

| Папка | Экран | Статус | Сборка |
|---|---|---|---|
| [`sozvezdiya-23-5/src`](sozvezdiya-23-5/src) | **23.5** — основной экран (`/23-5/`, ярлык «DR Lab 23.5») | текущий, основа TP-2.0 ([meaning/25](../meaning/25-tp-2-0-specifikaciya.md)) | `python design/sozvezdiya-23-5/src/build.py` → `lab/dist/23-5/` |
| [`sozvezdiya-24`](sozvezdiya-24/README.md) | **24** «Границы хода» (`/24/`) | сохранён как работает; под SC-1.1, полная спецификация — [`spec/ekran-24/`](../spec/ekran-24/README.md) | `python design/sozvezdiya-24/src/build.py` → `lab/dist/24/` |
| [`sozvezdiya-22`](sozvezdiya-22/README.md) | дизайн 22 (`/22/`) | legacy, вне контракта, не развивать | `lab/dist/index.html`, `sozvezdiya.js` |
| [`sozvezdiya-23`](sozvezdiya-23/README.md) | дизайн 23 (`/sem-v1/`) | legacy, вне контракта, не развивать | `lab/dist/sem-v1/` |

23.5 вырос из 24: тот же сервер, контракт и рисунок; правила рисунка с причинами — в
[`meaning/13-zhurnal-vizualizacii.md`](../meaning/13-zhurnal-vizualizacii.md), требования оператора к интерфейсу — в
[`docs/UI_RULES.md`](../docs/UI_RULES.md). Перед визуальной правкой прочитайте оба.

Прежние дизайны 1–21, макеты на синтетических данных и замечания оператора по раундам 24–30.09 убраны из `main`
11.11.2026; они в истории git, коммит [`3847a70`](https://github.com/FARTOFALOS/dr-idr/tree/3847a70/design).
