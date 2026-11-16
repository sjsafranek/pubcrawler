uv python install 3.15
uv run --python 3.15 -m venv pubcrawler
source pubcrawler/bin/activate

pip install django
pip install gunicorn
pip install osmnx

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

source python_environments/pubcrawler/bin/activate
cd webapps/pubcrawler
gunicorn pubcrawler.wsgi:application --bind 0.0.0.0:5002



