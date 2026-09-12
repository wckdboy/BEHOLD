.PHONY: zip clean

zip:
	@bash scripts/build_addon.sh

clean:
	rm -rf dist
