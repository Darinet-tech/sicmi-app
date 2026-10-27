from django.db import migrations

GRUPOS = [
    'Cimentaciones',
    'Muros, tabiques y cerramientos',
    'Cubiertas',
    'Carpintería',
    'Pisos',
    'Revestimientos (salpicado, resano, fino y estuco)',
    'Enchapes',
    'Falso techo',
    'Muebles sanitarios',
    'Redes sanitarias y pluviales',
    'Redes hidráulicas, equipos y accesorios',
    'Redes eléctricas, equipos y accesorios',
    'Impermeabilización',
    'Estructuras metálicas',
    'Pintura (paredes, techo, carpintería y otros elementos)',
    'Cercas, rampas y escaleras',
    'Cisternas, fosas y depósitos',
    'Herrería, rejas y barandas',
    'Áreas verdes',
    'Aceras y viales',
]


def cargar(apps, schema_editor):
    GrupoGenerico = apps.get_model('catalogos', 'GrupoGenerico')
    for i, nombre in enumerate(GRUPOS, start=1):
        GrupoGenerico.objects.get_or_create(numero=i, defaults={'nombre': nombre})


def borrar(apps, schema_editor):
    GrupoGenerico = apps.get_model('catalogos', 'GrupoGenerico')
    GrupoGenerico.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cargar, borrar),
    ]