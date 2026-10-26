# Decisões da Fase III (registo)

Data: 20/10/2026. Prazo de entrega: 27/10/2026.

## 1. Casos de uso (18, 3 por membro)

Mantém-se a numeração da secção 9 do documento (UC01 a UC13). As secções 14, 18, 19 e 20,
que usam outra numeração, serão corrigidas. Acrescentam-se 5 casos de uso:

| UC | Nome | Actor |
|----|------|-------|
| UC14 | Registar conta | Inquilino/Comprador, Proprietário/Agência |
| UC15 | Iniciar e terminar sessão | Todos |
| UC16 | Gerir parâmetros do sistema | Administrador (obrigatório) |
| UC17 | Gerir perfil pessoal | Todos |
| UC18 | Guardar imóveis favoritos | Inquilino/Comprador |

## 2. Distribuição por membro (por módulo)

| Membro | Casos de uso | Módulo |
|--------|--------------|--------|
| Amilton Chipuale | UC01 Publicar, UC02 Editar, UC03 Remover | Gestão de Anúncios |
| Caetano Ruby | UC04 Pesquisar, UC07 Mapa, UC18 Favoritos | Pesquisa e Filtros |
| Elias Cuna | UC05 Preço justo, UC06 Alertas de fraude, UC08 Recomendações | Módulos de IA |
| Ferson Mula | UC14 Registar, UC15 Sessão, UC17 Perfil | Autenticação e Perfis |
| Frederico Cossa | UC10 Moderar, UC11 Gerir utilizadores, UC16 Parâmetros | Administração |
| Shelton de Castro | UC12 Alertas de IA, UC13 Indicadores, UC09 Assistente virtual | Monitorização e Assistente |

## 3. Inteligência artificial

| Módulo | Implementação |
|--------|---------------|
| Preço justo | Regressão linear (scikit-learn) com zona, tipo, divisões e área |
| Detecção de fraude | Regras (preço atípico, palavras suspeitas) + Isolation Forest |
| Verificação de imagens | Hash SHA-256 para detectar duplicados exactos |
| Recomendações | Semelhança com o histórico do utilizador (zona, tipo, faixa de preço) |
| Assistente virtual | Regras por palavras-chave (DUAT, caução, SISA, etc.) |

## 4. Instalação e demonstração

Docker Compose (PostgreSQL + Django + React) com `instalar.bat` e `instalar.sh` no CD.
Requisito único: Docker Desktop. Coincide com o ambiente da secção 20.5.

## 5. Plano por dias

| Dia | Data | Sprint | Trabalho |
|-----|------|--------|----------|
| 1 | 20/10 | Sprint 1 | Decisões, backlog, servidor Django: modelos, autenticação, permissões |
| 2 | 21/10 | Sprint 1 | API de anúncios, módulos de IA, padrões de desenho, dados de demonstração |
| 3 | 22/10 | Sprint 2 | Sistema de design (aprovação), React: sessão, menu por perfil, pesquisa, detalhe, mapa |
| 4 | 23/10 | Sprint 2 | React: publicar/editar, favoritos, recomendações, assistente, painéis de administração |
| 5 | 24/10 | Sprint 3 | Validações, usabilidade, Docker Compose, scripts de instalação, execução dos TC |
| 6 | 25/10 | Sprint 3 | Documento: secções da Fase III, diagramas PlantUML, correcção da numeração UC |
| 7 | 26/10 | Revisão | Regressão final, PDF, zip, tabela de participação |
| - | 27/10 | Entrega | Envio ao docente |

## Pendente

- Enunciado `LES-TG-2026_actualizado.docx` (não recebido).
- Percentagens reais da tabela de participação (a recolher no dia 7).
