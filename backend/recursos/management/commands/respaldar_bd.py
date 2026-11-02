from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
from datetime import datetime


class Command(BaseCommand):
    help = "Genera un respaldo de la base de datos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Ruta del archivo de salida (opcional)",
        )

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        engine = db["ENGINE"]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ejemplo para PostgreSQL
        if "postgresql" in engine:
            output = options["output"] or f"backup_{timestamp}.sql"
            cmd = [
                "pg_dump",
                "-U", db["USER"],
                "-h", db.get("HOST", "localhost"),
                "-p", str(db.get("PORT", 5432)),
                "-F", "c",
                "-f", output,
                db["NAME"],
            ]
            env = os.environ.copy()
            env["PGPASSWORD"] = db["PASSWORD"]
            subprocess.run(cmd, check=True, env=env)
            self.stdout.write(self.style.SUCCESS(f"Respaldo creado: {output}"))

        # Ejemplo para SQLite
        elif "sqlite3" in engine:
            import shutil
            src = db["NAME"]
            output = options["output"] or f"backup_{timestamp}.sqlite3"
            shutil.copy2(src, output)
            self.stdout.write(self.style.SUCCESS(f"Respaldo creado: {output}"))

        else:
            self.stderr.write(f"Motor no soportado: {engine}")