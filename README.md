# Antigravity Discord Rich Presence (RPC) 🚀

[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Pure%20Python)-brightgreen.svg)](https://github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Интеграция **Discord Rich Presence (RPC)** для **Google Antigravity** (IDE, Desktop и CLI).  
Отображает динамический статус вашей работы с AI-агентом в реальном времени прямо в профиле Discord.

---

## ✨ Возможности

- 💡 **Динамические статусы агента**:
  - `Вайбкодит` — когда модель генерирует код или обдумывает решение (`PreInvocation`).
  - `Редактирует код: <файл>` — при модификации файлов (`edit_file`, `write_file`).
  - `Запускает команду: <действие>` — при выполнении тестов, сборки или команд терминала (`run_command`).
  - `Анализирует проект: <файл>` — при чтении и исследовании структуры кодовой базы (`read_file`).
  - `Ищет информацию` — при сетевом поиске через инструменты исследования (`search_web`).
  - `В режиме ожидания` — когда агент завершил ход и ожидает следующую задачу (`Stop` / таймер неактивности).
- ⏱️ **Таймер активности** — показывает прошедшее время работы над текущей сессией.
- 🔒 **Конфиденциальность из коробки**:
  - Полные пути к файлам автоматически обрезаются до базового имени (`app.py` вместо `/home/user/secret_project/app.py`).
  - Токены, пароли и чувствительные параметры в командах терминала маскируются.
- ⚡ **Zero-Dependency**: работает на стандартной библиотеке Python (`socket`, `struct`, `asyncio`, `json`). Никаких `pip install` или внешних зависимостей.
- 🖥️ **Кроссплатформенность**: полноценная поддержка **Linux** (Unix domain sockets / systemd), **Windows** (Named Pipes & TCP fallback), и **macOS**.

---

## 🛠️ Архитектура

```text
Google Antigravity (Hooks)
          │
          ▼ (PreInvocation / PreToolUse / Stop)
      hook.py  <-- Мгновенный разбор события (< 5 мс)
          │
          ▼ Local IPC (Unix Socket / Localhost TCP)
     daemon.py <-- Фоновый процесс RPC
          │
          ▼ Discord IPC Socket / Named Pipe
     Discord Desktop (Отображение в профиле)
```

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/zeroo011/antigravity-discord-rpc.git
cd antigravity-discord-rpc
```

---

### 2. Установка на Linux / macOS

Запустите скрипт автонастройки:

```bash
chmod +x install.sh
./install.sh
```

#### Запуск в фоне:
Вы можете запустить демон вручную в фоне:
```bash
python3 main.py &
```

Или настроить как **systemd user-сервис** (автозапуск при входе в систему):
```bash
mkdir -p ~/.config/systemd/user/
sed "s|%PROJECT_DIR%|$(pwd)|g; s|%PYTHON_BIN%|$(which python3)|g" antigravity-rpc.service > ~/.config/systemd/user/antigravity-rpc.service
systemctl --user daemon-reload
systemctl --user enable --now antigravity-rpc.service
```

---

### 3. Установка на Windows

1. Откройте командную строку (CMD или PowerShell) в папке репозитория.
2. Запустите скрипт настройки:
   ```cmd
   install.bat
   ```
   *(или `python setup_hooks.py --global`)*

#### Запуск в фоне на Windows:
Чтобы демон работал в фоновом режиме без всплывающего окна консоли, запустите его через `pythonw`:
```cmd
pythonw main.py
```
*(Для автозапуска можно добавить ярлык на `pythonw main.py` в папку автозагрузки Windows: нажмите `Win + R`, введите `shell:startup` и поместите туда ярлык).*

---

## 🎨 Кастомизация

### Создание своего приложения в Discord
Если вы хотите загрузить собственный логотип или переименовать статус в Discord:
1. Перейдите в [Discord Developer Portal](https://discord.com/developers/applications) и нажмите **New Application**.
2. Введите имя приложения (например, `Antigravity`).
3. В разделе **Rich Presence -> Art Assets** загрузите:
   - `antigravity_logo` (Большой логотип).
   - `coding`, `thinking`, `terminal`, `idle` (Маленькие значки статусов).
4. Скопируйте **Application ID (Client ID)**.
5. Укажите его в переменной окружения:
   ```bash
   export DISCORD_CLIENT_ID="ВАШ_CLIENT_ID"
   ```
   или измените поле `DEFAULT_CLIENT_ID` в `src/config.py`.

### Настройка текста статусов и таймаута
В файле `src/config.py` вы можете изменить любые тексты статусов и таймер неактивности:
```python
IDLE_TIMEOUT_SECONDS = 120  # переключать в Idle через 2 минуты неактивности

STATUS_TEXTS = {
    "thinking": {
        "state": "Вайбкодит",
        "details": "Формулирует ответ...",
    },
    ...
}
```

---

## 🧪 Тестирование

Запуск модульных тестов:
```bash
python3 -m unittest discover tests/
```

Проверка соединения с Discord:
```bash
python3 main.py --test
```

Эмуляция событий хука вручную:
```bash
# Эмуляция начала рассуждений
echo '{"modelName":"Gemini 3.8 Flash"}' | python3 main.py --hook --event PreInvocation

# Эмуляция редактирования файла
echo '{"toolCall":{"name":"edit_file","args":{"Path":"server.py"}}}' | python3 main.py --hook --event PreToolUse
```

---

## 📄 Лицензия

MIT License — подробности в файле [LICENSE](LICENSE).
