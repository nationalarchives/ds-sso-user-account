import datetime
import os
import subprocess
from shlex import quote

from invoke import run as local
from invoke.tasks import task

# Process .env file
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f.readlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            var, value = line.strip().split("=", 1)
            os.environ.setdefault(var, value)

FRONTEND = os.getenv("FRONTEND", "docker")

PROJECT_DIR = "/app"
LOCAL_DUMP_DIR = "database_dumps"

DEVELOPMENT_APP_INSTANCE = "tna-account-management-poc"

LOCAL_MEDIA_DIR = "media"
LOCAL_DATABASE_NAME = PROJECT_NAME = "tna_account_management"
LOCAL_DATABASE_USERNAME = "tna_account_management"


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def container_exec(cmd, container_name="web", check_returncode=False):
    result = subprocess.run(
        ["docker-compose", "exec", "-T", container_name, "bash", "-c", cmd]
    )
    if check_returncode:
        result.check_returncode()
    return result


def db_exec(cmd, check_returncode=False):
    "Execute something in the 'db' Docker container."
    return container_exec(cmd, "db", check_returncode)


def web_exec(cmd, check_returncode=False):
    "Execute something in the 'web' Docker container."
    return container_exec(cmd, "web", check_returncode)


@task
def run_management_command(c, cmd, check_returncode=False):
    """
    Run a Django management command in the 'web' Docker container
    with access to Django and other Python dependencies.
    """
    return web_exec(f"poetry run python manage.py {cmd}", check_returncode)

############
# Production
############

@task
def build(c):
    """
    Build the development environment (call this first)
    """
    directories_to_init = [LOCAL_DUMP_DIR, LOCAL_MEDIA_DIR]
    directories_arg = " ".join(directories_to_init)

    group = subprocess.check_output(["id", "-gn"], encoding="utf-8").strip()
    local("mkdir -p " + directories_arg)
    local("chown -R $USER:{} {}".format(group, directories_arg))
    local("chmod -R 775 " + directories_arg)

    local("docker-compose pull")
    local("docker-compose build")


@task
def start(c, container_name=None):
    """
    Start the local development environment.
    """
    cmd = "docker-compose"
    if container_name:
        cmd += f" up {container_name} -d"
    elif FRONTEND != "local":
        cmd += f" -f docker-compose.yml -f docker/docker-compose-frontend.yml up -d"
    local(cmd)


@task
def stop(c, container_name=None):
    """
    Stop the development environment
    """
    cmd = "docker-compose stop"
    if container_name:
        cmd += f" {container_name}"
    local(cmd)


@task
def restart(c):
    """
    Restart the development environment
    """
    stop(c)
    start(c)


@task
def destroy(c):
    """
    Destroy development environment containers (database will lost!)
    """
    local("docker-compose down")


@task
def sh(c, service="web"):
    """
    Run bash in a local container
    """
    subprocess.run(["docker-compose", "exec", service, "bash"])


@task
def psql(c, command=None):
    """
    Connect to the local postgres DB using psql
    """
    cmd_list = [
        "docker-compose",
        "exec",
        "db",
        "psql",
        *["-d", LOCAL_DATABASE_NAME],
        *["-U", LOCAL_DATABASE_USERNAME],
    ]
    if command:
        cmd_list.extend(["-c", command])

    subprocess.run(cmd_list)


def delete_db(c):
    db_exec(
        f"dropdb --if-exists --host db --username={LOCAL_DATABASE_USERNAME} {LOCAL_DATABASE_NAME}"
    )
    db_exec(
        f"createdb --host db --username={LOCAL_DATABASE_USERNAME} {LOCAL_DATABASE_NAME}"
    )


@task
def import_data(c, database_filename):
    """
    Import local data file to the db container.
    """
    # Copy the data file to the db container
    # Import the database file to the db container
    db_exec(
        "pg_restore --clean --no-acl --if-exists --no-owner --host db \
            --username={project_name} -d {database_name} {database_filename}".format(
            project_name=PROJECT_NAME,
            database_name=LOCAL_DATABASE_NAME,
            database_filename=database_filename,
        ),
        service="db",
    )
    delete_db(c)
    print(
        "Any superuser accounts you previously created locally will have been wiped and will need to be recreated."
    )


def db_dump(c, filename):
    """Snapshot the database, files will be stored in the db container"""
    if not filename.endswith(".psql"):
        filename += ".psql"
    db_exec(
        f"pg_dump -d {LOCAL_DATABASE_NAME} -U {LOCAL_DATABASE_USERNAME} > {filename}"
    )
    print(f"Database dumped to: {filename}")


