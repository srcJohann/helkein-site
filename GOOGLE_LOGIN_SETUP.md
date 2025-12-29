# Configuração do Login com Google (OAuth2)

Este documento descreve os passos necessários para configurar a autenticação via Google no projeto Helkein Site.

## 1. Criar Projeto no Google Cloud Console

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um novo projeto ou selecione um existente.
3. No menu lateral, vá em **APIs e Serviços** > **Tela de permissão OAuth**.
4. Selecione **Externo** e clique em **Criar**.
5. Preencha as informações obrigatórias (Nome do App, E-mail de suporte, etc.) e salve.

## 2. Criar Credenciais

1. No menu lateral, vá em **APIs e Serviços** > **Credenciais**.
2. Clique em **+ CRIAR CREDENCIAIS** e selecione **ID do cliente OAuth**.
3. Em **Tipo de aplicativo**, selecione **Aplicativo da Web**.
4. Dê um nome para o cliente (ex: "Helkein Local").

## 3. Configurar URIs (Importante!)

Esta é a parte mais crítica para o funcionamento do `django-allauth`.

### Origens JavaScript autorizadas
Adicione a URL base do seu site.
* **Desenvolvimento:** `http://127.0.0.1:8000` (e `http://localhost:8000` se usar)
* **Produção:** `https://helkein.com.br` (ou seu domínio final)

### URIs de redirecionamento autorizados
O `django-allauth` usa um endpoint específico para o callback.
* **Desenvolvimento:** 
  ```
  http://127.0.0.1:8000/accounts/google/login/callback/
  ```
* **Produção:**
  ```
  https://helkein.com.br/accounts/google/login/callback/
  ```

> **Nota:** Se você estiver usando `localhost` em vez de `127.0.0.1`, certifique-se de adicionar ambos ou usar consistentemente um deles. O Django e o Google são sensíveis a essa diferença.

## 4. Configurar Variáveis de Ambiente

Após criar as credenciais, você receberá um **ID do cliente** e uma **Chave secreta do cliente**. Adicione-os ao seu arquivo `.env` na raiz do projeto:

```dotenv
GOOGLE_CLIENT_ID=seu-id-do-cliente-aqui.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=sua-chave-secreta-aqui
```

## 5. Testando

1. Certifique-se de que o servidor está rodando (`python manage.py runserver`).
2. Acesse a página de login (`/accounts/login/`).
3. Clique no botão "Entrar com Google".
4. Se tudo estiver correto, você será redirecionado para o Google, fará o login e voltará para o sistema já autenticado.

## Solução de Problemas Comuns

* **Erro 400: redirect_uri_mismatch**: A URL no navegador não bate exatamente com a cadastrada no Google Cloud. Verifique `http` vs `https`, `www`, e portas.
* **SocialApp matching query does not exist**: O projeto está configurado para usar as configurações do `settings.py` via variáveis de ambiente, então não é necessário criar um "SocialApp" no Django Admin, mas certifique-se de que o `SITE_ID` no `settings.py` está correto (padrão: 1).
