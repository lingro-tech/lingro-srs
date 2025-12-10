#!/usr/bin/env bash
#
# Скрипт реорганизации репозитория lingro-srs
# Запускать из корня репозитория:
#   /home/ol/nvme512/lingro-srs
#
#   chmod +x reorg_repo.sh
#   ./reorg_repo.sh
#

set -euo pipefail

# Проверяем, что стоим в нужном каталоге (по наличию README.md и app/)
if [[ ! -f "README.md" ]]; then
  echo "Не найден README.md в текущем каталоге. Запустите скрипт из корня репозитория."
  exit 1
fi

echo "Текущий каталог: $(pwd)"
echo "Старт реорганизации..."

###############################################
# 1. Создаём базовые верхнеуровневые каталоги #
###############################################

# backend
if [[ ! -d "backend" ]]; then
  echo "Создаю каталог backend/"
  mkdir backend
else
  echo "Каталог backend/ уже существует — пропускаю создание."
fi

# frontend
if [[ ! -d "frontend" ]]; then
  echo "Создаю каталог frontend/"
  mkdir frontend
else
  echo "Каталог frontend/ уже существует — пропускаю создание."
fi

# offline
if [[ ! -d "offline" ]]; then
  echo "Создаю каталог offline/"
  mkdir offline
else
  echo "Каталог offline/ уже существует — пропускаю создание."
fi

# infra
if [[ ! -d "infra" ]]; then
  echo "Создаю каталог infra/"
  mkdir infra
else
  echo "Каталог infra/ уже существует — пропускаю создание."
fi

###############################################
# 2. Переносим старый app/ в backend/         #
###############################################

if [[ -d "app" ]]; then
  echo "Переношу app/ в backend/ (git mv)..."
  git mv app backend
else
  echo "Каталог app/ не найден (возможно уже перенесён) — пропускаю."
fi

# Теперь всё, что было в app/, живёт в backend/
# Ожидаем там файлы: app_srs.py, srs_logic.py, start_app.sh, static/, README.md, requirements.txt

# Переименовываем app_srs.py -> app/main.py
if [[ -f "backend/app_srs.py" ]]; then
  echo "Создаю каталог backend/app/ (если ещё нет)..."
  mkdir -p backend/app

  echo "Переименовываю backend/app_srs.py -> backend/app/main.py (git mv)..."
  git mv backend/app_srs.py backend/app/main.py
else
  echo "Файл backend/app_srs.py не найден — пропускаю переименование main.py."
fi

# Переносим srs_logic.py внутрь backend/app/
if [[ -f "backend/srs_logic.py" ]]; then
  echo "Переношу backend/srs_logic.py -> backend/app/srs_logic.py (git mv)..."
  mkdir -p backend/app
  git mv backend/srs_logic.py backend/app/srs_logic.py
else
  echo "Файл backend/srs_logic.py не найден — пропускаю."
fi

# Переносим static/ внутрь backend/app/static
if [[ -d "backend/static" ]]; then
  echo "Переношу backend/static/ -> backend/app/static/ (git mv)..."
  mkdir -p backend/app
  git mv backend/static backend/app/static
else
  echo "Каталог backend/static/ не найден — пропускаю."
fi

# Переименовываем start_app.sh -> start_backend.sh
if [[ -f "backend/start_app.sh" ]]; then
  echo "Переименовываю backend/start_app.sh -> backend/start_backend.sh (git mv)..."
  git mv backend/start_app.sh backend/start_backend.sh
else
  echo "Файл backend/start_app.sh не найден — пропускаю."
fi

# Создаём внутри backend/app базовую структуру под FastAPI, если ещё не создана
echo "Создаю базовую структуру каталогов внутри backend/app/..."
mkdir -p backend/app/api
mkdir -p backend/app/core
mkdir -p backend/app/db
mkdir -p backend/app/models
mkdir -p backend/app/schemas
mkdir -p backend/app/services

# backend/requirements.txt уже переехал вместе с app -> backend
if [[ -f "backend/requirements.txt" ]]; then
  echo "Файл backend/requirements.txt уже существует."
else
  echo "Файл backend/requirements.txt не найден — создаю пустой шаблон."
  cat > backend/requirements.txt <<'EOF'
# Зависимости backend (FastAPI + PostgreSQL и пр.)
fastapi
uvicorn[standard]
# sqlalchemy или sqlmodel — выбрать нужное
sqlalchemy
psycopg[binary]
pydantic
python-jose[cryptography]
EOF
fi

