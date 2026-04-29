web: cd backend && python manage.py collectstatic --noinput && python manage.py migrate && gunicorn visitas_corporativas.wsgi:application --bind 0.0.0.0:$PORT
