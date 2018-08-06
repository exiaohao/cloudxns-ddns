restart:
	docker-compose build
	docker-compose up -d

debug:
	docker exec -it cloudxns-ddns_service_1 ipython

log:
	docker logs -f cloudxns-ddns_service_1