###############################################
# 3. Создаём базовый каркас frontend/         #
###############################################

echo "Создаю базовый каркас frontend/ (без установки зависимостей)..."

# src, public, базовые подпапки
mkdir -p frontend/src/app
mkdir -p frontend/src/components/{layout,srs,auth,ui}
mkdir -p frontend/src/lib/i18n
mkdir -p frontend/src/locales/{en,ru}
mkdir -p frontend/src/styles
mkdir -p frontend/public/icons

# .gitkeep, чтобы каталоги попали в git
touch frontend/src/app/.gitkeep
touch frontend/src/components/layout/.gitkeep
touch frontend/src/components/srs/.gitkeep
touch frontend/src/components/auth/.gitkeep
touch frontend/src/components/ui/.gitkeep
touch frontend/src/lib/i18n/.gitkeep
touch frontend/src/locales/en/.gitkeep
touch frontend/src/locales/ru/.gitkeep
touch frontend/src/styles/.gitkeep
touch frontend/public/icons/.gitkeep

# Заготовка package.json, если ещё нет
if [[ ! -f "frontend/package.json" ]]; then
  echo "Создаю frontend/package.json (минимальная заготовка)..."
  cat > frontend/package.json <<'EOF'
{
  "name": "lingro-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
  },
  "devDependencies": {
  }
}
EOF
else
  echo "frontend/package.json уже существует — не трогаю."
fi

# Базовые конфиги (пустые заготовки, если нет)
if [[ ! -f "frontend/next.config.mjs" ]]; then
  cat > frontend/next.config.mjs <<'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Здесь будем настраивать i18n и пр.
};

export default nextConfig;
EOF
  echo "Создан frontend/next.config.mjs."
fi

if [[ ! -f "frontend/tailwind.config.mjs" ]]; then
  cat > frontend/tailwind.config.mjs <<'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {}
  },
  plugins: []
};
EOF
  echo "Создан frontend/tailwind.config.mjs."
fi

if [[ ! -f "frontend/postcss.config.mjs" ]]; then
  cat > frontend/postcss.config.mjs <<'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF
  echo "Создан frontend/postcss.config.mjs."
fi

if [[ ! -f "frontend/tsconfig.json" ]]; then
  cat > frontend/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ESNext",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
EOF
  echo "Создан frontend/tsconfig.json."
fi

# Заглушка манифеста PWA
if [[ ! -f "frontend/public/manifest.json" ]]; then
  cat > frontend/public/manifest.json <<'EOF'
{
  "name": "Lingro SRS",
  "short_name": "Lingro",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ffffff",
  "icons": []
}
EOF
  echo "Создан frontend/public/manifest.json."
fi

# Стартовый скрипт для фронтенда
if [[ ! -f "frontend/start_frontend.sh" ]]; then
  cat > frontend/start_frontend.sh <<'EOF'
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
npm run dev
EOF
  chmod +x frontend/start_frontend.sh
  echo "Создан frontend/start_frontend.sh."
fi

###############################################
# 4. Перенос оффлайн-компонент в offline/     #
###############################################

move_if_exists() {
  local src="$1"
  local dst_dir="$2"

  if [[ -d "$src" ]]; then
    echo "Переношу $src -> $dst_dir/ (git mv)..."
    git mv "$src" "$dst_dir"/
  else
    echo "Каталог $src не найден — пропускаю."
  fi
}

move_if_exists "freqphrase-builder" "offline"
move_if_exists "hablai" "offline"
move_if_exists "mt" "offline"
move_if_exists "subtitle-phrase-miner" "offline"
move_if_exists "subtitles-cleaner" "offline"
move_if_exists "tts" "offline"
move_if_exists "img" "offline"

###############################################
# 5. Infra (пока только каталог)              #
###############################################

# Если docker-compose.yml будет добавлен, его можно положить в infra/
if [[ -f "docker-compose.yml" ]]; then
  echo "Переношу docker-compose.yml -> infra/ (git mv)..."
  git mv docker-compose.yml infra/
else
  echo "Файл docker-compose.yml не найден — возможно, вы ещё его не создавали."
fi

echo "Реорганизация завершена."
echo "Проверьте git статус:"
echo "  git status"
echo "Если всё устраивает — закоммитьте изменения."
