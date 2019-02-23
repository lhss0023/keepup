#!/bin/bash

echo "Checking for required repository"
if [ $(cat /etc/apt/sources.list | grep cz.archive.ubuntu.com/ubuntu | wc -l ) == 0 ]; then
	add-apt-repository 'deb http://cz.archive.ubuntu.com/ubuntu trusty main universe'
fi

echo "Installing dependencies packages"
apt-get update && apt-get install -y sshpass inotify-tools ldap-utils software-properties-common python3 python3-setuptools

#echo "Instaling Python Libraries.."
cd libs/setuptools-40.8.0
python3 setup.py install
cd libs/configparser-3.7.1/
python3 setup.py install
cd ../../

echo "Installing Ansible"
if [[ $(dpkg -l | grep ansible | awk '{print $2}') != 'ansible' ]]; then
	apt-add-repository --yes --update ppa:ansible/ansible && apt-get install -y ansible
	sed -i '/^#log_path/s/^#//g' /etc/ansible/ansible.cfg
        sed -i '/^#strategy/s/^#//g' /etc/ansible/ansible.cfg
        sed -i '/^#host_key_checking/s/^#//g' /etc/ansible/ansible.cfg
fi

echo "Creating Directories and Copying Files.."
if [ ! -d /etc/ansible/gpo/usr/files ]; then
	mkdir -p /etc/ansible/gpo/usr/files
fi

if [ ! -d /etc/ansible/gpo/maq/files ]; then
        mkdir -p /etc/ansible/gpo/maq/files
fi

cp systemd/keepup-maq.service /etc/ansible/gpo/maq/files/
cp systemd/keepup-usr.service /etc/ansible/gpo/maq/files/
cp client_app/adjustprofile.sh /etc/ansible/gpo/maq/files/
cp client_app/keepup-usr.py /etc/ansible/gpo/maq/files/
cp client_app/keepup-maq.py /etc/ansible/gpo/maq/files/

if [ ! -d /usr/local/sbin/keepup ] ;then
	mkdir -p /usr/local/sbin/keepup
fi

cp keepup.py /usr/local/sbin/keepup/
cp keepupserver.py /usr/local/sbin/keepup/
cp keepup-version-usr.sh /usr/local/sbin/keepup/
cp keepup-version-maq.sh /usr/local/sbin/keepup/
cp configFile.py /usr/local/sbin/keepup/
cp keepup.cfg /etc/
chmod -R 750 /usr/local/sbin/keepup/*

echo "Configuring KeepUp as a Daemon Service.. and Starting Keepup."
cp systemd/keepup.service /etc/systemd/system/
cp systemd/keepup-version-maq.service /etc/systemd/system/
cp systemd/keepup-version-usr.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable keepup

cp maq_gpo* /etc/ansible/gpo/maq/

echo "############################################################################################

	Instalacao concluida, seguir as instrucoes:

        0. Criar um usuario no seu servidor LDAP para realizar consultas..

        1. Ajustar configuracoes em: /etc/keepup.cfg

        2. CONFIGURE /etc/ansible/gpo/maq/files/keepup-usr.py & keepup-maq.py
                Ajustar as linhas nos dois arquivos:
                        HOST = 'ip_servidor_keepup'
                        PORT = 'porta_servidor_keepup'

        3. Adicionar os clientes linux da sua rede em /etc/ansible/hosts abaixo de [linux-clients]
                Exemplo:
                        [linux-clients]
                        host01
                        host02

        4. CONFIGURAR CHAVE SSH CLIENTE E SERVIDOR
        Voce deve gerar um par de chave ssh como ROOT.
        e copiar a chave publica para cada cliente da rede que usara o app
            Exemplo:
                ssh-keygen -t rsa
            *Pressione enter para todas as perguntas
        Copie o conteudo de /root/.ssh/id_rsa.pub
        Acesse a maquina do cliente, dentro do diretorio /root/.ssh/authorized_keys  e cole o conteudo da chave.
            * Se o client nao tiver ssh deve instalar.
            * se nao existir a estrutura de pasta e arquivo, criar com mkdir e touch.
        Feito isso so salvar e sair.

        6. Verificar se o servidor acessa o cliente sem pedir senha (Use root):
                Exemplo:
                :# ssh root@host01
                :# Talvez precise digitar yes apenas..

        7.Iniciando:
                systemctl start keepup

        8. Para instalar nos clientes configurados em [linux-clients] Rode:
                ansible-playbook /etc/ansible/gpo/maq_gpo_configure_client.yml

        9. Verificar Log:
                tail /var/log/keepup.log

     \############################################################################################## "


