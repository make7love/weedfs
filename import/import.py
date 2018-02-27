#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import urllib2
import sys
import time
import subprocess
import json
import re

reload(sys)
sys.setdefaultencoding('utf-8')

def get_timestamp():
	return time.strftime("%Y-%m-%d %H:%M:%S" , time.localtime())
	
def send_error(msg):
	print "[ Error ] %s - %s" % (get_timestamp() , msg)

def shell_command(cmd):
	exec_cmd = subprocess.Popen(cmd , shell=True , stdout=subprocess.PIPE , stderr = subprocess.STDOUT)
	exec_rt , exec_err = exec_cmd.communicate()
	if exec_err is None:
		return exec_rt.strip()
	else:
		send_error("%s - command execute error!" % cmd)
		sys.exit(1)		

def get_upload_url(vd):
	if not weed_ip:
		send_error("global variable weed_ip is empty!")
		sys.exit(1)
		
	curl_string = "http://%s:9333/dir/lookup?volumeId=%d" % (weed_ip , vd)
	req = urllib2.urlopen(curl_string).read()
	if not req:
		send_error("request volueId error!")
		sys.exit(1)
	n = json.loads(req)
	u = n['locations'][0]['url']
	if not u:
		print n
		send_error("parse json error!")
		sys.exit(1)
		
	return "http://%s" % u
	
def weedfs_upload_file(img_file,img_name , img_vid):
	upload_url = get_upload_url(img_vid)
	file_dir = os.path.dirname(img_file)
	os.chdir(file_dir)
	upload_cmd = "curl -s -X PUT -F \"fileUpload=@\\\"%s\\\"\" %s/%s" % (img_name , upload_url , img_name)
	print ""
	u_c = shell_command(upload_cmd)
	print u_c
	
	
sql_conf = "/usr/local/sunlight/conf/server.conf"
current_dir = os.path.split(os.path.realpath(__file__))[0]
image_dir = "%s/images" % current_dir


if not os.path.isdir(image_dir):
	send_error("%s not found." % image_dir)
	sys.exit(1)
	
if not os.listdir(image_dir):
	send_error("%s is empty!" % image_dir)
	sys.exit(1)
	
if not os.path.exists(sql_conf):
	send_error("%s not found" % sql_conf)
	sys.exit(1)
	
conf_dict = {}
with open(sql_conf ,"r") as sqlconfig:
	for line in sqlconfig:
		(k , v) = line.strip().split("=")
		conf_dict[k] = v
		
if not conf_dict:
	send_error("config is empty!")
	sys.exit(1)

if not conf_dict['dbpass'] or not conf_dict['dbhost'] or not conf_dict['dbuser'] or not conf_dict['dbport'] :
	send_error("dbpass or dbhost or dbuser is empty! please check!")
	sys.exit(1)
	
query_sql="\"use cdb20;select paramvalue from systemparameters where paramname='seaweedfs_ip';\""
query_command = "mysql -h%s -P%s -u%s -p%s -e %s" % (conf_dict['dbhost'] , conf_dict['dbport'] , conf_dict['dbuser'], conf_dict['dbpass'] ,query_sql)
query_result = shell_command(query_command)
weed_ip = query_result.split("\n")[1]
if not weed_ip:
    send_error("myql query error! weed_ip is empty!")
	sys.exit(1)

if not re.match("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$" , weed_ip):
	send_error("weed_ip read from mysql is error!")
	sys.exit(1)

for d in os.listdir(image_dir):
		image_file = os.path.join(image_dir , d)
		image_file_volumeId = int(d.split(",")[0])
		if os.path.isfile(image_file) and image_file_volumeId:
			weedfs_upload_file(image_file , d ,image_file_volumeId)
			
			