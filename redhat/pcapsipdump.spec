Name:           pcapsipdump
Version:        1.2.0
Release:        1%{?dist}
Summary:        Dump SIP sessions to one pcap file per call

License:        GPL-2.0-or-later
URL:            https://github.com/denyspozniak/pcapsipdump
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  libpcap-devel
BuildRequires:  systemd-rpm-macros

%description
pcapsipdump is a libpcap-based sniffer that writes SIP signalling and the
associated RTP/RTCP media to disk in the same format as "tcpdump -w", but
splits the output into one .pcap file per SIP session - even with thousands
of concurrent calls.

File names are built from a strftime()-style template that can embed the
caller, the callee and the Call-ID, so a single call can be located without
grepping through a bulk capture. Calls can be filtered by SIP method, by
number (regular expression) or by a pcap-filter(7) expression, and open/close
triggers can move finished files or hand them to an external command.

The same binary also splits an existing bulk capture offline:
"pcapsipdump -r bulk.pcap -d /tmp/calls".

%prep
%autosetup

%build
%make_build RELEASEFLAGS="%{optflags}" LDFLAGS="%{build_ldflags}"

%install
%make_install PREFIX=%{_prefix} SYSTEMDUNITDIR=%{_unitdir} MANDIR=%{_mandir}

%post
%systemd_post %{name}.service %{name}-cleanup.timer

%preun
%systemd_preun %{name}.service %{name}-cleanup.timer

%postun
%systemd_postun_with_restart %{name}.service

%files
%license LICENSE
%doc README.md ChangeLog
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_sbindir}/%{name}
%{_mandir}/man8/%{name}.8*
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-cleanup.service
%{_unitdir}/%{name}-cleanup.timer
%dir %attr(0700,root,root) /var/spool/%{name}

%changelog
* Fri Aug 28 2026 Denys Pozniak <denys.pozniak@gmail.com> - 1.2.0-1
- Repackage against upstream SVN r157 plus the jchavanton flush/logging fixes
- Replace the SysV init script with systemd units
- Add pcapsipdump-cleanup.timer honouring the RETENTION setting
- Build from GitHub Actions
