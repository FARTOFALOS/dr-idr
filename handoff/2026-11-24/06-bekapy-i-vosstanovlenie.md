# 06. Бэкапы дня и восстановление без облака

## Что где хранится

| Бэкап | Где | Что внутри | Восстановить |
|---|---|---|---|
| Снимок рабочей копии | ветка `snapshot/working-copy-2026-11-24` (2b40998, только локально) | все незакоммиченные и новые файлы на 24.11 23:30 UTC поверх `main` | `git worktree add ../dr-idr-snap snapshot/working-copy-2026-11-24` (посмотреть) или `git checkout snapshot/working-copy-2026-11-24 -- <путь>` (вернуть файл) |
| Ветки дня с GitHub | `_backup/2026-11-24_branches.bundle` (нужен `main` 6897a8a) | PR #32, #33, #34, `ant-layer-23-5`, `ekran-24-r9` | `git fetch _backup/2026-11-24_branches.bundle 'refs/remotes/origin/*:refs/remotes/origin/*'` |
| Локальные имена веток | `handoff/pr32-state-colors`, `handoff/pr33-lines-70-50`, `handoff/pr34-steady-hover`, `ant-layer-23-5`, `ekran-24-r9` | то же, что на GitHub на 24.11 | уже в репозитории |
| tv-palette целиком (устаревший снимок) | `_backup/2026-11-24_tv-palette.bundle` | коммиты и теги на HEAD f63a983 (24.11 23:28 UTC); актуально — сама папка `tv-palette` | `git clone _backup/2026-11-24_tv-palette.bundle tv-palette-restored` |
| Шаги 24.11 по файлам | `*.bak-*-2411`, `.claude-*-235.patch`, `_backup-2026-11-24-flicker/`, `_backup/2026-11-24_lines-70-50/` | состояния файлов до каждого шага | см. 02, раздел «Откат по частям» |
| Старые поставки | `Claude outputs/` | `ant-layer-commit-2411.tgz`, `ekran-24-r9-2411.bundle`, `backup-before-tp2-2026-11-10.tgz`, `local-state-2026-11-10.tgz`, поставки TP-2.0 | распаковать в отдельную папку и сравнить |
| Файлы облачного проекта | `handoff/2026-11-24/cloud-files/` (23.5) и `_backup/2026-11-24_tv-dark-copies/` (ранняя спека палитры) | патчи цветов и мельтешения, заметка журнала; спека и инвентарь палитры v2 | — |
| Эта папка в git | ветка `handoff-2026-11-24` (только локально) | `main` + `handoff/2026-11-24/` + ссылка в `AGENTS.md` | `git show handoff-2026-11-24:handoff/2026-11-24/README.md` |

`_backup/`, `Claude outputs/` и `.bak` лежат только на диске ПК (не в git). Для внешней копии достаточно скопировать
папку `dr-idr` целиком (с `.git`) — внутри будут и ветки, и бандлы.

## Как ветки дня попали на ПК

Песочница агента на ПК не ходит на github.com (прокси 403), поэтому `git fetch` с ПК из агента не работает. Ветки
собраны в облаке в `git bundle` и перенесены файлом. Сам оператор (обычный терминал) может `git fetch origin` как
обычно. Когда PR будут слиты, `git fetch --prune` уберёт `origin/claude/project-thread-*`, но локальные
`handoff/pr*` останутся.

## Если облака больше нет

- Всё, что нужно для продолжения, — в этой папке, в ветках выше, в `tv-palette/` и в `AGENTS.md`.
- Недоступно без облака: чаты тредов, документ Claude Docs (U9taB5dTdHw9TkFPqe8vT6), общая папка проекта (её копия по
  23.5 — `cloud-files/`; всё по палитре — в `tv-palette/START/`).
- Память проекта (заметки облачного координатора) сводится к 04 и 05 этой папки.
