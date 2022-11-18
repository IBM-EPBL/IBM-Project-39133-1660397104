import ibm_db

email = 'bala.abinesh.surya@gmail.com'
password = 'lwksbcjtupsyjalj'
connection_string = ibm_db.connect('DATABASE=bludb;HOSTNAME=2f3279a5-73d1-4859-88f0-a6c3e6b4b907.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=30756;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=tdn81266;PWD=fWbJoZBoxQPpz8Ux', '', '')

