#!/bin/bash

REQUIRED_MONO_VERSION="4.0.1"
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
	yes | yum install mono-devel-4.0.1 --skip-broken
	yes | yum install mono-complete-4.0.1 --skip-broken
	# Install required stuff to build cryptography package
	yes | yum -y install gcc 
	yes | yum -y install python-devel
	yes | yum -y install openssl-devel
	# Install requiered packages for the QsDriverHost
	pip install -r $ES_INSTALL_PATH/packages/VirtualEnvironment/requirements.txt
	
}

setup_supervisor() {
	# Install Needed Package
	yes | yum install python-setuptools
	yes | yum install supervisor
	# create config file
	echo_supervisord_conf > /etc/supervisord.conf
	echo -e '\n[program:cloudshell_execution_server]\ndirectory='$ES_INSTALL_PATH'\ncommand=/bin/bash -c "/usr/bin/mono QsExecutionServerConsoleConfig.exe /s:'$cs_server_host' /u:'$cs_server_user' /p:'$cs_server_pass' /esn:'$es_name' /i:'$ES_NUMBER_OF_SLOTS' && /usr/bin/mono QsExecutionServer.exe console"\nenvironment=MONO_IOMAP=all\n' >> /etc/supervisord.conf
}

# Install Python pip
yum-complete-transaction -y --cleanup-only
yes | yum install epel-release
yes | yum -y install python-pip
yes | pip install -U pip

# create installation directory
mkdir -p $ES_INSTALL_PATH

# download ES
wget $ES_DOWNLOAD_LINK -O es.tar
tar -xf es.tar -C $ES_INSTALL_PATH --strip-components=1

if [command_exists mono]
	then
		echo "Mono installed, checking version..."
		res=$(mono -V);

		if ! [contains "res" $REQUIRED_MONO_VERSION]
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
pip install virtualenv

# add python path to customer.config
# python_path=$(which python)
# sed -i "s~</appSettings>~<add key='ScriptRunnerExecutablePath' value='${python_path}' />\n</appSettings>~g" customer.config

service supervisord start
rm es.tar

