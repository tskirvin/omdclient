Name:           omdclient
Group:          System Environment/Libraries
Version:        1.1.0
Release:        0%{?dist}
Summary:        OMD/WATO API check_mk connection tools for puppet
URL:            http://cms-git.fnal.gov/omdclient.git

License:        Artistic 2.0
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch

Requires:       rsync shyaml moreutils python-beautifulsoup4 python-requests
BuildRequires:  rsync

Source:         omdclient-%{version}-%{release}.tar.gz

%description
Tools to interact with the OMD/WATO API for check_mk, and to tie them 
into puppet.

%prep
%setup -q -c -n omdclient

%build
# Empty build section added per rpmlint

%install
if [[ $RPM_BUILD_ROOT != "/" ]]; then
    rm -rf $RPM_BUILD_ROOT
fi

for i in etc usr; do
    rsync -Crlpt --delete ./${i} ${RPM_BUILD_ROOT}
done

for i in bin sbin; do
    if [ -d ${RPM_BUILD_ROOT}/$i ]; then
        chmod 0755 ${RPM_BUILD_ROOT}
    fi
done

mkdir -p ${RPM_BUILD_ROOT}/usr/share/man/man1
for i in `ls usr/bin`; do
    pod2man --section 1 --center="System Commands" usr/bin/${i} \
        > ${RPM_BUILD_ROOT}/usr/share/man/man1/${i}.1 ;
done

python setup.py install --prefix=${RPM_BUILD_ROOT}/usr

%clean
# Adding empty clean section per rpmlint.  In this particular case, there is 
# nothing to clean up as there is no build process

%files
%defattr(-,root,root)
%config(noreplace) /etc/omdclient/config.yaml
%config(noreplace) /etc/omdclient/place.holder
%{_bindir}/omd-*
/usr/share/man/man1/*
/usr/libexec/omdclient/git-hooks/*
/usr/lib*/python*/site-packages/*
/etc/omdclient/*

%changelog
* Mon Jun 15 2015  Tim Skirvin <tskirvin@fnal.gov>      1.1.0-0
- added omd-nagios-report, omd-nagios-ack, omd-nagios-downtime
- fixed the git post-receive hook

* Mon Jun 15 2015  Tim Skirvin <tskirvin@fnal.gov>      1.0.0-0
- initial commit
