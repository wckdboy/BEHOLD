.PHONY: zip clean test

zip:
	@bash scripts/build_addon.sh

test:
	@PYTHONPATH=. python3 -m unittest discover -s tests -v

clean:
	rm -rf dist
