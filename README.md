# AmparaPet — Back-end

Sistema de adoção de animais do **Abrigo Toca de Assis** (Ivaiporã - PR).
Projeto Integrador — Análise e Desenvolvimento de Sistemas, UNIVALE 2026.

| Camada | Tecnologia |
|--------|------------|
| Back-end | **Python 3.13** portátil (dentro da pasta) com **FastAPI**, uma API REST que responde em JSON |
| Banco de dados | **MySQL 8.4** portátil, dentro da própria pasta do projeto, sem instalação |
| Interface de teste | HTML + JavaScript simples em `frontend-teste/`, só para testar a API |
| Front-end oficial | Feito à parte, por outra pessoa da equipe. Ele consome esta API. |

---

## Sumário

1. [Início rápido](#1-início-rápido)
2. [O que foi feito](#2-o-que-foi-feito)
3. [Como o MySQL e o Python portáteis funcionam](#3-como-o-mysql-e-o-python-portáteis-funcionam)
4. [Painel de controle e arquivos .bat](#4-painel-de-controle-e-arquivos-bat)
5. [Outras formas de rodar (VS Code e terminal)](#5-outras-formas-de-rodar-vs-code-e-terminal)
6. [Banco de dados](#6-banco-de-dados)
7. [Guia da API para o front-end](#7-guia-da-api-para-o-front-end)
8. [Decisões técnicas](#8-decisões-técnicas)
9. [Testes automatizados](#9-testes-automatizados)
10. [Configuração e produção](#10-configuração-e-produção)
11. [Estrutura de pastas](#11-estrutura-de-pastas)
12. [Problemas comuns](#12-problemas-comuns)

---

## 1. Início rápido

**Não é preciso instalar nada:** nem Python, nem MySQL, nem XAMPP, nem Visual C++. Também não precisa de internet nem de permissão de administrador. Tudo o que o sistema usa está dentro da pasta. Funciona em qualquer Windows 10 ou 11 de 64 bits, a partir de qualquer pasta (seção 4, "Mover ou copiar o projeto").

1. Dê dois cliques em **`AmparaPet.exe`** (o painel de controle) e clique em **▶ Iniciar**. Em poucos segundos o navegador abre sozinho na interface de teste.
   Quem preferir pode usar o **`iniciar.bat`**, que faz a mesma coisa sem o painel.
2. Com o sistema ligado, acesse:
   - **Interface de teste:** http://localhost:8000/teste/
   - **Documentação da API (Swagger):** http://localhost:8000/docs
3. Entre na área administrativa com `admin@amparapet.local` / `trocar123`. Esses dados vêm do `.env`; **troque a senha** depois do primeiro login.
4. Para desligar tudo, clique em **■ Parar** no painel (ou dê dois cliques em **`parar.bat`**).

Para popular o banco com 6 animais de exemplo (com fotos geradas automaticamente), rode isto com o banco ligado e ainda sem animais:

```bash
cd backend && ..\python\python -m app.init_db --exemplos
```

---

## 2. O que foi feito

Tudo foi implementado a partir da documentação do Projeto Integrador (RF01–RF14 e RNF01–RNF11).

### Requisitos funcionais

| Requisito | Como foi implementado |
|-----------|-----------------------|
| **RF01** Cadastro de animais | `POST /api/admin/animais`. Além dos campos pedidos, foram incluídos **sexo**, **vacinas detalhadas** e **necessidades especiais**. Espécie: Cão/Gato. Porte: Pequeno/Médio/Grande. A idade é guardada como **data de nascimento aproximada** e calculada automaticamente ("2 anos e 3 meses"), então nunca fica desatualizada. |
| **RF02** Vitrine pública | `GET /api/animais`, sem login. Mostra só animais Disponíveis e Em processo, com paginação. |
| **RF03** Página do animal | `GET /api/animais/{id}`, com todos os dados, as fotos e os links prontos. |
| **RF04** Fotos | Envio de várias fotos de uma vez (JPG, PNG ou WEBP, até 5 MB cada), remoção e reordenação. O servidor confere se o arquivo é mesmo uma imagem, corrige a rotação de fotos de celular, converte para WEBP comprimido (máx. 1600 px) e gera uma **miniatura** de 400 px. A pré-visualização antes de enviar é feita no navegador. |
| **RF05** Filtros | Espécie, porte, sexo, castrado, vacinado, status e busca por nome, raça ou cor. |
| **RF06** Interesse | Botão "Tenho interesse" abre o WhatsApp do abrigo com uma mensagem pronta citando o nome e o código do animal. Cada clique é **contado** (sem coletar dados pessoais) e aparece no painel. |
| **RF07** Área administrativa | Login por e-mail e senha, logout, sessão com validade de 8 horas e bloqueio das rotas para quem não está logado. Vários administradores, todos com o mesmo nível. |
| **RF08** Status | Disponível, Em processo e Adotado. Adotados somem da vitrine mas continuam salvos. Toda mudança fica no **histórico**, com data, autor e observação, e o animal pode ser reativado. |
| **RF09** Edição e exclusão | Todos os campos são editáveis. A exclusão é definitiva e apaga também fotos e histórico. A confirmação "tem certeza?" fica no front-end. |
| **RF10** Armazenamento | MySQL, com datas de cadastro e de atualização em todos os registros. |
| **RF11** Compartilhamento | A API devolve o link da página do animal (para copiar) e um link de compartilhamento pelo WhatsApp. |
| **RF12 / RF13** Como adotar e endereço | Endereço, horários, WhatsApp, passo a passo e documentos exigidos ficam no banco e são **editáveis pela área administrativa**, sem mexer no código. |
| **RF14** Painel | Total de animais, disponíveis, em processo, adotados, cliques de interesse e os 5 animais mais procurados. |

### Requisitos não funcionais atendidos pelo back-end

| Requisito | Como |
|-----------|------|
| **RNF04** Desempenho | Fotos comprimidas em WEBP com miniaturas, índices nos campos usados nos filtros e paginação na vitrine. |
| **RNF05** Segurança | Senhas com **bcrypt**; no banco, os tokens de sessão ficam só como hash; bloqueio de 15 minutos após 5 erros de login; logout encerra a sessão na hora; validação de todos os dados recebidos. O HTTPS fica a cargo da hospedagem. |
| **RNF06** Manutenibilidade | Código separado por responsabilidade (rotas, regras, banco, segurança, imagens), testes automatizados e esta documentação. |
| **RNF07** Qualidade das imagens | Redimensionamento sem distorção (mantém a proporção) e miniaturas otimizadas. |
| **RNF11** Tempo de resposta | Consultas indexadas e fotos servidas diretamente como arquivos estáticos. |

RNF01–RNF03 e RNF08–RNF10 (usabilidade, responsividade, acessibilidade, SEO) dependem do **front-end oficial**.

### Entregas

- API completa, com documentação interativa (Swagger) em `/docs`, que atende ao item "Documentar endpoints da API" do checklist;
- banco MySQL portátil e scripts para ligar, desligar, testar e abrir o console;
- documentação do banco com DER e dicionário de dados em [`docs/banco-de-dados.md`](docs/banco-de-dados.md), que atende ao item "MER/DER" do checklist;
- 17 testes automatizados cobrindo os requisitos;
- **painel de controle** (`AmparaPet.exe`), um programa de janela para ligar, desligar e administrar o sistema sem usar os `.bat`;
- interface de teste simples (vitrine, página do animal, "como adotar" e área administrativa completa).

---

## 3. Como o MySQL e o Python portáteis funcionam

O projeto carrega dentro da própria pasta os dois programas de que precisa: o **MySQL** (pasta `mysql/`) e o **Python** (pasta `python/`). Assim ele roda em qualquer PC com Windows 64 bits, sem instalar nada.

### MySQL portátil

O MySQL normalmente é instalado no Windows como um **serviço** que liga junto com o computador. Aqui foi usada a versão **ZIP "sem instalador"** oficial da Oracle (MySQL Community 8.4.13 LTS), que roda direto de uma pasta. Por isso:

- não precisa de instalação nem de permissão de administrador;
- não entra em conflito com outro MySQL, XAMPP ou WAMP que já exista na máquina;
- a pasta do projeto pode ser copiada para outro computador ou pendrive e continua funcionando;
- o MySQL só roda quando você manda (pelo `iniciar.bat`) e para quando você manda (pelo `parar.bat`).

#### O que fica dentro de `mysql/`

```
mysql/
  server/      programas do MySQL (mysqld.exe, mysql.exe, mysqldump.exe...)
  data/        os DADOS do banco (tabelas, registros). Criada na primeira execução.
  my.ini       configuração, gerada automaticamente a cada execução
  mysql.log    log do servidor (consulte se o banco não ligar)
```

#### Passo a passo do que o script `scripts/banco.ps1` faz

Os `.bat` chamam este script. Ele faz o seguinte:

1. **Baixa o MySQL, se precisar.** Se `mysql/server/` não existir (por exemplo, logo depois de clonar o repositório do GitHub), baixa o ZIP oficial de `cdn.mysql.com` e confere a integridade pelo MD5 publicado pela Oracle. Depois extrai o ZIP e apaga os arquivos de depuração (`.pdb`), o que reduz a pasta de ~1,2 GB para ~420 MB.
2. **Gera o `my.ini`** com os caminhos da pasta atual. Como o arquivo é refeito toda vez, o projeto pode mudar de lugar (outro disco, outro computador) sem quebrar. Configurações principais:
   - `port=3307`, para não brigar com um MySQL "normal", que usa a 3306;
   - `bind-address=127.0.0.1`, para aceitar só conexões do próprio computador (ninguém na rede consegue acessar);
   - `character-set-server=utf8mb4`, para acentos e emojis.
3. **Na primeira vez**, roda `mysqld --initialize-insecure`, que cria a pasta `data/` com as tabelas internas do MySQL e um usuário `root` **sem senha**. Como o servidor só aceita conexões locais, isso é aceitável para desenvolvimento.
4. **Liga o servidor** (`mysqld.exe`) em segundo plano, numa janela oculta, e espera ele responder na porta 3307.
5. **Na primeira vez**, também cria:
   - o banco `amparapet` (dados do sistema);
   - o banco `amparapet_teste` (usado só pelos testes automatizados);
   - o usuário `amparapet` com a senha `amparapet`, que tem acesso só a esses dois bancos. A API usa esse usuário, nunca o `root`.

As **tabelas** do sistema (animais, fotos etc.) não são criadas pelo script. A API as cria sozinha quando sobe, junto com o administrador inicial e os dados padrão do abrigo.

Para **desligar**, o script envia o comando `mysqladmin shutdown`, que encerra o MySQL corretamente, salvando tudo. Não é preciso matar o processo.

#### Bibliotecas do Visual C++ embutidas

O MySQL para Windows depende de três arquivos do **Microsoft Visual C++ Redistributable** (`msvcp140.dll`, `vcruntime140.dll` e `vcruntime140_1.dll`). Muitos PCs já têm esse pacote, mas um Windows recém-formatado normalmente não tem, e aí o MySQL nem abre. Por isso, uma cópia desses três arquivos fica em `mysql/server/bin/`, ao lado do `mysqld.exe`. O Windows sempre procura primeiro na pasta do programa, então o MySQL usa essa cópia. A Microsoft permite distribuir esses arquivos junto com programas (é a chamada instalação "app-local").

### Python portátil

Foi usado o pacote oficial **"Windows embeddable package"** do python.org (Python 3.13.17, 64 bits): um Python completo que roda de uma pasta e não mexe no Windows (não altera o PATH nem o registro). Ele já traz os próprios arquivos do Visual C++.

```
python/
  python.exe                o Python
  python313._pth            configuração: avisa o Python para usar Lib\site-packages
  Lib/site-packages/        bibliotecas do back-end (FastAPI, SQLAlchemy, Pillow...)
```

O script `scripts/python.ps1` cuida dele:

1. **Se a pasta `python/` não existir**, por exemplo num clone do GitHub, baixa o pacote do python.org, ativa o uso de bibliotecas no `python313._pth` e instala o `pip`. Isso exige internet.
2. **Confere se as bibliotecas estão instaladas**, importando as principais. Se faltar alguma, instala as de `backend/requirements.txt`. Na pasta pronta, essa checagem leva menos de 1 segundo.

Os `.bat`, o VS Code e os testes sempre usam `python\python.exe`. Um Python instalado no Windows, se houver, é ignorado.

### Por que `mysql/` e `python/` não vão para o GitHub

São ~420 MB e ~120 MB de programas, além dos dados locais de cada pessoa. As duas pastas estão no `.gitignore`. Quem **clonar** o repositório roda o `iniciar.bat` e os scripts baixam o MySQL e o Python sozinhos. Só nesse caso é preciso internet. Quem recebe a **pasta copiada** (pendrive, ZIP) já recebe tudo pronto.

---

## 4. Painel de controle e arquivos .bat

Há duas formas equivalentes de ligar e desligar o sistema: o **painel de controle** (`AmparaPet.exe`), uma janela com botões, e os **arquivos `.bat`**. Os dois usam os mesmos scripts por baixo (`scripts\*.ps1`), então dá para misturar: ligar pelo painel e desligar pelo `parar.bat`, por exemplo.

### Painel de controle (`AmparaPet.exe`)

Dê dois cliques em **`AmparaPet.exe`**, na pasta principal do projeto. Ele mostra:

- **Situação**, atualizada a cada 1,5 s: o banco de dados (MySQL, porta 3307) e a API (http://localhost:8000) aparecem como ● Ligado ou ● Desligado. Se o sistema foi ligado por um `.bat`, o painel também mostra como ligado.
- **Sistema:**
  - **▶ Iniciar:** faz o mesmo que o `iniciar.bat`. Roda as checagens (64 bits, caminho, desbloqueio, porta), confere o Python portátil, liga o MySQL e a API e abre o navegador, se a opção "Abrir o navegador ao iniciar" estiver marcada.
  - **■ Parar:** faz o mesmo que o `parar.bat`, desligando a API e o MySQL.
  - **Abrir site de teste** e **Documentação da API:** abrem o navegador nas páginas certas. Só ficam ativos com a API ligada.
- **Ferramentas:**
  - **Rodar testes:** faz o mesmo que o `testar.bat`. Os 17 testes rodam no banco separado `amparapet_teste` e o resultado aparece no registro.
  - **Console do MySQL:** faz o mesmo que o `mysql.bat`. Liga o banco, se precisar, e abre o console SQL em outra janela.
  - **Reinstalar bibliotecas:** faz o mesmo que o `instalar.bat` (precisa de internet).
  - **Abrir pasta** e **Log do MySQL:** atalhos para a pasta do projeto e para o arquivo `mysql\mysql.log`.
- **Registro:** a área escura embaixo mostra tudo o que está acontecendo, inclusive as mensagens da API, como cada acesso ao site e possíveis erros.

Detalhes:

- **Ao fechar o painel com o sistema ligado**, ele pergunta se deve desligar tudo antes. **Sim** desliga e fecha. **Não** fecha só o painel e o sistema continua no ar. Para desligar depois, abra o painel de novo ou use o `parar.bat`.
- Só abre **um painel por vez**. Se ele já estiver aberto, aparece um aviso.
- As mensagens da API também ficam gravadas em `logs\api.log`. É por isso que a API continua funcionando mesmo depois que o painel é fechado.
- O painel liga a API **sem** o `--reload`, ou seja, ela não reinicia sozinha ao editar arquivos `.py`. Para desenvolver alterando o código, use o `iniciar.bat` ou o VS Code (seção 5).
- O `AmparaPet.exe` precisa ficar na **pasta principal** do projeto, junto dos `.bat`. Para ter um atalho na Área de Trabalho, clique com o botão direito nele → "Enviar para" → "Área de trabalho (criar atalho)".

#### Como o painel foi feito

O painel é um programa **C# com Windows Forms**. Foi escolhido porque o compilador C# e as bibliotecas de janela do **.NET Framework 4** já vêm em todo Windows 10 e 11, então ele roda em qualquer PC sem instalar nada, como o resto do projeto. O Python portátil não serve para isso, porque não inclui a biblioteca de janelas (tkinter).

| Arquivo | Função |
|---------|--------|
| `AmparaPet.exe` | O painel pronto (~60 KB) |
| `scripts\painel\Painel.cs` | Código-fonte do painel |
| `scripts\painel\amparapet.ico` | Ícone (pata), gerado por `scripts\painel\gerar_icone.py` |
| `scripts\compilar_painel.ps1` | Compila o `Painel.cs` e gera o `AmparaPet.exe` |

Para alterar o painel, edite o `Painel.cs` e compile de novo com o comando abaixo. O compilador do Windows aceita só **C# 5**, então não use recursos mais novos, como `$"texto {variavel}"` ou `?.`.

```bash
powershell -ExecutionPolicy Bypass -File scripts\compilar_painel.ps1
```

### Arquivos .bat

#### Por que existem

Para acessar o `localhost:8000`, **dois programas** precisam estar rodando:

1. o **MySQL** (`mysqld.exe`), que guarda os dados;
2. a **API** (`uvicorn`, o servidor web do Python), que responde no `localhost:8000`.

Sem os `.bat`, seria preciso abrir um editor como o VS Code, ativar o ambiente Python, ligar o MySQL e digitar o comando do servidor no terminal. Os `.bat` fazem tudo isso com dois cliques, sem precisar de nenhum editor aberto. Assim, qualquer pessoa da equipe, ou o próprio abrigo, consegue rodar.

#### O que cada um faz

| Arquivo | O que faz, passo a passo |
|---------|--------------------------|
| **`iniciar.bat`** | 1. **Checagens** (`scripts\preparar.ps1`): confere se o Windows é 64 bits e se o caminho da pasta não é longo demais, **desbloqueia** os arquivos (quando a pasta vem de um ZIP baixado, o Windows marca os programas como "da internet" e pode travá-los) e confere se a porta 8000 está livre. 2. Confere o Python portátil e as bibliotecas (`scripts\python.ps1`). 3. Se não existir o `.env`, copia o `.env.example`. 4. Liga o MySQL (`scripts\banco.ps1 iniciar`). 5. Abre o navegador em http://localhost:8000/teste/ e sobe a API com `uvicorn --reload`. **A janela preta é a API**: enquanto ela estiver aberta, o site funciona. Com `--reload`, a API reinicia sozinha quando um arquivo `.py` é alterado. Se algo der errado, a janela para e mostra o motivo. |
| **`parar.bat`** | 1. Encerra a API (`scripts\api.ps1 parar`): procura os processos Python rodando `app.main:app` e os fecha, junto com os processos filhos. 2. Desliga o MySQL corretamente (`scripts\banco.ps1 parar`). |
| **`instalar.bat`** | Reinstala as bibliotecas de `backend\requirements.txt` no Python portátil. Não é usado no dia a dia; rode só quando mudar o `requirements.txt`. Precisa de internet. |
| **`testar.bat`** | Liga o MySQL, se estiver desligado, e roda os 17 testes automatizados no banco `amparapet_teste`, sem tocar nos dados reais. |
| **`mysql.bat`** | Abre o console SQL do MySQL já conectado ao banco `amparapet`, para rodar comandos como `SELECT * FROM animais;`. Digite `exit` para sair. |

#### Detalhes importantes

- **Fechar a janela do `iniciar.bat`** (ou apertar Ctrl+C nela) para **só a API**. O MySQL continua ligado em segundo plano. Para desligar os dois, use o **`parar.bat`**.
- **Se o localhost abre mas dá erro**, a API está rodando mas o MySQL está desligado. Rode o `iniciar.bat` de novo, que liga o que estiver faltando, ou o `parar.bat` para desligar tudo.
- Rodar o `iniciar.bat` com o MySQL já ligado não causa problema: o script percebe e só avisa "MySQL ja esta rodando".
- Os `.bat` chamam scripts PowerShell com `-ExecutionPolicy Bypass`. Isso libera **apenas aquele script**, sem mudar nenhuma configuração do Windows.
- Os `.bat` sempre entram na pasta onde estão (`pushd "%~dp0"`). Por isso funcionam com dois cliques, pelo terminal, por atalho e até a partir de uma pasta de rede.
- Para não abrir o navegador automaticamente, defina a variável de ambiente `AMPARAPET_SEM_NAVEGADOR=1`.

### Mover ou copiar o projeto

A pasta roda **em qualquer diretório e em qualquer PC com Windows 10 ou 11 de 64 bits**, inclusive com espaços ou acentos no caminho (ex.: `C:\Users\Você\Documentos\Projeto Integrador\AMPARAPET`). Nenhum arquivo do projeto guarda o caminho da pasta: os scripts descobrem onde estão a cada execução e o `my.ini` do MySQL é gerado de novo toda vez.

Teste feito: a pasta foi copiada para um caminho com espaços e acentos, os arquivos foram marcados como "baixados da internet" (como num ZIP) e o `iniciar.bat` foi rodado sem nenhum Python no PATH. O sistema subiu em ~5 segundos. O MySQL carregou as DLLs do Visual C++ da própria pasta e a API rodou no Python portátil.

- **Para outro lugar ou outro computador** (pendrive, ZIP, rede): rode o `parar.bat`, copie a pasta **inteira** e rode o `iniciar.bat` no destino. Os dados e as fotos vão junto. Não precisa de internet.
- O tamanho total é de ~740 MB (MySQL ~420 MB, dados do banco ~190 MB, Python ~125 MB).
- O caminho da pasta deve ter **no máximo ~140 caracteres**, por um limite do Windows. Qualquer pasta comum, como Documentos ou Área de Trabalho, serve; o `iniciar.bat` avisa se passar disso.
- **Evite pastas sincronizadas** (OneDrive, Google Drive, Dropbox) enquanto o sistema estiver ligado: a sincronização pode mexer nos arquivos do banco no meio do uso.
- **Nunca copie a pasta com o MySQL ligado.** Os arquivos de `mysql\data\` podem ser copiados pela metade. Sempre rode o `parar.bat` antes.
- Só pode rodar **uma cópia por vez**, porque todas usam as mesmas portas (3307 e 8000).

---

## 5. Outras formas de rodar (VS Code e terminal)

Os `.bat` são a forma mais simples, mas não a única. Quem preferir trabalhar no editor tem estas opções.

### Pelo VS Code

O projeto já vem com a pasta `.vscode/` configurada. Abra a **pasta `AMPARAPET`** inteira no VS Code (Arquivo → Abrir Pasta) e instale a extensão **Python**, da Microsoft.

- **F5 (Executar e Depurar)** → "AmparaPet: API (depurar)": liga o MySQL e sobe a API com o **depurador**, permitindo usar breakpoints. Para parar, use o botão vermelho do depurador. O MySQL continua ligado; desligue pela tarefa "parar tudo" ou pelo `parar.bat`.
- **Terminal → Executar Tarefa...**, com as tarefas prontas:
  - `AmparaPet: iniciar tudo (igual ao iniciar.bat)`
  - `AmparaPet: iniciar banco`
  - `AmparaPet: parar tudo (API + banco)`
  - `AmparaPet: rodar testes`
- A aba **Testes** (ícone de frasco) também encontra e roda os testes.
- O Python portátil (`python\python.exe`) já vem selecionado (`.vscode/settings.json`).

### Pelo terminal (qualquer editor)

```bash
powershell -ExecutionPolicy Bypass -File scripts\banco.ps1 iniciar
```

```bash
cd backend && ..\python\python -m uvicorn app.main:app --reload --port 8000
```

O primeiro comando liga o MySQL. O segundo sobe a API, que fica rodando até Ctrl+C. O `banco.ps1` também aceita `parar`, `status` e `console`.

### Usando outro MySQL (XAMPP, instalado, nuvem)

O MySQL portátil é só uma conveniência. Para usar outro, crie o banco e o usuário nele e altere `DATABASE_URL` no `.env`. Por exemplo, para o XAMPP na porta 3306:

```
DATABASE_URL=mysql+pymysql://usuario:senha@127.0.0.1:3306/amparapet?charset=utf8mb4
```

As tabelas são criadas automaticamente na primeira vez que a API sobe.

---

## 6. Banco de dados

**Documentação completa, com DER, dicionário de dados, relacionamentos e regras: [`docs/banco-de-dados.md`](docs/banco-de-dados.md)**

![DER](docs/der.png)

| Tabela | Conteúdo |
|--------|----------|
| `animais` | Dados dos animais, status e contador de cliques em "tenho interesse" |
| `fotos` | Fotos de cada animal; a de menor `ordem` é a principal |
| `historico_status` | Toda mudança de status, com data, usuário e observação |
| `usuarios` | Administradores (senha com bcrypt) |
| `sessoes` | Sessões de login ativas (só o hash do token) |
| `tentativas_login` | Registro de logins, usado para bloquear após 5 erros seguidos |
| `configuracoes` | Dados do abrigo editáveis: endereço, horários, WhatsApp, textos |

| Acesso | Valor |
|--------|-------|
| Servidor | `127.0.0.1`, porta **3307** |
| Banco | `amparapet` |
| Usuário / senha | `amparapet` / `amparapet` (o `root` não tem senha e só acessa localmente) |

Também dá para abrir o banco em programas como o MySQL Workbench, o DBeaver ou o HeidiSQL com esses dados, desde que o MySQL esteja ligado.

- **Zerar tudo:** `parar.bat`, apague as pastas `mysql\data\` e `uploads\` e rode o `iniciar.bat`.
- **Backup:** veja a seção "Operação" em [`docs/banco-de-dados.md`](docs/banco-de-dados.md#6-operação).

---

## 7. Guia da API para o front-end

A documentação completa, com todos os campos, exemplos e o botão "Try it out" para testar, está em **http://localhost:8000/docs**.

### Rotas públicas (sem login)

| Método | Rota | Uso |
|--------|------|-----|
| GET  | `/api/animais` | Vitrine. Filtros: `especie`, `porte` (pode repetir), `sexo`, `castrado`, `vacinado`, `status`, `busca`, `pagina`, `por_pagina`. Adotados nunca aparecem. |
| GET  | `/api/animais/{id}` | Página do animal, com `fotos` e `links` (página, WhatsApp de interesse, compartilhar) |
| POST | `/api/animais/{id}/interesse` | Conta o clique e devolve `whatsapp_url` para abrir |
| GET  | `/api/abrigo` | Endereço, horários, WhatsApp, "como adotar", documentos |
| GET  | `/api/opcoes` | Valores aceitos (CAO, GATO, PEQUENO...) com rótulos em português |

### Rotas administrativas

Faça `POST /api/auth/login` com `{"email": "...", "senha": "..."}` e envie o `token` recebido em todas as chamadas seguintes, no cabeçalho:

```
Authorization: Bearer <token>
```

Uma resposta **401** significa que a sessão expirou: mande o usuário para a tela de login.

| Método | Rota | Uso |
|--------|------|-----|
| POST   | `/api/auth/logout` | Sair |
| GET    | `/api/auth/eu` | Usuário logado |
| PUT    | `/api/auth/senha` | Trocar a própria senha |
| GET    | `/api/admin/painel` | Totais (RF14) |
| GET/POST | `/api/admin/animais` | Listar todos (inclusive adotados) / cadastrar |
| GET/PATCH/DELETE | `/api/admin/animais/{id}` | Ver / editar (só os campos enviados) / excluir |
| PATCH  | `/api/admin/animais/{id}/status` | `{"status": "ADOTADO", "observacao": "..."}`. Para reativar, volte para `DISPONIVEL`. |
| GET    | `/api/admin/animais/{id}/historico` | Histórico de status |
| POST   | `/api/admin/animais/{id}/fotos` | `multipart/form-data`, campo `fotos` (pode repetir). JPG, PNG ou WEBP de até 5 MB cada. |
| PUT    | `/api/admin/animais/{id}/fotos/ordem` | `{"ids": [3, 1, 2]}`. A primeira vira a principal. |
| DELETE | `/api/admin/fotos/{id}` | Remover foto |
| GET/PUT | `/api/admin/abrigo` | Dados do abrigo |
| GET/POST/PATCH/DELETE | `/api/admin/usuarios` | Administradores |

### Observações

- **Idade:** envie `data_nascimento` aproximada (`AAAA-MM-01` se só souber mês/ano). A API devolve `idade` já em texto.
- **Fotos:** use `miniatura_url` na vitrine e `url` na página do animal.
- **Exclusão:** é definitiva. Peça confirmação ao usuário antes de chamar o `DELETE`.
- **Links do WhatsApp e de compartilhamento:** são montados com o campo `url_pagina_animal` dos dados do abrigo (com `{id}`). Quando o front-end oficial estiver no ar, ajuste esse campo na área administrativa para o endereço real, por exemplo `https://amparapet.com/animal.html?id={id}`.
- **WhatsApp do abrigo:** enquanto o número não for preenchido na área administrativa, `whatsapp_interesse` vem `null`.
- **Exemplo de código:** a interface de teste (`frontend-teste/`) mostra como chamar cada rota em JavaScript puro. O arquivo `comum.js` tem a função `api()`, que já envia o token.

---

## 8. Decisões técnicas

| Decisão | Motivo |
|---------|--------|
| **FastAPI** como framework | Gera a documentação Swagger automaticamente e valida os dados de entrada. É simples para uma API JSON consumida por um front-end separado. |
| **SQLAlchemy** para acessar o banco | As tabelas são definidas em Python (`models.py`) e criadas automaticamente. Também protege contra SQL injection. |
| **Sessões com token guardado no banco**, em vez de JWT | Permite logout de verdade e permite derrubar as sessões de um usuário desativado na hora. |
| **Fotos em arquivos**, só o caminho no banco | Mantém o banco leve e as fotos são servidas direto pelo servidor web, o que é mais rápido. |
| **Conversão para WEBP** | Arquivos bem menores que JPG/PNG com a mesma qualidade (RNF04). |
| **Data de nascimento** em vez de idade | A idade se atualiza sozinha. |
| **Contador de cliques**, sem formulário de interesse | Não coleta dados pessoais (LGPD) e o contato continua pelo WhatsApp, como o abrigo pediu. |
| **Dados do abrigo em tabela chave-valor** | O endereço e o WhatsApp do abrigo ainda não estavam definidos; o abrigo pode editá-los sem programador. |
| **Valores fixos (ENUM) sem acento** (`CAO`, `MEDIO`) | Evitam diferença de grafia entre front-end e banco. Os rótulos com acento vêm de `/api/opcoes`. |

---

## 9. Testes automatizados

```bash
testar.bat
```

São 17 testes em `backend/tests/` (pytest). Eles cobrem login e bloqueio, cadastro e validações, status e histórico, upload (formatos, tamanho, miniatura, ordem), filtros, links do WhatsApp, painel, dados do abrigo e gerenciamento de administradores. Os testes usam o banco **`amparapet_teste`** e uma pasta temporária para as fotos, então os dados reais não são tocados.

---

## 10. Configuração e produção

As configurações ficam no arquivo `.env`, criado automaticamente a partir do [`.env.example`](.env.example). O `.env` **não vai para o GitHub**, porque contém senhas.

| Variável | Para que serve |
|----------|----------------|
| `DATABASE_URL` | Conexão com o MySQL |
| `DATABASE_URL_TESTE` | Banco usado pelos testes |
| `CORS_ORIGENS` | Endereços do front-end autorizados a chamar a API (`*` = qualquer um) |
| `ADMIN_INICIAL_*` | Administrador criado quando o banco está vazio |
| `SESSAO_HORAS` | Validade do login |
| `LOGIN_MAX_TENTATIVAS` / `LOGIN_BLOQUEIO_MINUTOS` | Bloqueio por senha errada |
| `SERVIR_INTERFACE_TESTE` | `1` mostra a interface de teste em `/teste` |

Para publicar (Render, Railway etc.):

- `DATABASE_URL` apontando para o MySQL hospedado;
- `ADMIN_INICIAL_SENHA` forte;
- `CORS_ORIGENS` com o endereço do front-end, em vez de `*`;
- `SERVIR_INTERFACE_TESTE=0`;
- HTTPS (RNF05), que já vem incluído no Render e no Railway;
- comando de início: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers`, rodado dentro da pasta `backend`;
- a pasta de fotos (`UPLOAD_DIR`) precisa ficar num disco persistente.

---

## 11. Estrutura de pastas

```
AMPARAPET/
├── AmparaPet.exe       painel de controle (seção 4)
├── iniciar.bat / parar.bat / instalar.bat / testar.bat / mysql.bat   atalhos (seção 4)
├── .env.example        modelo das configurações (.env é gerado a partir dele)
├── backend/
│   ├── requirements.txt    bibliotecas Python, com versões fixas
│   ├── app/
│   │   ├── main.py         cria a API, CORS e arquivos estáticos
│   │   ├── config.py       lê o .env
│   │   ├── database.py     conexão com o MySQL
│   │   ├── models.py       tabelas do banco
│   │   ├── schemas.py      formato e validação dos dados de entrada/saída
│   │   ├── servicos.py     regras de negócio (idade, links do WhatsApp, histórico, dados do abrigo)
│   │   ├── security.py     senhas, sessões e bloqueio de tentativas
│   │   ├── imagens.py      validação, compressão e miniaturas das fotos
│   │   ├── init_db.py      cria tabelas, admin inicial e animais de exemplo
│   │   └── routers/        rotas: publico.py, auth.py, admin.py, usuarios.py
│   └── tests/              testes automatizados
├── frontend-teste/     páginas HTML simples para testar a API
├── docs/               documentação do banco, DER (png/svg) e schema.sql
├── scripts/
│   ├── preparar.ps1    checagens do iniciar.bat (64 bits, caminho, desbloqueio, porta)
│   ├── python.ps1      confere/baixa o Python portátil e as bibliotecas (seção 3)
│   ├── banco.ps1       liga/desliga/baixa o MySQL portátil (seção 3)
│   ├── api.ps1         desliga a API
│   ├── compilar_painel.ps1  gera o AmparaPet.exe
│   ├── painel/         código-fonte (Painel.cs) e ícone do painel
│   └── gerar_der.py    gera a imagem do DER
├── .vscode/            configuração pronta do VS Code (seção 5)
├── python/             Python 3.13 portátil + bibliotecas (fora do Git)
├── mysql/              MySQL portátil, DLLs do Visual C++ e dados (fora do Git)
├── uploads/            fotos enviadas (fora do Git)
└── logs/               mensagens da API quando ligada pelo painel (fora do Git)
```

---

## 12. Problemas comuns

| Sintoma | Causa provável e solução |
|---------|--------------------------|
| `localhost:8000` não abre | A API não está rodando. Rode o `iniciar.bat` e deixe a janela aberta. |
| A página abre mas dá **erro** (500) ou não carrega os animais | O MySQL está desligado. Rode o `iniciar.bat` de novo. |
| "O caminho da pasta e muito longo" | Mova a pasta para um lugar mais curto, como `C:\AMPARAPET` ou Documentos. |
| "MySQL nao subiu" | Veja as últimas linhas de `mysql\mysql.log`. Se mencionar porta em uso, outro programa está usando a 3307: feche-o ou troque a porta em `scripts\banco.ps1` e no `.env`. |
| "Falta msvcp140.dll" | As DLLs do Visual C++ foram apagadas de `mysql\server\bin\` e o Windows também não as tem. Copie a pasta de novo ou instale o "Microsoft Visual C++ Redistributable x64". |
| "A porta 8000 esta sendo usada por outro programa" | Feche o programa indicado na mensagem e rode o `iniciar.bat` de novo. |
| O Windows mostra "O Windows protegeu o computador" ao abrir o `AmparaPet.exe` | Acontece quando a pasta veio de um ZIP baixado da internet, porque o programa não tem assinatura digital. Clique em **Mais informações → Executar assim mesmo**. Isso só é preciso uma vez. Outra opção é usar o `iniciar.bat`. |
| "O painel do AmparaPet já está aberto" | Ele já está aberto, talvez minimizado ou atrás de outra janela. Procure na barra de tarefas. |
| "Não encontrei os arquivos do projeto" (painel) | O `AmparaPet.exe` foi tirado da pasta do projeto. Ele precisa ficar na pasta principal; para ter um atalho em outro lugar, use "Criar atalho". |
| Mudei o código e o painel não reiniciou a API | O painel não usa `--reload`. Clique em Parar e Iniciar, ou use o `iniciar.bat` para desenvolver. |
| "A API ja esta rodando" | Ela está aberta em outra janela. Use essa janela ou rode o `parar.bat` e depois o `iniciar.bat`. |
| O antivírus bloqueia o `mysqld.exe` ou o `python.exe` | São os programas oficiais da Oracle e do python.org. Libere a pasta `AMPARAPET` no antivírus. |
| Um clone do GitHub pede internet na primeira vez | É esperado: `python/` e `mysql/` não vão para o Git e são baixados uma vez (seção 3). |
| Esqueci a senha do admin | Rode `mysql.bat` e execute `DELETE FROM usuarios;`. Ao reiniciar a API, o admin do `.env` é recriado. Isso apaga **todos** os administradores. |
| Mudei uma coluna em `models.py` e nada aconteceu | A API só cria tabelas que não existem. Aplique um `ALTER TABLE` ou zere o banco (seção 6). |
