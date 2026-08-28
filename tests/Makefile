tests:
	$(MAKE) -C unit
	$(MAKE) -C .. pcapsipdump
	# tests/segfaults needs a packet-size.prepare generator that upstream
	# never committed, so it stays out of the default run.
	#$(MAKE) -C segfaults
	$(MAKE) -C smoke
	$(MAKE) -C performance

clean:
	$(MAKE) -C unit clean
	$(MAKE) -C performance clean

.PHONY: tests clean
