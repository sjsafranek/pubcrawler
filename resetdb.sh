find . -name "*.pyc" -exec rm {} \;
rm db.sqlite3

py -3.15 manage.py makemigrations
py -3.15 manage.py migrate

# py -3.15 manage.py create_test_data

py -3.15 manage.py createsuperuser