# CAAFE Analítico — Insegurança Alimentar

MVP Django com três abas: **Tabelas**, **Dashboards** e **Mapa**. O sistema calcula prevalências, IC95% de Wilson, razões de prevalência brutas e regressão de Poisson com variância robusta, além de agregar resultados por escola.

## Arquitetura de dados

1. Um CSV **pseudonimizado e sem identificadores diretos** é armazenado em bucket privado do Supabase Storage.
2. O servidor Django baixa o arquivo usando `SUPABASE_SERVICE_ROLE_KEY` apenas no backend.
3. O conteúdo é validado por SHA-256 e convertido para Parquet com compressão Zstandard.
4. O Parquet e os resultados analíticos são reutilizados pelo cache até vencer o TTL.
5. Em ambiente local sem Supabase, o sistema usa `data/caafe_dashboard.csv`.

Por governança estatística, o modo padrão `CAAFE_MODEL_MODE=validated` mantém os coeficientes inferenciais versionados do relatório técnico, evitando que uma atualização de arquivo altere silenciosamente resultados publicados. Use `live` somente para recalcular e validar uma nova versão.

## Execução local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py refresh_data --force
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

## Supabase

Crie um bucket privado chamado `caafe-data` e envie:

```text
analytics/caafe_dashboard.csv
```

Configure no Render `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET` e `SUPABASE_OBJECT_PATH`. A chave `service_role` nunca deve ir para HTML, JavaScript, GitHub ou cliente móvel.

## Atualização manual

```bash
python manage.py refresh_data --force
python manage.py validate_baseline
```

Também existe `POST /api/atualizar/` com o cabeçalho `X-Refresh-Token`.

## Deploy no Render

1. Suba o projeto para um repositório GitHub privado.
2. No Render, crie um Blueprint usando `render.yaml`.
3. Preencha as variáveis do Supabase.
4. O build instala dependências, coleta estáticos, migra e atualiza o Parquet.

O disco do plano gratuito é efêmero; isso não compromete a fonte, pois o cache é reconstruído a partir do Supabase em cada novo deploy.

## Coordenadas das escolas

O banco original não possui latitude e longitude. O arquivo `data/school_locations.csv` contém coordenadas **provisórias**, marcadas para validação. Antes de qualquer publicação institucional, substitua-as por coordenadas oficiais verificadas.

## Segurança e LGPD

O CSV analítico incluído não contém nome, nome da mãe, telefone, e-mail ou data de nascimento. Não envie o Excel original ao bucket consumido pelo painel.
