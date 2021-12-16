%global pypi_name iodict
%{?!released_version: %global released_version 0.11.3}

Name:           %{pypi_name}
Release:        1%{?dist}
Summary:        iodict is a thread safe dictionary implementation which uses a pure python object store.

License:        None
URL:            https://github.com/directord/iodict
Version:        %{released_version}
Source0:        iodict.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel

%description
iodict is a thread safe dictionary implementation which uses a pure python
object store.

Requires(pre):  shadow-utils

%prep
%autosetup -n %{pypi_name}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%py3_build

%install
%py3_install

%check
%{__python3} setup.py test

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/%{pypi_name}
%{python3_sitelib}/%{pypi_name}-%{released_version}-py%{python3_version}.egg-info

%changelog
* Thu Jul 29 2021 Kevin Carter <kecarter@redhat.com>
- Initial package.
