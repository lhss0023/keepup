#!/usr/bin/python3

'''
    AUTHOR: Lucas Henrique
    CONTACT: henriqueweb@icloud.com
    WEBPAGE: https://www.linkedin.com/in/lhss0023/
'''

import socket
import threading
import pickle
import subprocess
from configFile import *
from keepup import Keepup


class ThreadedServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, PORT))

    def listen(self):
        # Server Starts on Listening Mode
        self.sock.listen(200)
        while True:
            client, address = self.sock.accept()
            threading.Thread(target=self.listenToClient, args=(client, address)).start()

    def listenToClient(self, conn, address):

        connection = Keepup(conn, address)

        logging.info('Connected from ' + str(connection.address))

        connection.conn.send('connected'.encode())
        connection.client_response = conn.recv(size).decode()

        # Request KeepUp Version from Client.
        connection.conn.send('version_request'.encode())
        connection.client_version = conn.recv(size).decode()

        # Recieve Execution Code From client, 1 For Machine GPO or 2 For User GPO
        conn.send('exec_code_request'.encode())
        exec_code = conn.recv(size).decode()

        # Recieve Array With Actual GPOs from Client CSV
        conn.send('arr_gpos'.encode())
        data = conn.recv(size)
        arr_usr_csv = pickle.loads(data)

        # Create an self.arr_compare_results
        # Index 0 = GPO That Are needed to Update on Client
        # Index 1 = Updated CSV to send Back to Client
        connection.compareVersion(exec_code, arr_usr_csv)

        if len(connection.arr_compare_results) != 0:
            arr_gpo_to_update = connection.arr_compare_results[0]

            # Execute Necessary Updates for Client
            connection.executeAnsible(arr_gpo_to_update, exec_code)

            # Do not change GPO version that was not successfuly
            arr_update_client_csv = []
            for gpo in connection.arr_compare_results[1]:
                gpo_exists = 0
                for gpo_to_notchange in connection.arr_gpo_got_error:
                    if gpo_to_notchange in gpo:
                        gpo_exists = 1
                        arr_update_client_csv.append(gpo_to_notchange + ',0')
                if gpo_exists == 0:
                    arr_update_client_csv.append(gpo)

            arr_update_client_csv = pickle.dumps(connection.arr_compare_results[1])

        else:
            arr_update_client_csv = pickle.dumps(connection.arr_compare_results)

        # Send Array to Client for Update
        connection.conn.send(arr_update_client_csv)
        logging.info('Disconnected from ' + str(connection.address))
        connection.conn.close()

def checkService(service):
    check_services = "systemctl | grep " + service + " | grep running | wc -l"
    check_services = subprocess.Popen(check_services, shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)
    check_services = check_services.stdout.readlines()
    if int(check_services[0].decode()) == 0:
        return 0
    return 1


if __name__ == "__main__":
    # Services to Check before start.
    services = ['keepup-version-usr', 'keepup-version-maq']
    for service in services:
        try:
            exit_code = checkService(service)
            if exit_code == 0:
                logging.info("Service: " + service + " is not running, trying to start..")
                subprocess.call(["systemctl", "start", service])
                exit_code = checkService(service)
                if exit_code == 0: logging.info("Service [ERR]: " + service)
                else:
                    logging.info("Service [OK]: " + service)
            else:
                logging.info("Service [OK]: " + service)

        except (ValueError, FileNotFoundError):
            print("An error occoured while trying to start " + service + " using systemctl, please CHECK!")

    ThreadedServer().listen()
