# Nand2Tetris Python環境セットアップ

.PHONY: setup clean test format lint run-06 run-07 run-08

# 仮想環境のセットアップ
setup:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e .[dev]

# 環境のクリーンアップ
clean:
	rm -rf venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# テスト実行
test:
	./venv/bin/pytest

# コードフォーマット
format:
	./venv/bin/black .

# コードリンティング
lint:
	./venv/bin/flake8 .

# 各章の実行
run-06:
	cd 06 && ../venv/bin/python main.py

run-07:
	cd 07 && ../venv/bin/python main.py

run-08:
	cd 08 && ../venv/bin/python main.py