LIBS ?= -lpcap -lstdc++
RELEASEFLAGS ?= -O3 -Wall
#CXXFLAGS ?= --std=c++0x

PREFIX ?= /usr
SBINDIR ?= $(PREFIX)/sbin
SYSCONFDIR ?= /etc
SPOOLDIR ?= /var/spool/pcapsipdump
SYSTEMDUNITDIR ?= $(PREFIX)/lib/systemd/system
MANDIR ?= $(PREFIX)/share/man

# auto-detect if bsd/strings.h is available
ifeq ($(shell $(CXX) $(CXXFLAGS) $(LDFLAGS) $(DEFS) -E -o /dev/null \
    	make-checks/libbsd.cpp 2>/dev/null; echo $$?),0)
	BSDSTR_DEFS := -DUSE_BSD_STRING_H
	BSDSTR_LIBS := -lbsd
endif

# auto-detect rhel/fedora and debian/ubuntu
ifneq ($(wildcard /etc/redhat-release),)
	EXTRA_INSTALL := install-redhat
endif
ifneq ($(wildcard /etc/debian_version),)
	EXTRA_INSTALL := install-debian
endif

all: make-checks/all pcapsipdump

include make-checks/*.mk

pcapsipdump: make-checks *.cpp *.h
	$(CXX) $(RELEASEFLAGS) $(CXXFLAGS) $(LDFLAGS) $(DEFS) $(BSDSTR_DEFS) \
	*.cpp \
	$(LIBS) $(BSDSTR_LIBS) \
	-o pcapsipdump

pcapsipdump-debug: make-checks *.cpp *.h
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(DEFS) $(BSDSTR_DEFS) -ggdb \
	*.cpp \
	$(LIBS) $(BSDSTR_LIBS) -pg \
	-o pcapsipdump-debug

clean: make-checks/clean
	rm -f pcapsipdump pcapsipdump-debug gmon.out

install: pcapsipdump install-systemd install-man $(EXTRA_INSTALL)
	install -d ${DESTDIR}${SBINDIR}
	install -m 0755 pcapsipdump ${DESTDIR}${SBINDIR}/pcapsipdump
	install -d -m 0700 ${DESTDIR}${SPOOLDIR}

install-man:
	install -d ${DESTDIR}${MANDIR}/man8
	install -m 0644 man/pcapsipdump.8 ${DESTDIR}${MANDIR}/man8/pcapsipdump.8

install-systemd:
	install -d ${DESTDIR}${SYSTEMDUNITDIR}
	install -m 0644 systemd/pcapsipdump.service \
		systemd/pcapsipdump-cleanup.service \
		systemd/pcapsipdump-cleanup.timer \
		${DESTDIR}${SYSTEMDUNITDIR}/

install-redhat:
	install -d ${DESTDIR}${SYSCONFDIR}/sysconfig
	install -m 0644 redhat/pcapsipdump.sysconfig \
		${DESTDIR}${SYSCONFDIR}/sysconfig/pcapsipdump

install-debian:
	install -d ${DESTDIR}${SYSCONFDIR}/default
	install -m 0644 debian/pcapsipdump.default \
		${DESTDIR}${SYSCONFDIR}/default/pcapsipdump

.PHONY: all clean install install-systemd install-man install-redhat install-debian tests

tests:
	$(MAKE) -C tests
