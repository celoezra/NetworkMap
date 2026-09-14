# NetworkMap Enterprise

Sistema corporativo para documentação e gerenciamento de infraestrutura de rede, agora com suporte multi-unidade e autenticação Microsoft Entra ID integrados.

## Stack
*   **Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLCipher (banco criptografado localmente).
*   **Frontend:** React 19, TypeScript, TailwindCSS, Vite.

## Segurança e Autenticação (Microsoft Entra ID)

O NetworkMap Enterprise utiliza a autenticação corporativa via **Microsoft Entra ID (OIDC / OAuth2)**. 

### Variáveis de Ambiente Necessárias (.env)

Crie um arquivo `.env` na raiz do backend ou exporte estas variáveis em seu ambiente:

```env
# Configurações do Azure/Entra ID para Autenticação
AZURE_TENANT_ID="seu-tenant-id"
AZURE_CLIENT_ID="seu-client-id"
AZURE_REDIRECT_URI="http://localhost:3000"

# (Opcional no desenvolvimento, recomendado para produção)
# Define uma chave organizacional padrão para portabilidade de DBs entre instâncias seguras da mesma empresa
ORGANIZATION_DB_KEY="sua-chave-organizacional-secreta"
```

## Primeiro Acesso (SUPERADMIN)

A primeira conta administrativa está vinculada nativamente ao email:
`marcelo.romero@rededor.com.br`

**Fluxo de inicialização:**
1.  Configure as credenciais MSAL.
2.  Acesse o frontend.
3.  Clique em "Entrar com Microsoft" e autentique-se com a conta designada.
4.  O backend criará automaticamente sua identidade no banco de dados e lhe dará a role global de `SUPERADMIN`.
5.  A partir deste ponto, o sistema usará seu `Tenant ID` e `Object ID` permanentemente.

## Controle de Acesso (RBAC) e Multi-Unidade

*   **Novos Usuários:** Após efetuarem o login na Microsoft, o NetworkMap cria o cadastro com o status `PENDING`. O usuário deve aguardar a aprovação de um `SUPERADMIN` ou `ADMIN` autorizado.
*   **Perfis por Unidade:** Usuários podem receber perfis diferentes (ex: `ADMIN`, `TECNICO`, `VISUALIZACAO`) em diferentes unidades através do Painel de Administração.
*   **Filtros de Isolamento:** Os dados no painel e na API são isolados enviando o Header `X-Unit-ID`. O backend valida estritamente o acesso para a unidade requisitada baseando-se nas tabelas `UserUnitAccess`.

## Criptografia do Banco de Dados (SQLCipher)

Os dados são armazenados localmente em `data/networkmap.db` com criptografia transparente AES-256 utilizando SQLCipher.

*A chave nunca é enviada ao frontend ou registrada em logs.*  
Em ambientes de desenvolvimento Linux, ela pode ser gerada e salva em `data/.db_key`. Em produção no Windows, recomenda-se configurar a `app/security/key_manager.py` para injetar credenciais advindas do `DPAPI` ou `Credential Manager`.

### Importação de Bancos (.db)

Para permitir a portabilidade entre instalações da mesma organização, utilize a variável `ORGANIZATION_DB_KEY`.
Arquivos `.db` podem ser enviados via Painel de Administração > **Importar Banco**. 
O sistema mesclará automaticamente o esquema UUID sem substituir a instalação local inteira e sem falhar chaves estrangeiras. Todos os `Racks`, `Switches` e `Localizações` originais serão preservados debaixo de uma Nova Unidade.

## Como Executar

### Backend
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.1 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

> **Aviso:** Nunca versão a chave `data/.db_key` ou arquivos `.db` reais nos repositórios git. O repositório já se encontra pré-configurado com regras de exclusão no `.gitignore`.
