web: cd backend && python manage.py collectstatic --noinput && python manage.py migrate && gunicorn visitaPro.wsgi:application --bind 0.0.0.0:$PORT
