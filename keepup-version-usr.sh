#!/bin/bash
# Sniff for changes on gpo yml files under path directory, when it happens, increment a value for the respective
# line in csv file.
path='/etc/ansible/gpo/usr/'
csv_usr_file='/usr/local/sbin/keepup/keepup-version-usr.csv'

if [[ ! -f $csv_usr_file ]]; then touch ${csv_usr_file}; fi

/usr/bin/inotifywait -m ${path} -e MODIFY,DELETE --exclude swp |
while read path action file; do
    if [[ ${action} == "MODIFY" ]]; then
        if [[ ${file} == *".yml" && ${file} != "fila"* ]]; then
            CURRENT_VERSION=$(cat ${csv_usr_file} | grep ${file} | cut -d "," -f 2)
            if [[ ${CURRENT_VERSION} != "" ]]; then
                    echo ${CURRENT_VERSION}
                    NEW_VERSION=$(($CURRENT_VERSION + 1));
                    sed -i "s|.*$file.*|$file,$NEW_VERSION|" ${csv_usr_file}
            else
                    echo ${file}",1" >> ${csv_usr_file}
        fi
    fi
    elif [[ ${action} == "DELETE" ]]; then
        if [[ ${file} == *".yml" ]]; then
            sed -i "/$file/d" ${csv_usr_file}
        fi
    fi
done
