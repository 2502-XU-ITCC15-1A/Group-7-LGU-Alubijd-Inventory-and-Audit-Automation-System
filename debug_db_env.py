import os
from dotenv import load_dotenv
load_dotenv()
print('cwd=' + os.getcwd())
print('MYSQL_HOST=' + str(os.getenv('MYSQL_HOST')))
print('MYSQL_USER=' + str(os.getenv('MYSQL_USER')))
print('MYSQL_PASSWORD=' + str(os.getenv('MYSQL_PASSWORD')))
print('MYSQL_DB=' + str(os.getenv('MYSQL_DB')))
