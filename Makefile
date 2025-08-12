up:
	docker compose -f docker-compose.yml up -d --build --force-recreate --remove-orphans

watch:
	WATCH_MODE=True docker compose -f docker-compose.yml watch

stop:
	docker compose -f docker-compose.yml stop

rm:
	docker compose -f docker-compose.yml down -v

logs:
	docker compose -f docker-compose.yml logs
