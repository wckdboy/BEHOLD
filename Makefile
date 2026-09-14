.PHONY: zip clean test smoke-step

zip:
	@bash scripts/build_addon.sh

test:
	@PYTHONPATH=. python3 -m unittest discover -s tests -v

smoke-step:
	@if ! command -v blender >/dev/null 2>&1; then \
	  echo "blender is not on PATH."; \
	  echo "Run inside Blender when OCP or STEPper is present:"; \
	  echo "  blender --background --python scripts/smoke_step_vertical.py"; \
	  exit 2; \
	fi
	blender --background --python scripts/smoke_step_vertical.py

clean:
	rm -rf dist
