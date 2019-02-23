#!/usr/bin/python3
import csv
import subprocess
from configFile import *


class Keepup:

    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

    def compareVersion(self, exec_code, arr_usr_csv):

        # Create an array of arrays with 2 indices.
        # Indice 0 = GPO That Are needed to Update on Client
        # Indice 1 = Updated CSV to send Back to Client
        self.arr_compare_results = []
        # Code 1 For Machine GPO
        if exec_code == '1':

            # Compare Client GPOs with Server GPOs
            arr_gpo_to_compare_versions = self.maqContentChecker(arr_usr_csv)

            # Fills the array with GPOs needed to update on indice 0, and Updated CSV to client update on indice 1.
            if len(arr_gpo_to_compare_versions) != 0:
                self.arr_compare_results = self.maqCompareVersions(arr_gpo_to_compare_versions)

        # Code 2 For User GPO
        elif exec_code == '2':

            # Request Authenticated User Name
            self.conn.send('username_request'.encode())
            self.linux_username = self.conn.recv(size).decode().rstrip('\n')

            # Request LDAP Groups of a given user and store in a array.
            ldap_grupos_gpo = self.checkUserGroupsLDAP()

            # Compare Content of User CSV and LDAP Groups, Generating a New Array to update Versions.
            arr_gpo_to_compare_versions = self.usrContentChecker(ldap_grupos_gpo, arr_usr_csv)

            # Compara Versoes e Retorna Array com GPOS para Atualizar
            # Fills the array with GPOs needed to update on indice 0, and Updated CSV to client update on indice 1.
            if len(arr_gpo_to_compare_versions) != 0:
                self.arr_compare_results = self.usrCompareVersions(arr_gpo_to_compare_versions)

    def checkUserGroupsLDAP(self):
        # Return an Array with a given user LDAP Groups.
        str_grupos_gpo = ("ldapsearch -h " + LDAP_SERVER + "." + FQDN + " -p " + LDAP_PORT + " -x -D "
                          "\"cn=" + LDAP_USER + "," + LDAP_USER_PATH + "\" -b \"" + FQDN_PATH +
                          "\" \"(sAMAccountName=" + self.linux_username + ")\" memberOF -w " + LDAP_PASSWORD +
                          " | egrep ^memberOf | cut -d ',' -f 1 | cut -d '=' -f 2")
        str_grupos_gpo = subprocess.check_output(str_grupos_gpo, shell=True).decode().rstrip('\n')
        arr_grupos_gpo = str_grupos_gpo.split('\n')
        return arr_grupos_gpo

    def executeAnsible(self, arr_gpo_to_update, exec_code):
        self.arr_gpo_got_error = []  # Array to store gpos that got error to do not change user csv version
        # Calls a function to execute Playbooks according with exec_code.
        if exec_code == '1':
            self.executeAnsibleMachine(arr_gpo_to_update)
        elif exec_code == '2':
            self.executeAnsibleUser(arr_gpo_to_update)

    def executeAnsibleUser(self, arr_gpo_to_update):
        # Execute User Playbooks
        for gpo in arr_gpo_to_update:
            gpo = gpo.split(',')
            if gpo[0] != "":
                logging.info('User: ' + self.linux_username + ' | Machine: ' + str(self.address[0]) +
                             ' | Executing GPO: ' + str(gpo[0]))
                try:
                    subprocess.check_output("ansible-playbook " + gpo_usr_path + gpo[0] + " -i " +
                                            self.address[0] + "," + " --extra-vars" + " target=" +
                                            self.address[0] + " --extra-vars" + " username=" +
                                            self.linux_username, shell=True)
                    logging.info(str('User: ' + self.linux_username + ' | Machine: ' + str(self.address[0]) +
                                     ' | GPO [OK]: ' + str(gpo[0])))
                except subprocess.CalledProcessError as ansible_run_exc:
                    self.arr_gpo_got_error.append(gpo[0])
                    logging.warning('User: ' + self.linux_username + ' | Machine: ' + str(self.address[0]) +
                                    ' | GPO [ERR]: ' + str(gpo[0]))
                    exception_output = ansible_run_exc.output
                    logging.debug(str(exception_output))

    def executeAnsibleMachine(self, arr_gpo_to_update):
        # Execute Machine Playbooks
        for file in arr_gpo_to_update:
            file = file.split(',')
            logging.info('Machine: ' + str(self.address[0]) + ' | Executing GPO: ' + str(file[0]))
            try:
                subprocess.check_output("ansible-playbook " + gpo_maq_path + file[0] + " -i " + self.address[0] +
                                        "," + " --extra-vars" + " target=" + self.address[0], shell=True)
                logging.info('Machine: ' + str(self.address[0]) + ' | GPO [OK]: ' + str(file[0]))
            except subprocess.CalledProcessError as ansible_run_exc:
                self.arr_gpo_got_error.append(file[0])
                logging.warning('Machine: ' + str(self.address[0]) + ' | GPO [ERR]: ' + str(file[0]))
                exception_output = ansible_run_exc.output
                logging.debug(str(exception_output))

    def maqContentChecker(self, arr_usr_csv):
        # Compare User GPOs with Server GPOs and return a new array.
        # If Exists GPO on User that are not on Server, Remove From User
        # If Exists GPO on Server that are not on User, Adds to User.
        arr_gpo_to_compare_versions = []

        with open(csv_maq_file_path, 'r') as version_csv:
            arr_srv_gpo = version_csv.readlines()

        for srv_gpo in arr_srv_gpo:
            gpo_exists = 0
            srv_gpo = srv_gpo.split(',')
            for usr_gpo in arr_usr_csv:
                if srv_gpo[0] in usr_gpo:
                    gpo_exists = 1
                    arr_gpo_to_compare_versions.append(usr_gpo)
            if gpo_exists == 0:
                arr_gpo_to_compare_versions.append(srv_gpo[0] + ',0')

        return arr_gpo_to_compare_versions

    def maqCompareVersions(self, arr_gpo_to_compare_versions):
        # Compare User Versions with Server Versions, returning an array for GPOs that are needed to update
        # And another to send back to client to update CSV Database
        arr_gpo_to_update = []
        arr_gpo_to_new_csv = []

        with open(csv_maq_file_path, 'rt') as version_csv:
            reader = csv.reader(version_csv, delimiter=',')
            for row_srv in reader:
                for row_maq in arr_gpo_to_compare_versions:
                    row_maq = row_maq.split(',')
                    if row_maq[0] == row_srv[0]:
                        if row_maq[1] != row_srv[1]:
                            arr_gpo_to_update.append(row_srv[0] + ',' + row_srv[1])
                        arr_gpo_to_new_csv.append(row_srv[0] + ',' + row_srv[1])
        return arr_gpo_to_update, arr_gpo_to_new_csv

    def usrContentChecker(self, check_ldap_grupos_gpo, arr_usr_csv):
        # Compare User GPOs with Server GPOs and return a new array.
        # If Exists GPO on User that are not on Server, Remove From User
        # If Exists GPO on Server that are not on User, Adds to User.
        arr_gpo_to_compare_versions = []

        # Remove user groups that not have gpos, like 'domain admins...'
        ldap_grupos_gpo = []
        check_files = "ls /etc/ansible/gpo/usr/ | egrep .yml$"
        check_files = subprocess.Popen(check_files, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check_files = check_files.stdout.readlines()
        for file in check_files:
            file = file.decode().replace('.yml\n', '')
            if file in check_ldap_grupos_gpo:
                ldap_grupos_gpo.append(file + '.yml')


        if len(ldap_grupos_gpo) == 1 and ldap_grupos_gpo[0] == '':
            return arr_gpo_to_compare_versions

        else:
            for ldap_gpo in ldap_grupos_gpo:
                gpo_exists = 0
                for usr_gpo in arr_usr_csv:
                    if ldap_gpo in usr_gpo:
                        gpo_exists = 1
                        arr_gpo_to_compare_versions.append(usr_gpo)
                if gpo_exists == 0:
                    arr_gpo_to_compare_versions.append(ldap_gpo + ',0')

            return arr_gpo_to_compare_versions

    def usrCompareVersions(self, arr_gpo_to_compare_versions):
        # Compare User GPO Versions with Server Versions, returning an array for GPOs that are needed to update
        # And another to send back to client to update CSV Database
        arr_gpo_to_update = []
        arr_gpo_to_new_csv = []

        with open(csv_usr_file_path, 'rt') as version_csv:
            reader = csv.reader(version_csv, delimiter=',')
            for row_srv in reader:
                for row_usr in arr_gpo_to_compare_versions:
                    row_usr = row_usr.split(',')
                    if row_usr[0] == row_srv[0]:
                        if row_usr[1] != row_srv[1]:
                            arr_gpo_to_update.append(row_srv[0] + ',' + row_srv[1])
                        arr_gpo_to_new_csv.append(row_srv[0] + ',' + row_srv[1])
        return arr_gpo_to_update, arr_gpo_to_new_csv