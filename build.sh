# exit on error
set -o errexit

# install project dependencies
#uv sync

# make sure django has all the things it needs to run
#cd $(dirname $(find . | grep manage.py$))
#uv run ./manage.py collectstatic --no-input
# uv run ./manage.py migrate
# uv run ./manage.py createsuperuser --username admin --email "guillermina.tagliavini@gmail.com" --noinput || true    



pip install -r requirements.txt

python manage.py migrate
python manage.py collectstatic --no-input

# Crea el superusuario (opcional, pero buena práctica)
python manage.py createsuperuser --username admin --email "guillermina.tagliavini@gmail.com" --noinput || true