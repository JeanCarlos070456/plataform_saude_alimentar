"""Conteúdo editorial inicial da página institucional.

Este arquivo concentra textos e metadados que ainda não estão no banco de dados.
Quando a equipe finalizar biografias, links e autorizações, o conteúdo pode ser
migrado para modelos administráveis pelo Django Admin sem alterar o template.
"""

PROJECT_AREAS = [
    {
        "title": "Consumo alimentar",
        "icon": "plate",
        "text": (
            "Registro dos alimentos consumidos no dia anterior, distribuídos entre "
            "café da manhã, lanches, almoço, jantar e ceia."
        ),
    },
    {
        "title": "Estado nutricional",
        "icon": "measure",
        "text": (
            "Avaliação de peso, altura e Índice de Massa Corporal por idade, conforme "
            "referências de crescimento para crianças e adolescentes."
        ),
    },
    {
        "title": "Atividade física",
        "icon": "activity",
        "text": (
            "Mapeamento de brincadeiras, esportes, educação física e deslocamentos "
            "realizados pelos estudantes ao longo do dia."
        ),
    },
    {
        "title": "Uso de telas",
        "icon": "screen",
        "text": (
            "Identificação de comportamentos sedentários relacionados à televisão, "
            "celular, computador e videogame."
        ),
    },
    {
        "title": "Insegurança alimentar",
        "icon": "home",
        "text": (
            "Triagem das dificuldades familiares para manter alimentos suficientes "
            "e variados no domicílio."
        ),
    },
]

METHOD_STEPS = [
    {
        "number": "01",
        "title": "Autorização das famílias",
        "text": (
            "Pais ou responsáveis recebem as informações da pesquisa, autorizam a "
            "participação e respondem ao questionário socioeconômico."
        ),
    },
    {
        "number": "02",
        "title": "Concordância do estudante",
        "text": (
            "Os escolares conhecem os procedimentos e manifestam sua concordância "
            "por meio do Termo de Assentimento."
        ),
    },
    {
        "number": "03",
        "title": "Avaliação antropométrica",
        "text": (
            "Uma equipe treinada realiza medidas de peso e altura em ambiente "
            "adequado e com proteção da privacidade."
        ),
    },
    {
        "number": "04",
        "title": "Aplicação do Web-CAAFE",
        "text": (
            "É um sistema que monitora o estado nutricional, consumo alimentar e atividade física do dia anterior. Os estudantes respondem ao questionário digital em computadores ou tablets, com apoio de imagens e recursos sonoros."
        ),
    },
    {
        "number": "05",
        "title": "Análise e devolutiva",
        "text": (
            "Os dados são qualificados, analisados de forma agregada e transformados "
            "em relatórios, indicadores, gráficos e mapas."
        ),
    },
]

TEAM_GROUPS = [
    {
        "title": "Coordenação",
        "subtitle": "Coordenação geral e coordenação de campo",
        "image": "institutional/img/team/equipe-coordenacao.webp",
        "members": [
            "Patrícia de Fragas Hinnig — coordenação geral",
            "Viviane Belini Rodrigues — coordenação geral",
            "Adriano Gomes — coordenação de campo",
        ],
    },
    {
        "title": "Residentes",
        "subtitle": "Atenção Básica — UnB/HUB — Nutrição",
        "image": "institutional/img/team/equipe-residentes.webp",
        "members": ["Clara Mota", "Jéssica Celestino"],
    },
    {
        "title": "Bolsistas",
        "subtitle": "Pesquisa, análise e apoio de campo",
        "image": "institutional/img/team/equipe-bolsistas.webp",
        "members": [
            "Mayara — mestre em Nutrição",
            "Jean Carlos — sanitarista",
            "Ana Salomão — sanitarista",
        ],
    },
    {
        "title": "Graduandos",
        "subtitle": "Nutrição e Educação Física — UnB",
        "image": "institutional/img/team/equipe-graduandos-1.webp",
        "members": ["Isadora", "Marianne", "Juliana", "Bárbara"],
    },
    {
        "title": "Graduandos",
        "subtitle": "Nutrição — UnB",
        "image": "institutional/img/team/equipe-graduandos-2.webp",
        "members": ["Mariana", "Vitor Gabriell", "Raquel", "Ashley"],
    },
    {
        "title": "Graduandos",
        "subtitle": "Nutrição — UnB",
        "image": None,
        "members": ["Lívia", "Leonardo", "Anna Clara", "Layane"],
    },
]

EXPERIENCES = [
    {
        "title": "Promoção da alimentação saudável nas escolas",
        "image": "institutional/img/experiences/vivencia-seminario.webp",
        "alt": (
            "Integrantes da equipe em evento sobre promoção da alimentação saudável "
            "nas escolas do Distrito Federal"
        ),
        "meta": "Seminário técnico-científico · 2025",
        "text": (
            "Participação da equipe em espaço de diálogo sobre alimentação saudável, "
            "saúde escolar e políticas públicas no Distrito Federal."
        ),
    },
    {
        "title": "Vivência em ambiente escolar",
        "image": "institutional/img/experiences/vivencia-campo.webp",
        "alt": "Equipe do projeto durante atividade em escola",
        "meta": "Atividade de campo",
        "text": (
            "Organização dos equipamentos e aproximação com a comunidade escolar para "
            "apresentação e execução das etapas da pesquisa."
        ),
    },
    {
        "title": "Divulgação científica",
        "image": "institutional/img/experiences/vivencia-congresso.webp",
        "alt": "Pesquisadoras ao lado de pôster científico apresentado em evento",
        "meta": "Evento acadêmico",
        "text": (
            "Compartilhamento de métodos, resultados e experiências do projeto com a "
            "comunidade acadêmica e profissionais da área."
        ),
    },
]