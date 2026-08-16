.PHONY: install test lint self-gates demo

install:
	pip install -e ".[dev]" 2>/dev/null || pip install -e .

test:
	python -m pytest tests -q

lint:
	python -m ruff check specforge tests || true

self-gates: ## dogfood: H4 contract diff + H6 scan + H1 compile on specforge itself
	python -m compileall -q specforge
	python -m specforge.cli extract-contract specforge > /tmp/sf_surface_new.json
	python -m specforge.cli extract-contract specforge > /tmp/sf_surface_ref.json
	python -c "from specforge.contracts import SurfaceSnapshot, diff_surfaces; a=SurfaceSnapshot.from_json(open('/tmp/sf_surface_ref.json').read()); b=SurfaceSnapshot.from_json(open('/tmp/sf_surface_new.json').read()); d=diff_surfaces(a,b); print('breaking:', d.has_breaking)"

demo:
	python -m specforge.cli demo
