.PHONY: evaluate figures all clean

# Usage: make evaluate IMG_DIR=/path/to/images LIMIT=50 N=1000

IMG_DIR ?= .
LIMIT ?= 50
N ?= 1000

METRICS_DIR := docs/metrics

evaluate:
	@echo "Evaluating watermark on $(IMG_DIR) (limit=$(LIMIT))"
	python -m scripts.evaluate_watermark --images $(IMG_DIR) --limit $(LIMIT)
	@echo "Evaluating pHash ROC on $(IMG_DIR) (limit=$(LIMIT))"
	python -m scripts.evaluate_phash --images $(IMG_DIR) --limit $(LIMIT)
	@echo "Evaluating dual-layer ROC (if CLIP available) on $(IMG_DIR) (limit=$(LIMIT))"
	python -m scripts.evaluate_dual_layer --images $(IMG_DIR) --limit $(LIMIT) || true
	@echo "Benchmarking local ledger appends (N=$(N))"
	LEDGER_SECRET=$${LEDGER_SECRET:-ephemeral} python -m scripts.benchmark_ledger --n $(N)

figures:
	python -m scripts.generate_chapter6_figures

all: evaluate figures

clean:
	rm -f $(METRICS_DIR)/*.json $(METRICS_DIR)/*.csv docs/figures/*.png
	@echo "Cleaned metrics and figures."

# --- Local HTTPS server helpers (non-intrusive) ---
.PHONY: serve-start serve-stop serve-stop-force serve-restart serve-status serve-logs

serve-start:
	@bash scripts/https_server.sh start

serve-stop:
	@bash scripts/https_server.sh stop

serve-stop-force:
	@bash scripts/https_server.sh stop --force

serve-restart:
	@bash scripts/https_server.sh restart

serve-status:
	@bash scripts/https_server.sh status

serve-logs:
	@bash scripts/https_server.sh logs -f

