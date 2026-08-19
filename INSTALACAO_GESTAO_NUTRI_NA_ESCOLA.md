# Atualização — Gestão, autenticação, galeria e equipe individual

Esta atualização foi preparada sobre os arquivos atuais enviados em 19/08/2026.

## O que entra nesta versão

- botão **Login** na Home ao lado de **Acessar Sala de Situação**;
- login por e-mail e senha;
- **Esqueci minha senha**;
- **Solicitar acesso**;
- aprovação/recusa de solicitações;
- envio de link individual para criação da primeira senha;
- painel de gestão;
- gerenciador de usuários e perfis;
- desligamento de usuário protegido por uma segunda senha armazenada apenas como hash no ambiente;
- gestão da Galeria de Vivências: criar, editar, arquivar e excluir logicamente;
- gestão individual da equipe: foto, nome, função, apresentação e Currículo Lattes;
- auditoria das ações administrativas;
- upload de fotos novas para um bucket público separado no Supabase Storage;
- PostgreSQL persistente preparado via `DATABASE_URL` para produção;
- conteúdo atual da galeria e nomes atuais da equipe migrados automaticamente para as novas tabelas.

## 1. Aplicar os arquivos

Extraia o ZIP na raiz do projeto `caafe_mvp1`, permitindo substituir os arquivos existentes.

O pacote altera/cria principalmente:

```text
config/settings.py
config/urls.py
institutional/views.py
institutional/templates/institutional/home.html
institutional/static/institutional/css/home.css
gestao/
render.yaml
.env.example
.python-version
.gitattributes
```

## 2. Desenvolvimento local

O SQLite continua funcionando localmente se `DATABASE_URL` estiver ausente ou vazio.

Execute:

```powershell
python manage.py migrate
python manage.py check
```

A migration inicial cria as tabelas da gestão e uma segunda migration converte o conteúdo institucional atual para:

- 3 registros iniciais de Galeria de Vivências;
- membros atuais da equipe em cards individuais.

## 3. Criar o primeiro usuário Desenvolvedor

Execute:

```powershell
python manage.py bootstrap_developer --email jeancarloscustodio0@gmail.com
```

O terminal solicitará a senha sem gravá-la no histórico do comando. Para o teste local solicitado, digite `123456` quando o prompt aparecer.

> Essa senha é somente para desenvolvimento local. Antes de publicar autenticação em produção, altere-a para uma senha forte.

## 4. Criar a senha especial para desligamentos

A senha especial da coordenação **não deve ficar em texto puro no `.env`**.

Execute:

```powershell
python manage.py make_critical_secret_hash
```

Digite a senha da professora duas vezes. O comando imprimirá um hash semelhante a:

```text
pbkdf2_sha256$...
```

No `.env`, coloque somente o hash:

```env
GESTOR_CRITICAL_ACTION_SECRET_HASH=pbkdf2_sha256$...
```

## 5. Testar localmente

```powershell
python manage.py runserver
```

Rotas principais:

```text
/                         Home pública
/gestao/login/            Login
/gestao/solicitar-acesso/ Solicitação de acesso
/gestao/                  Painel de gestão
/gestao/solicitacoes/     Solicitações
/gestao/usuarios/         Usuários
/gestao/galeria/          Galeria
/gestao/equipe/           Equipe
/gestao/auditoria/        Auditoria
```

No desenvolvimento local, enquanto SMTP não estiver configurado, os e-mails de convite e recuperação são impressos no terminal. Assim é possível testar todo o fluxo sem serviço externo de e-mail.

## 6. Bucket de mídia no Supabase

Crie um bucket separado chamado:

```text
saude-alimentar-media
```

Esse bucket deve ser destinado exclusivamente às fotos públicas da Home, com pastas geradas automaticamente:

```text
gallery/
team/
```

Não misture esse bucket com `projeto_saude_alimentar`, que contém os dados científicos.

Sem esse bucket, todo o restante da gestão funciona, mas novos uploads de fotos serão recusados com uma mensagem de configuração.

## 7. PostgreSQL para o Render

Para produção, `DATABASE_URL` deixa de ser opcional. Configure uma conexão PostgreSQL persistente do projeto Supabase.

No Render:

```text
DATABASE_URL=<connection string PostgreSQL>
```

Use a conexão apropriada para servidor/backend indicada pelo Supabase. Depois disso, o `build.sh` já executa:

```text
python manage.py migrate --noinput
```

portanto as tabelas serão criadas automaticamente no banco persistente durante o deploy.

## 8. E-mail de produção

Configure no Render:

```env
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=
```

O sistema usa esses dados para:

- convite após aprovação de acesso;
- cadastro da primeira senha;
- recuperação de senha.

## 9. Variáveis novas no Render

Além das variáveis atuais:

```text
DATABASE_URL
SITE_BASE_URL
SUPABASE_MEDIA_BUCKET
EMAIL_HOST
EMAIL_PORT
EMAIL_USE_TLS
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL
GESTOR_CRITICAL_ACTION_SECRET_HASH
```

O `render.yaml` do pacote já declara as novas variáveis e também corrige o nome do serviço para `saude-alimentar-unb`.

## 10. Git

Depois dos testes locais:

```powershell
git add .
git status
git commit -m "Add site management authentication gallery and team"
git push
```

Nunca versionar:

```text
.env
db.sqlite3
senhas
connection strings
service_role
credenciais SMTP
```

## 11. Antes do deploy final

Rode:

```powershell
python manage.py check
python manage.py test gestao
python manage.py collectstatic --noinput
```

Depois valide localmente o fluxo completo:

```text
Solicitar acesso
→ aprovar como desenvolvedor
→ receber link no terminal/e-mail
→ definir senha
→ login
→ editar galeria
→ cadastrar membro
→ arquivar conteúdo
→ testar desligamento com a senha crítica
```
