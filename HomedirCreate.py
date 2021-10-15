#!/usr/bin/python
__Author__ = "Vincent Lamy"
__version__ = "2021.1015"

import sys

from q_functions import *
# Default values
username = ''
quota_size = ''
default_quota_size = 50000000000
src_path = '/Lab-Q/HomeDir/'
homedir_owner = 'q-admins'


# Logging Details
logging.basicConfig(filename='Q-HomedirCreate.log', level=logging.INFO,
                    format='%(asctime)s,%(levelname)s,%(message)s')
# Get command arguments
argv = sys.argv[1:]



try:
      opts, args = getopt.getopt(argv,"hu:q:",["help","user=","quota="])
except getopt.GetoptError:
      print ('{} -u <username> -q <quota>'.format(sys.argv[0]))
      print('-u / --username=    Username to setup homedir for')
      print('-q / --quota=   Quota Limit to define on the homedir (50M, 50G, 50T, 50P/ optional ')
      sys.exit(2)
print(opts)
for opt, arg in opts:
      if opt in ("-h", "--help"):
         print ('{} -u <username> -q <quota>'.format(sys.argv[0]))
         print('-u / --username=    Username to setup homedir for')
         print('-q / --quota=   Quota Limit to define on the homedir (50M, 50G, 50T, 50P) / optional ')
         sys.exit(0)
      elif opt in ("-u", "--username"):
         username = arg
      elif opt in ("-q", "--quota"):
         quota_size = arg


if username == '':
    print('Username must be provided')
    print('{} -u <username> -q <quota>'.format(sys.argv[0]))
    print('-u / --username=    Username to setup homedir for')
    print('-q / --quota=   Quota Limit to define on the homedir (50M, 50G, 50T, 50P) / optional ')
    sys.exit(1)


if quota_size == '':
    quota_size = default_quota_size
else:
    # Check if quota unit is supported
    unit = quota_size[-1]
    if unit in ("M", "G", "T", "P"):
        quota_size = convert_quota_size(quota_size,logging)
    else:
        print('Quota unit provided is no support : {}'.format(quota_size))
        print('{} -u <username> -q <quota>'.format(sys.argv[0]))
        print('-u / --username=    Username to setup homedir for')
        print('-q / --quota=   Quota Limit to define on the homedir (50M, 50G, 50T, 50P) / optional ')
        sys.exit(1)

# Build the homedir path
homedir_path = src_path+username+'/'

# Read credentials
json_file = open('./credentials.json', 'r')
json_data = json_file.read()
json_object = json.loads(json_data)
json_file.close()

# Parse cluster credentials
primary_cluster_address = json_object['primary_cluster_address']
primary_port_number = json_object['primary_port_number']
primary_username = json_object['primary_username']
primary_password = json_object['primary_password']

# Connect to cluster
try:
    prc = RestClient(primary_cluster_address, primary_port_number)
    prc.login(primary_username, primary_password)
    logging.info('main,Connection established with {}'.format(primary_cluster_address))
    print('Connection established with {}'.format(primary_cluster_address))
except Exception as err:
    logging.error('main,Connection cannot be established with {}'.format(primary_cluster_address))
    logging.error(
        'Error message is {}'.format(err.__dict__))
    logging.info('main,Ending program now')
    quit()

# Check if user exists on Active Directory through Qumulo cluster - exit if user do no exist
# User attributes such as auth_id are stored in ad_user for futur use in this script
try:
    ad_user = prc.auth.find_identity(domain='ACTIVE_DIRECTORY',name=username)
    logging.info('main,User {} exists on Active Directory and its auth_id is {}'.format(ad_user['name'],
                                                                                        ad_user['auth_id']))
    print('User {} exists on Active Directory and its auth_id is {}'.format(ad_user['name'],ad_user['auth_id']))
except Exception as err:
    error = err.__dict__
    logging.error('main,User {} does not exists on the Active Directory'.format(username))
    logging.error('main,Error description is : {}'.format(error['description']))
    logging.info('main,Exiting program now')
    print('User {} does not exists on the Active Directory'.format(username))
    print('Error description is : {}'.format(error['description']))
    print('Exiting program now')
    prc.close()
    logging.info('main,Connection ended with {}'.format(primary_cluster_address))
    print('Connection ended with {}'.format(primary_cluster_address))
    quit(1)

# Create directory on the cluster
try:
    created_dir = prc.fs.create_directory(username,src_path)
    logging.info('main,Directory {} has been created on the cluster'.format(created_dir['path']))
    print('Directory {} has been created on the cluster'.format(created_dir['path']))
except Exception as err:
    error = err.__dict__
    if error['error_class'] == 'fs_entry_exists_error':
        logging.warning('main,Directory {}{} already exists on this cluster'.format(src_path,username))
        print('Directory {}{} already exists on this cluster'.format(src_path,username))

# Modify the owner of this directory - must be user / group in homedir_owner
try:
    homdir_ad_owner = prc.auth.find_identity(domain='ACTIVE_DIRECTORY', name=homedir_owner)
    chg_own = prc.fs.set_file_attr(path=homedir_path,owner=homdir_ad_owner['auth_id'])
    logging.info('main,Owner of directory {} is now {}'.format(chg_own['path'],homdir_ad_owner['name']))
    print('Owner of directory {} is now {}'.format(chg_own['path'],homdir_ad_owner['name']))
except Exception as err:
    error = err.__dict__
    logging.error('main,Error when trying to change owner of directory {} with {}'.format(chg_own['path'],
                                                                                          ad_user['name']))
    logging.error('main,Error message is {}'.format(err.__dict__))
    print('Error when trying to change owner of directory {} with {}'.format(chg_own['path'],
                                                                             ad_user['name']))
    print('Error message is {}'.format(err.__dict__))

# Set ACL for user on its homedir - Full control with heritance

# Generate JSON object for ACLs
json_acl = gen_json_acl(username,homedir_owner)

# Update ACLs on user homedir
try:
    upd_acl = prc.fs.set_acl_v2(acl=json_acl,path=homedir_path)
    logging.info('main,ACLs updated for directory {}'.format(homedir_path))
    print('ACLs updated for directory {}'.format(homedir_path))
except Exception as err:
    error = err.__dict__
    print('Error when trying to update ACLs on directory {}'.format(homedir_path))
    print('Error message is {}'.format(err.__dict__))
    logging.error('main,Error when trying to update ACLs on directory {}'.format(homedir_path))
    logging.error('main,Error message is {}'.format(err.__dict__))

# Create a quota for the homedir
try:
    # Get Directory ID on the filesystem (mandatory for setting quota on it)
    homedir_attr = prc.fs.get_file_attr(path=homedir_path)
    homedir_quota = prc.quota.create_quota(homedir_attr['id'],quota_size)
    logging.info('main,Quota has been set for directory {} - limit is {} bytes'.format(homedir_path,quota_size))
    print('Quota has been set for directory {} - limit is {} bytes'.format(homedir_path,quota_size))
except Exception as err:
    error = err.__dict__
    logging.error('main, Quota can not be set for directory {}'.format(homedir_path))
    logging.error('main, Error description is : {}'.format(error['description']))
    print('Quota can not be set for directory {}'.format(homedir_path))
    print('Error description is : {}'.format(error['description']))

prc.close()
logging.info('main,Connection ended with {}'.format(primary_cluster_address))
print('Connection ended with {}'.format(primary_cluster_address))





