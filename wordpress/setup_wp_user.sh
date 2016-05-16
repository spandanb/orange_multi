#!/bin/bash

mysql -uroot << EOF
CREATE DATABASE wordpress;
GRANT ALL PRIVILEGES ON wordpress.* TO 'wordpress'@'%' IDENTIFIED BY "12345";
FLUSH PRIVILEGES;
EOF
