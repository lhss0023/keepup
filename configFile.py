import configparser
import logging
# Read configuration file /etc/keepup.cfg
# And Instance values in variables

config = configparser.ConfigParser()
config.read("/etc/keepup.cfg")
HOST = config.get("main", "host")
PORT = int(config.get("main", "port"))
LDAP_SERVER = config.get("main", "ldap_server")
LDAP_PORT = config.get("main", "ldap_port")
FQDN = config.get("main", "fqdn")
FQDN_PATH = config.get("main", "fqdn_path")
LDAP_USER = config.get("main", "ldap_user")
LDAP_PASSWORD = config.get("main", "ldap_password")
LDAP_USER_PATH = config.get("main", "ldap_user_path")
LOG_FILE = config.get("main", "log_file")
KEEPUP_VERSION = '1.0'
csv_usr_file_path = '/usr/local/sbin/keepup/keepup-version-usr.csv'
csv_maq_file_path = '/usr/local/sbin/keepup/keepup-version-maq.csv'
gpo_maq_path = '/etc/ansible/gpo/maq/'
gpo_usr_path = '/etc/ansible/gpo/usr/'
size = 1024

logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
