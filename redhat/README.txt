Building an RPM
===============

The GitHub Actions "release" workflow builds these packages automatically for
Rocky Linux 9 and Fedora. To build one by hand from a source checkout:

    VERSION=$(sed -n 's/.*PCAPSIPDUMP_VERSION "\(.*\)".*/\1/p' pcapsipdump.h)
    mkdir -p ~/rpmbuild/SOURCES
    git archive --format=tar.gz \
        --prefix="pcapsipdump-${VERSION}/" -o ~/rpmbuild/SOURCES/pcapsipdump-${VERSION}.tar.gz HEAD
    rpmbuild -bb redhat/pcapsipdump.spec

Build dependencies: gcc-c++ make libpcap-devel systemd-rpm-macros rpm-build.
