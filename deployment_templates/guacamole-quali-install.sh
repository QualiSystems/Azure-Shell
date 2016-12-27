#!/bin/bash
set -e
set -o pipefail
set -o nounset

##														PARAMETERS 
GUACAMOLE_VERSION="0.9.9"
GUACAMOLE_WAR_NAME="remote"
QUALI_AUTH_MAIN_CLASS="net.sourceforge.guacamole.net.auth.quali.QualiProvider"
GUACAMOLE_PROPERTIES="/etc/guacamole/guacamole.properties"
S3LOCATION="https://s3-us-west-2.amazonaws.com/qualix-ova/qualix-0.9.9.tar.gz"
QUALI_AUTH_PACK_NAME="qualix-0.9.9"
HTTP_PORT="80"
HTTPS_PORT="443"
KEYSTORE_PASS="123123"

##														CODE

#Make sure all yum transaction are complete
yum-complete-transaction -y

#Update all 
yum update -y 

#source https://deviantengineer.com/2015/02/guacamole-centos7/

#Make sure all yum transaction are complete
yum-complete-transaction -y

#Prerequisite
yum -y install epel-release wget

wget -O /etc/yum.repos.d/home:felfert.repo http://download.opensuse.org/repositories/home:/felfert/Fedora_19/home:felfert.repo

yum -y install cairo-devel freerdp-devel gcc java-1.8.0-openjdk.x86_64 libguac libguac-client-rdp libguac-client-ssh libguac-client-vnc \
libjpeg-turbo-devel libpng-devel libssh2-devel libtelnet-devel libvncserver-devel libvorbis-devel libwebp-devel openssl-devel pango-devel \
pulseaudio-libs-devel terminus-fonts tomcat tomcat-admin-webapps tomcat-webapps uuid-devel

#Guacd Install
mkdir ~/guacamole && cd ~/
wget http://sourceforge.net/projects/guacamole/files/current/source/guacamole-server-0.9.9.tar.gz
tar -xzf guacamole-server-$GUACAMOLE_VERSION.tar.gz
cd guacamole-server-$GUACAMOLE_VERSION
./configure --with-init-dir=/etc/init.d
make
make install
ldconfig

#guacamole client
mkdir -p /var/lib/guacamole
cd /var/lib/guacamole/
wget http://sourceforge.net/projects/guacamole/files/current/binary/guacamole-$GUACAMOLE_VERSION.war -O $GUACAMOLE_WAR_NAME.war
ln -s /var/lib/guacamole/$GUACAMOLE_WAR_NAME.war /var/lib/tomcat/webapps/
rm -rf /usr/lib64/freerdp/guacdr.so
ln -s /usr/local/lib/freerdp/guacdr.so /usr/lib64/freerdp/

#Configure Guacamole
mkdir -p /etc/guacamole/
touch $GUACAMOLE_PROPERTIES
mkdir -p /usr/share/tomcat/.guacamole/{extensions,lib}
ln -s $GUACAMOLE_PROPERTIES /usr/share/tomcat/.guacamole/

echo "# /etc/guacamole/guacamole.properties
	# Hostname and port of guacamole proxy
	guacd-hostname: localhost
	guacd-port:     4822

	lib-directory: /etc/guacamole

	# Auth provider class (authenticates user/pass combination, needed if using the provided login screen)
	auth-provider: $QUALI_AUTH_MAIN_CLASS" >> $GUACAMOLE_PROPERTIES

	
#Deploy guacamole-auth-quali
cd ~
mkdir qualix
cd qualix
wget $S3LOCATION
tar -xzf $QUALI_AUTH_PACK_NAME.tar.gz
cd guacamole-auth-quali-$GUACAMOLE_VERSION
cp guacamole-auth-quali-$GUACAMOLE_VERSION.jar /etc/guacamole
cd resources
for f in *; do chmod +x $f ;  done
for f in *; do cp $f / ;  done


#Redirect ports for tomcat
iptables -t nat -A PREROUTING -p tcp --dport $HTTP_PORT -j REDIRECT --to-port 8080
iptables -t nat -A PREROUTING -p tcp --dport $HTTPS_PORT -j REDIRECT --to-port 8443
iptables-save > /etc/iptables.conf
echo "iptables-restore < /etc/iptables.conf" >> /etc/rc.local
chmod +x /etc/rc.d/rc.local


# https://www.sslshopper.com/article-how-to-create-a-self-signed-certificate-using-java-keytool.html
cd /usr/share/tomcat
keytool -genkeypair -noprompt -alias Tomcat -keyalg RSA -dname "CN=quali, OU=quali, O=quali, L=quali, S=quali, C=IL" -keystore .keystore -storepass $KEYSTORE_PASS -keypass $KEYSTORE_PASS 
 
 
# Change /etc/tomcat/server.xml
cd /etc/tomcat
sed -i '/<Service name="Catalina">/a <Connector port="8443" protocol="org.apache.coyote.http11.Http11Protocol" maxThreads="150" SSLEnabled="true" scheme="https" secure="true" keystoreFile="${user.home}/.keystore" keystorePass="'$KEYSTORE_PASS'" clientAuth="false" sslProtocol="TLS" />' server.xml

#Cleanups
cd ~
rm -rf guacamole*

#Enable all services
#http://www.davidghedini.com/pg/entry/install_tomcat_7_on_centos

chkconfig --level 234 tomcat on
chkconfig --add guacd
chkconfig --level 234 guacd on
systemctl enable tomcat
systemctl start tomcat
systemctl enable guacd
systemctl start guacd

#netstat -lnp | grep 80
#netstat -lnp | grep 443