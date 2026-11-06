# Локальный NinjaTrader-пакет для стека 23.5

Начать с [технической спецификации](../../spec/AGENT-TRADING-23-5-TECHNICAL-STACK.md).
Это public-исходники собственного индикатора/Sim-only AddOn, не DLL NinjaTrader и не рыночная база.
Нет разрешения торговать только на основании наличия этого каталога.

## Зависимости

Windows x64, установленный NinjaTrader Desktop (проверенная база 8.1.8.4), .NET Framework 4.8,
локальный `bin/Custom/NinjaTrader.Custom.csproj` и существующий Custom.dll с его ресурсом.
Roslyn и зависимости берутся из установленного NinjaTrader. Не скачивать DLL вендора из чужого архива.
PowerShell 5.1+; scripts хранятся с UTF‑8 BOM для Windows PowerShell. Все результаты — в игнорируемом `.local/`.

## Сборка и установка агентом

```powershell
& .\tools\agent_trading\build.ps1
# При нестандартной установке передать -NinjaUserDir и -NinjaInstallBin.
# После нормального полного закрытия NinjaTrader человеком:
& .\tools\agent_trading\install.ps1
```

Build не меняет установленный модуль или GUI. Он запускает синтетические tests и собирает клиент,
helper и полный Custom.dll со всеми локальными исходниками csproj, подставляя три исходника пакета.
Внешние исходники/ресурсы не попадают в git. Install проверяет завершение процесса, source/build hashes,
целевой каталог, сохраняет предыдущие файлы и затем устанавливает DLL/source/csproj.
Не запускает терминал, не сохраняет пароли, не включает ATI, не меняет счёт или workspace.

После входа человека создать/открыть MNQ-график, выбрать **Sim101**, добавить `MNQ Protection Panel`.
Параметры: RiskBudget300, RoundTripCommission2, AutoProtectOnLoadtrue, AutoProfitTargetfalse,
AllowLiveOrdersfalse. Проверить Flat/активные заявки; startup не присваивает прежнюю позицию.
Сохранить Compact, пока график открыт; настройку cold startup проверить отдельно по спецификации.

## Чтение API

```powershell
& .\tools\agent_trading\.local\build\SimApiClient.exe status
& .\tools\agent_trading\tools\probe_api.ps1
```

Probe шлёт только status, preview и заранее недопустимые торговые запросы: проверяет **серверный** отказ
для OneUp, другого символа, старой session, quantity2, broad flatten, закрытия не своей позиции,
повтор preview и конфликт requestId. Сравнивает начальные/конечные positions/orders.
Если реальная сим-позиция изменилась извне во время проверки, probe требует осмотра, а не закрывает её.

JSON передавать через stdin (не собирать shell-команду из непроверенного пользовательского текста):

```powershell
$simState = (& .\tools\agent_trading\.local\build\SimApiClient.exe status) | ConvertFrom-Json
@{op='preview_entry';account='Sim101';instrument='MNQ DEC26';session=$simState.session;
  requestId=[guid]::NewGuid().ToString('N');side='BUY';quantity=1} |
  ConvertTo-Json -Compress |
  & .\tools\agent_trading\.local\build\SimApiClient.exe request
```

Это **не открывает сделку**. Торговый `place_entry` требует отдельного разрешённого теста/действия,
тех же полей и `confirm=SIM101_ONLY`. Разрешены только MNQ DEC26 и quantity1; rollover не автоматический.
Перед повтором после timeout читать status, а не генерировать новый id для той же заявки.
`close_test` доступен только для собственного API-входа текущей server-session при неизменённом владении.
Нельзя закрывать чужую/ручную позицию ради прохождения теста.

## Откат

Человек управляет своими позициями и нормально закрывает NinjaTrader. Агент возвращает DLL,
csproj и существовавшие исходники из `.local/backups/<timestamp>`; добавленные впервые файлы
нужно переместить в локальный архив вместе с их Compile references (не оставлять старый DLL и новую
непреднамеренно автособираемую версию source). Не возвращать старые credentials/workspace поверх
новых данных пользователя. После входа проверить версию, позиции/ордера и восстановление интерфейса.

## Границы проверки

На исходном компьютере проверены transport/status/отказы/replay, а допустимые entry/close API
не выполнялись. Для пакета требуются новые build/read-only проверки в целевой среде.
Симуляционный экранный тест подтвердил создание стопа и cleanup, не полный набор partial-fill races.
Источник котировок API — callback панели; свежесть callback не доказывает real-time биржевое право.
Требования и ограничения подробно перечислены в спецификации.
