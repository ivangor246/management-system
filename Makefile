# develop
up:
	docker compose -f docker-compose.yml up -d --build --force-recreate --remove-orphans $(for)

watch:
	WATCH_MODE=True docker compose -f docker-compose.yml watch

stop:
	docker compose -f docker-compose.yml stop $(for)

rm:
	docker compose -f docker-compose.yml down -v $(for)

logs:
	docker compose -f docker-compose.yml logs $(for)

clear:
	docker compose -f docker-compose.yml down -v --rmi all --remove-orphans


# test
build-test:
	docker compose -f docker-compose.test.yml build

run-test:
	docker compose -f docker-compose.test.yml run --rm test_app

logs-test:
	docker compose -f docker-compose.test.yml logs $(for)

clear-test:
	docker compose -f docker-compose.test.yml down -v --rmi all --remove-orphans
