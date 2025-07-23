SRC=site
DST=_build

.PHONY: all structure render clean
all: structure render

structure:
	@mkdir -p "$(DST)"
	@echo "*" > "$(DST)"/.gitignore
	@ln -sfr -t "$(DST)" "$(SRC)"/*
	@rm "$(DST)"/**.j2

render:
	@python scripts/jinja.py "$(SRC)" "$(DST)"

serve: structure
	@python scripts/serve.py --cmd 'make render' --root "$(DST)" "$(SRC)" templates/ scripts/ ./content.yml

clean:
	@rm -rf "$(DST)"
