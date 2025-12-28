### Projeto — Site de Textos Acadêmicos/Filosóficos + Cursos

## Objetivo

Construir um site para publicação e divulgação de textos científicos e filosóficos e oferta de cursos com aulas em vídeo, com controle de acesso por assinatura.

---

## Perfis e acesso (RBAC)

### Perfis

* **Admin**

  * CRUD completo de artigos, cursos, aulas e mídia
  * Gerenciamento de usuários, planos e permissões
  * Publicar, despublicar e arquivar conteúdos
* **Usuário Free**

  * Acesso apenas a conteúdos marcados como gratuitos
* **Usuário Pago**

  * Acesso conforme o nível de assinatura contratada

### Regra de autorização (MVP)

* Todo conteúdo (Artigo e Aula) possui um campo `required_plan`

  * Ex.: `FREE`, `BASIC`, `PRO`
* Usuários possuem um `current_plan`, derivado de uma assinatura ativa
* O acesso é permitido quando `user.current_plan >= content.required_plan`

---

## Conteúdo (MVP)

### Artigos

* título
* slug
* resumo
* tags
* autor(es)
* PDF (upload)
* capa (opcional)
* status (`draft`, `published`, `archived`)
* `required_plan`

### Cursos

* título
* slug
* descrição
* capa
* status (`draft`, `published`)

### Aulas

* curso (FK)
* título
* ordem
* **vídeo hospedado no Vimeo** (URL ou ID do Vimeo)
* materiais complementares (PDF opcional)
* `required_plan`

---

## Vídeos (Vimeo)

* Os vídeos das aulas serão hospedados no **Vimeo**.
* O backend armazenará apenas:

  * `vimeo_video_id` ou URL do player
* O frontend exibirá o player oficial do Vimeo via iframe.
* Acesso às páginas de aula será protegido via RBAC; o controle de acesso ao vídeo ocorre no nível da aplicação.
* (Opcional futuro) Usar recursos de privacidade do Vimeo (domínio permitido, vídeos não listados).

---

## Pagamentos e assinaturas (Stripe)

### Planos

* Definição de múltiplos planos (ex.: Free, Basic, Pro).
* Cada plano mapeia para um **Stripe Price ID**.

### Fluxo de pagamento

* Checkout realizado via **Stripe Checkout**.
* Após pagamento:

  * Stripe envia eventos via **webhook** (`checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`, etc.).
  * O backend atualiza o estado da assinatura do usuário.

### Auditoria

* Registrar no banco:

  * ID do evento Stripe
  * usuário
  * plano
  * status da assinatura
  * timestamps
* Logs de pagamento são mantidos para auditoria e reconciliação.

---

## Requisitos não funcionais

### Responsividade

* Abordagem **mobile-first**
* Layout totalmente responsivo para desktop e mobile
* Implementação com **Tailwind CSS**

### SEO

* URLs amigáveis (`/artigos/<slug>`, `/cursos/<slug>`)
* Meta tags (title, description)
* Open Graph para compartilhamento
* Sitemap automático para conteúdos publicados

---

## Stack técnica

### Backend

* **Django**
* Django Admin como backoffice principal
* Controle de acesso via Groups/Permissions + lógica por plano

### Frontend

* **Django templates + Tailwind CSS**
* Uso pontual de JavaScript para interações (ex.: player, navegação)

### Banco de dados

* **SQLite** (produção inicial), com:

  * WAL habilitado
  * `busy_timeout` configurado
  * transações curtas e objetivas
  * uma conexão por request / pool pequeno

---

## PDFs e conteúdos pagos

* Artigos e materiais em PDF serão armazenados no backend.
* PDFs pagos **não devem ser servidos por URLs públicas diretas**.
* Acesso a PDFs protegidos será feito por endpoint autenticado/autorizado.
* Visualização dos PDFs via **PDF.js**.




