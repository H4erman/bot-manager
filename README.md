# Bot Manager - Android App

## Что сделано

### PC приложение (bot_manager.py)
- Темный интерфейс с цветными кнопками
- Управление BroBot и GachaBot
- Flask сервер для удаленного управления
- ngrok туннель для доступа из интернета
- Логи в реальном времени через SSE

### Android приложение (android/)
- Темный интерфейс
- Экран настроек (URL + пароль)
- Управление ботами (Старт/Стоп/Рестарт)
- Просмотр логов в реальном времени

## Как собрать APK

### Вариант 1: WSL (рекомендуется)

1. Установите WSL с Ubuntu:
   ```powershell
   wsl --install -d Ubuntu
   ```

2. В Ubuntu установите зависимости:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip buildozer git
   ```

3. Скопируйте папку `android` в WSL:
   ```bash
   # В WSL
   cd ~
   git clone https://github.com/ваш-репозиторий.git
   cd ваш-репозиторий/android
   ```

4. Соберите APK:
   ```bash
   buildozer android debug
   ```

   APK будет в `bin/`

### Вариант 2: GitHub Actions

1. Создайте GitHub репозиторий
2. Добавьте файл `.github/workflows/android.yml`:
   ```yaml
   name: Build Android APK
   
   on:
     push:
       branches: [main]
   
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up JDK
           uses: actions/setup-java@v3
           with:
             java-version: '17'
         - name: Install Buildozer
           run: |
             pip install buildozer
         - name: Build APK
           run: |
             cd android
             buildozer android debug
         - name: Upload APK
           uses: actions/upload-artifact@v3
           with:
             name: bot-manager.apk
             path: android/bin/*.apk
   ```

## Как использовать

1. Запустите `bot_manager.exe` на ПК
2. Скопируйте URL из интерфейса (например, `https://xxx.ngrok.io`)
3. Установите APK на телефон
4. Введите URL и пароль в приложении
5. Управляйте ботами удаленно!

## API Endpoints

- `GET /api/bots/status` - статус всех ботов
- `POST /api/bot/{name}/start` - запустить бота
- `POST /api/bot/{name}/stop` - остановить бота  
- `POST /api/bot/{name}/restart` - рестарт бота
- `GET /api/bot/{name}/logs` - SSE стрим логов
- `POST /api/config` - установить пароль

## Требования

- Python 3.14+
- PyQT6
- Flask + Flask-SSE
- pyngrok
