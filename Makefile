all: prepare build run delay5s test

delay5s:
	# can be used to let components start working
	sleep 5

sys-packages:
	sudo apt install -y docker-compose
	sudo apt install python3-pip -y
	sudo pip3 install pipenv

pipenv:
	pipenv install -r requirements-dev.txt	

prepare: clean sys-packages pipenv build

build:
	docker-compose build

run:
	docker-compose up -d

restart:
	docker-compose restart

run-device:
	pipenv run python device/device.py

run-system:
	pipenv run python protection_system/system.py

run-scada:
	pipenv run python scada/scada.py

run-file-server:
	export FLASK_DEBUG=1; pipenv run python ./file_server/server.py

test:
	pipenv run pytest -sv


clean:
	docker-compose down; pipenv --rm; rm -rf Pipfile*; echo cleanup complete