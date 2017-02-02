#!/bin/bash

REQUIRED_MONO_VERSION="4.0.1"
REQUIRED_PYTHON_VERSION="2.7.10"
ES_DOWNLOAD_LINK="https://s3.amazonaws.com/alex-az/ExecutionServer.tar"
ES_INSTALL_PATH="/opt/ExecutionServer/"

ES_NUMBER_OF_SLOTS=100
cs_server_host=${1}  # "192.168.120.20"
cs_server_user=${2}  # "user"
cs_server_pass=${3}  # "password"
es_name=${4}  # "ES_NAME"


command_exists () {
    type "$1" &> /dev/null ;
}

contains() {
    string="$1"
    substring="$2"

    if test "${string#*$substring}" != "$string"
    then
        return 0    # $substring is in $string
    else
        return 1    # $substring is not in $string
    fi
}

unistall_mono_old_version () {
	echo "Uninstalling old Mono..."
	yes | yum remove mono
	yes | yum autoremove
}

install_mono () {
	echo "installing mono v$REQUIRED_MONO_VERSION"
	# Obtain necessary gpg keys by running the following:
	wget http://download.mono-project.com/repo/xamarin.gpg
	# Import gpg key by running the following:
	rpm --import xamarin.gpg
	# Add Mono repository
	yum-config-manager --add-repo http://download.mono-project.com/repo/centos/
	# Install Mono
	yum -y install mono-devel-4.0.1 --skip-broken
	yum -y install mono-complete-4.0.1 --skip-broken
	# Install required stuff to build cryptography package
	yum -y install gcc
	yum -y install openssl-devel
	# Install requiered packages for the QsDriverHost
	$python_path -m pip install -r $ES_INSTALL_PATH/packages/VirtualEnvironment/requirements.txt
	
}

setup_supervisor() {
	# Install Needed Package
	yum -y install python-setuptools
	yum -y install supervisor
	# create config file
	echo_supervisord_conf > /etc/supervisord.conf
	echo -e '\n[program:cloudshell_execution_server]\ndirectory='$ES_INSTALL_PATH'\ncommand=/bin/bash -c "/usr/bin/mono QsExecutionServerConsoleConfig.exe /s:'$cs_server_host' /u:'$cs_server_user' /p:'$cs_server_pass' /esn:'$es_name' /i:'$ES_NUMBER_OF_SLOTS' && /usr/bin/mono QsExecutionServer.exe console"\nenvironment=MONO_IOMAP=all\n' >> /etc/supervisord.conf
}

yum-complete-transaction -y --cleanup-only
yum clean all
yum makecache

yum -y install epel-release
# previous command failed
if [ $? -ne 0 ]
then
    echo "Epel-release installation failed"
    sed -i "s~#baseurl=~baseurl=~g" /etc/yum.repos.d/epel.repo
    sed -i "s~mirrorlist=~#mirrorlist=~g" /etc/yum.repos.d/epel.repo
    yum -y install epel-release
fi

yum install -y which
yum install -y wget
python_version=$(python -V)
if ! contains "$python_version" "$REQUIRED_PYTHON_VERSION"
then
    echo "Installing Python required version..."
    yum -y update
    yum groupinstall -y 'development tools'
    yum install -y gcc zlib-dev openssl-devel sqlite-devel bzip2-devel
    # install needed python version
    cd /opt/
    wget https://www.python.org/ftp/python/$REQUIRED_PYTHON_VERSION/Python-$REQUIRED_PYTHON_VERSION.tgz
    tar xzf Python-$REQUIRED_PYTHON_VERSION.tgz
    cd Python-$REQUIRED_PYTHON_VERSION
    ./configure --prefix=/usr/local
    make altinstall
    python_path="/usr/local/bin/python2.7"
else
    python_path=$(which python)
fi

# install python for both Python versions
wget "https://bootstrap.pypa.io/get-pip.py"
$python_path get-pip.py
python get-pip.py

# create installation directory
mkdir -p $ES_INSTALL_PATH

# download ES
wget $ES_DOWNLOAD_LINK -O es.tar
tar -xf es.tar -C $ES_INSTALL_PATH --strip-components=1

if command_exists mono
then
    echo "Mono installed, checking version..."
    res=$(mono -V);

    if ! contains "$res" "$REQUIRED_MONO_VERSION"
        then
            echo "Mono Version is not $REQUIRED_MONO_VERSION"
            unistall_mono_old_version
            install_mono
    fi
else
	install_mono
fi

setup_supervisor

# install virtualenv
$python_path -m pip install virtualenv

echo -e "<appSettings>\n<add key='ScriptRunnerExecutablePath' value='${python_path}' />\n</appSettings>" > ${ES_INSTALL_PATH}customer.config

service supervisord start
rm es.tar

