# Q-HomeDir-Create
Sample script to create homedirs on Qumulo Cluster

Usage :<BR>
./HomedirCreate.py -u \<username\> -q \<quota\>
	
options :<BR>
	
	-u / --username=    Username to setup homedir for
	
	-q / --quota=   Quota Limit to define on the homedir (50M, 50G, 50T, 50P) / optional
	
 
This script will connect to Qumulo cluster API using informations from credentials.json<BR>	
  !!! be careful as login and password is stored as plaintext in credentials.json
  
It will then :<BR>
	
	- Create the homedir of the user
	
	- Change owner to defined variable homedir_owner (you should prefer using a group than a single user)
	
	- Setup ACLs on this homedir :
		- using the variable homedir_owner to setup an ACE with Full Control, inherited and heritable
		- using variable username to setup an ACE will all rights except "Change permissions" and "Change owner"
	
	-Create a quota for this directory:
		- if quota is not passed through the command, will use the default value in variable default_quota_size
		- if passed through the command, will use this value
		- if a quota is already defined on this directory, it won't be updated
  
# Requires
	
	- qumulo_api
	