@task
def db_restore(c, filename, delete_dump_on_success=False, delete_dump_on_error=False):
    """Restore the database from a snapshot in the db container"""
    print("Stopping 'web' to sever DB connection")
    stop(c, "web")
    if not filename.endswith(".psql"):
        filename += ".psql"
    delete_db(c)

    try:
        print(f"Restoring datbase from: {filename}")
        db_exec(
            f"psql -d {LOCAL_DATABASE_NAME} -U {LOCAL_DATABASE_USERNAME} < {filename}",
            check_returncode=True,
        )
    except subprocess.CalledProcessError:
        if delete_dump_on_error:
            db_exec(f"rm {filename}")
        raise

    if delete_dump_on_success:
        print(f"Deleting dump file: {filename}")
        db_exec(f"rm {filename}")

    start(c, "web")


#############
# Development
#############

@task
def pull_dev_data(c):
    """Pull database from development Heroku Postgres"""
    pull_database_from_heroku(c, DEVELOPMENT_APP_INSTANCE)


@task
def dev_shell(c):
    """Spin up a one-time Heroku development dyno and connect to shell"""
    open_heroku_shell(c, DEVELOPMENT_APP_INSTANCE)


def delete_local_database(c, local_database_name=LOCAL_DATABASE_NAME):
    local(
        "dropdb --if-exists {database_name}".format(database_name=local_database_name)
    )


########
# Heroku
########

def pull_database_from_heroku(c, app_instance):
    datestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    local(
        "heroku pg:backups:download --output={dump_folder}/{datestamp}.dump --app {app}".format(
            app=app_instance, dump_folder=LOCAL_DUMP_DIR, datestamp=datestamp
        ),
    )

    import_data(c, f"/app/{LOCAL_DUMP_DIR}/{datestamp}.dump")

    local(
        "rm {dump_folder}/{datestamp}.dump".format(
            dump_folder=LOCAL_DUMP_DIR,
            datestamp=datestamp,
        ),
    )


def open_heroku_shell(c, app_instance, shell_command="bash"):
    subprocess.call(
        [
            "heroku",
            "run",
            shell_command,
            "-a",
            app_instance,
        ]
    )


#######
# Utils
#######

def delete_db(c):
    db_exec(
        f"dropdb --if-exists --host db --username={LOCAL_DATABASE_USERNAME} {LOCAL_DATABASE_NAME}"
    )
    db_exec(
        f"createdb --host db --username={LOCAL_DATABASE_USERNAME} {LOCAL_DATABASE_NAME}"
    )


@task
def db_dump(c, filename):
    """Snapshot the database, files will be stored in the db container"""
    if not filename.endswith(".psql"):
        filename += ".psql"
    db_exec(
        f"pg_dump -d {LOCAL_DATABASE_NAME} -U {LOCAL_DATABASE_USERNAME} > {filename}"
    )
    print(f"Database dumped to: {filename}")


@task
def db_restore(c, filename, delete_dump_on_success=False, delete_dump_on_error=False):
    """Restore the database from a snapshot in the db container"""
    print("Stopping 'web' to sever DB connection")
    stop(c, "web")
    if not filename.endswith(".psql"):
        filename += ".psql"
    delete_db(c)

    try:
        print(f"Restoring datbase from: {filename}")
        db_exec(
            f"psql -d {LOCAL_DATABASE_NAME} -U {LOCAL_DATABASE_USERNAME} < {filename}",
            check_returncode=True,
        )
    except subprocess.CalledProcessError:
        if delete_dump_on_error:
            db_exec(f"rm {filename}")
        raise

    if delete_dump_on_success:
        print(f"Deleting dump file: {filename}")
        db_exec(f"rm {filename}")

    start(c, "web")


@task
def test(c, lint=False, parallel=False):
    """
    Run python tests in the web container
    """
    start(c, "web")
    if lint:
        print("Checking isort compliance...")
        web_exec("isort tna_account_management config --check --diff")
        print("Checking Black compliance...")
        web_exec("black tna_account_management config --check --diff --color --fast")
        print("Checking flake8 compliance...")
        web_exec("flake8 tna_account_management config")
        print("Running Django tests...")
    cmd = "python manage.py test --settings=tna_account_management.settings.test"
    if parallel:
        cmd += " --parallel"
    web_exec(cmd)


@task
def migrate(c):
    """
    Run database migrations
    """
    subprocess.run(["docker-compose", "run", "--rm", "web", "./manage.py", "migrate"])
