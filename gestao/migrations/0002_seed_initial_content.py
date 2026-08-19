from django.db import migrations


GALLERY = [
    {
        "title": "Promoção da alimentação saudável nas escolas",
        "eyebrow": "Seminário técnico-científico · 2025",
        "summary": "Participação da equipe em espaço de diálogo sobre alimentação saudável, saúde escolar e políticas públicas no Distrito Federal.",
        "static_image": "institutional/img/experiences/vivencia-seminario.webp",
        "sort_order": 10,
    },
    {
        "title": "Vivência em ambiente escolar",
        "eyebrow": "Atividade de campo",
        "summary": "Organização dos equipamentos e aproximação com a comunidade escolar para apresentação e execução das etapas da pesquisa.",
        "static_image": "institutional/img/experiences/vivencia-campo.webp",
        "sort_order": 20,
    },
    {
        "title": "Divulgação científica",
        "eyebrow": "Evento acadêmico",
        "summary": "Compartilhamento de métodos, resultados e experiências do projeto com a comunidade acadêmica e profissionais da área.",
        "static_image": "institutional/img/experiences/vivencia-congresso.webp",
        "sort_order": 30,
    },
]

TEAM = [
    ("Patrícia de Fragas Hinnig", "Coordenação geral", 10),
    ("Viviane Belini Rodrigues", "Coordenação geral", 20),
    ("Adriano Gomes", "Coordenação de campo", 30),
    ("Clara Mota", "Residente — Atenção Básica UnB/HUB — Nutrição", 40),
    ("Jéssica Celestino", "Residente — Atenção Básica UnB/HUB — Nutrição", 50),
    ("Mayara", "Bolsista — mestre em Nutrição", 60),
    ("Jean Carlos", "Bolsista — sanitarista", 70),
    ("Ana Salomão", "Bolsista — sanitarista", 80),
    ("Isadora", "Graduanda — Nutrição e Educação Física — UnB", 90),
    ("Marianne", "Graduanda — Nutrição e Educação Física — UnB", 100),
    ("Juliana", "Graduanda — Nutrição e Educação Física — UnB", 110),
    ("Bárbara", "Graduanda — Nutrição e Educação Física — UnB", 120),
    ("Mariana", "Graduanda — Nutrição — UnB", 130),
    ("Vitor Gabriell", "Graduando — Nutrição — UnB", 140),
    ("Raquel", "Graduanda — Nutrição — UnB", 150),
    ("Ashley", "Graduanda — Nutrição — UnB", 160),
    ("Lívia", "Graduanda — Nutrição — UnB", 170),
    ("Leonardo", "Graduando — Nutrição — UnB", 180),
    ("Anna Clara", "Graduanda — Nutrição — UnB", 190),
    ("Layane", "Graduanda — Nutrição — UnB", 200),
]


def seed(apps, schema_editor):
    GalleryItem = apps.get_model("gestao", "GalleryItem")
    TeamMember = apps.get_model("gestao", "TeamMember")

    if not GalleryItem.objects.exists():
        for row in GALLERY:
            GalleryItem.objects.create(**row)

    if not TeamMember.objects.exists():
        for full_name, role, sort_order in TEAM:
            TeamMember.objects.create(
                full_name=full_name,
                role=role,
                sort_order=sort_order,
            )


def unseed(apps, schema_editor):
    GalleryItem = apps.get_model("gestao", "GalleryItem")
    TeamMember = apps.get_model("gestao", "TeamMember")
    GalleryItem.objects.filter(title__in=[item["title"] for item in GALLERY]).delete()
    TeamMember.objects.filter(full_name__in=[item[0] for item in TEAM]).delete()


class Migration(migrations.Migration):
    dependencies = [("gestao", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
