_CHECK_PODMAN := $(shell command -v podman 2> /dev/null)
define compose-tool
	$(if $(_CHECK_PODMAN), podman-compose, docker-compose) -f container-compose.yml
endef

define container-tool
	$(if $(_CHECK_PODMAN), podman, docker)
endef

define download_dump
	wget https://infrastructure.fedoraproject.org/infra/db-dumps/anitya.dump.xz -O ./.container/dump/anitya.dump.xz
endef

define remove_dump
	$(call container-tool) exec -it postgres \bash -c 'rm /dump/anitya.dump.xz'
endef

up:
	$(call compose-tool) up -d
restart:
	$(call compose-tool) restart
halt:
	$(call compose-tool) down
bash-web:
	$(call container-tool) exec -it anitya-web bash -c "cat /app/ansible/roles/anitya-dev/files/motd; bash;"
bash-consumer:
	$(call container-tool) exec -it anitya-librariesio-consumer bash -c "cat /app/ansible/roles/anitya-dev/files/motd; bash;"
logs:
	$(call compose-tool) logs -f
init-db:
	$(call container-tool) exec -it anitya-web bash -c "python3 createdb.py"
dump-restore: init-db
	$(call download_dump)
	$(call container-tool) exec -it postgres \bash -c 'runuser -l postgres -c "createuser anitya" && xzcat /dump/anitya.dump.xz | runuser -l postgres -c "psql anitya"'
	$(call remove_dump)
