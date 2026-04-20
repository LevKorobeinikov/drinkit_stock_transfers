set -e

DIR="/home/ubuntu/apt/drinkit_stock_transfers/docker"
COMPOSE="docker compose -f $DIR/docker-compose.prod.yml"
NGINX_CONF="$DIR/nginx.conf"

# Определяем кто сейчас active
if grep -qE "^\s*server app_blue:8080;" "$NGINX_CONF"; then
  ACTIVE="app_blue"
  IDLE="app_green"
else
  ACTIVE="app_green"
  IDLE="app_blue"
fi

echo "==> Active: $ACTIVE | Deploying to: $IDLE"

# Пулим новый образ и поднимаем idle
$COMPOSE pull $IDLE
$COMPOSE up -d $IDLE

# Ждём healthy
echo "==> Waiting for $IDLE to be healthy..."
for i in $(seq 1 30); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' $IDLE 2>/dev/null || echo "none")
  echo "    [$i/30] status: $STATUS"
  if [ "$STATUS" = "healthy" ]; then
    echo "==> $IDLE is healthy"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "ERROR: $IDLE not healthy after 60s — aborting, rolling back"
    $COMPOSE stop $IDLE
    exit 1
  fi
  sleep 2
done

# Переключаем nginx.conf
sed -i "s|^\(\s*\)server ${ACTIVE}:8080;|\1# server ${ACTIVE}:8080;|" "$NGINX_CONF"
sed -i "s|^\(\s*\)# server ${IDLE}:8080;|\1server ${IDLE}:8080;|" "$NGINX_CONF"

docker exec drinkit_nginx nginx -s reload
echo "==> Nginx switched to $IDLE"

# Останавливаем старый
sleep 3
$COMPOSE stop $ACTIVE
echo "==> Stopped $ACTIVE. Deploy complete."