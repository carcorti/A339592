# Single canonical C17 build; private validation is make test.
CC = gcc-13
CFLAGS = -O3 -std=c17 -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wdouble-promotion -Wformat=2
LDFLAGS =
SOURCE = a339592_v2.c
.PHONY: all test clean FORCE
all: a339592
a339592: $(SOURCE) Makefile FORCE
	@set -eu; \
	source_sum=$$(sha256sum -- "$(SOURCE)"); \
	make_sum=$$(sha256sum -- Makefile); \
	source_sha=$${source_sum%% *}; make_sha=$${make_sum%% *}; \
	for hash in "$$source_sha" "$$make_sha"; do \
	  case "$$hash" in ''|*[!0-9a-f]*) echo 'ERROR: invalid build SHA-256' >&2; exit 1;; esac; \
	  test "$${#hash}" -eq 64 || { echo 'ERROR: invalid build SHA-256 length' >&2; exit 1; }; \
	done; \
	$(CC) $(CFLAGS) -DSOURCE_SHA="\"$$source_sha\"" -DMAKE_SHA="\"$$make_sha\"" $(SOURCE) $(LDFLAGS) -o $@
test: a339592
	./a339592 selftest
	python3 ../validation/test_candidate_v2.py ./a339592
clean:
	rm -f a339592
