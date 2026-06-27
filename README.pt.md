# Order Intake — AluProfil · Desafio SACOMP 2026

<sub>[English](./README.md) · 🌐 **Português**</sub>

> Transforma **PDFs de pedido de compra** caóticos de clientes em **EDIFACT ORDERS
> D.96A** validado para um ERP legado — com uma tela de reconciliação revisada por
> um operador.

Uma solução full-stack (**FastAPI + Next.js + Postgres/Mongo/Blob**, tudo em Docker
Compose) para o desafio de *order intake* do minicurso da **Machines Like Me** na
**SACOMP 2026**.

<p align="center">
  <img alt="Tela de reconciliação do Order Intake — pedido Bauprofil, 7 de 7 linhas resolvidas, pronto para gerar EDIFACT"
       src="./docs/assets/order-intake-reconciliation.png" width="640">
  <br>
  <sub>A tela de reconciliação: um pedido alemão totalmente resolvido para códigos internos <code>AE-</code>, cada linha verde, EDIFACT liberado.</sub>
</p>

---

## O desafio

Este repositório é um **fork do starter de workshop** usado num **minicurso
ministrado por pessoas da Machines Like Me** (automação de intake de documentos)
na **SACOMP 2026**. O starter é um scaffold full-stack quase em branco;
o exercício é construir a feature de ponta a ponta.

**O cenário:** a *AluProfil*, uma fabricante de perfis de alumínio, recebe ~300
pedidos de compra por mês como **PDFs** de ~100 clientes, em quatro formatos
completamente diferentes (tabela alemã, prosa suíça, parágrafos franceses,
dimensões suecas). Quatro funcionários os redigitam num ERP de 2009 (**MetallSoft
7.3**) com **~30% de erro**. O ERP é implacável: **um único código interno errado
rejeita o pedido inteiro**, e ele só fala **EDIFACT em UNOA/ASCII**.

📄 Enunciado completo → **[`docs/challenge/`](./docs/challenge/README.md)**

## O que eu construí

Um único módulo **`order_intake`** (trocável) que leva um PDF do upload até um
`.edi` para download:

- **Três estratégias de extração selecionáveis por cliente** — um parser
  determinístico de tabela DIN (grátis), um LLM local grátis (Ollama) e um LLM
  externo compatível com OpenAI (BYO key). Escolhidas com
  [evidência](./docs/benchmark/README.md), não no chute.
- **Reconciliação por specs** contra o catálogo de 35 perfis — `exato → dimensão →
  alias de liga → fuzzy → aprendido`. O código interno é **resolvido pelas specs,
  nunca inventado pelo LLM**, então um dígito trocado não embarca o produto errado.
- **Mapa aprendido por cliente** — cada correção do operador ensina
  `(cliente, código dele) → código interno`, então pedidos repetidos resolvem sozinhos.
- **Flags de confiança reais** — sinais determinísticos concretos (código não
  casado, unidade ambígua, código lido ≠ resolvido), nunca probabilidade do modelo.
- **EDIFACT seguro** — transliteração UNOA/ASCII + um gate que valida *todos* os
  `PIA+1` antes de gerar o arquivo.
- **Tela de reconciliação** — o PDF original ao lado das linhas resolvidas, edição
  inline Set/Confirm, botão "Generate EDIFACT" liberado por gate, i18n EN/DE.

## Prova de que funciona

- ✅ **Verificado ponta a ponta:** um pedido Bauprofil gerou uma mensagem
  `ORDERS:D:96A` válida de **55 segmentos**, com envelope correto e texto transliterado.
- 📊 **Medido:** [4 clientes × 3 estratégias em benchmark](./docs/benchmark/README.md)
  por velocidade e corretude contra os `.edi` de referência.
- ✅ **82 testes** de backend passando; typecheck + lint limpos.
- 🔎 **Auditado contra o enunciado:** veja o
  [scorecard honesto de requisitos](./docs/requirements-audit.md).

## Arquitetura em resumo

Um único módulo síncrono `custom/order_intake/` com estágios separados e trocáveis
(`ingest → extract → reconcile → confidence → edifact`). Detalhes e diagramas →
**[`docs/architecture/`](./docs/architecture/README.md)**.

## Começando

```bash
cp .env.example .env       # placeholders bastam para a stack local
./up.sh                    # sobe backend, frontend, 3 stores, viewers, ollama
docker compose exec ollama ollama pull qwen2.5:1.5b   # opcional: LLM local grátis
```

Depois abra **http://localhost:3000/order-intake** (login dev-stub é automático).
PDFs de exemplo em [`docs/sources/orders/`](./docs/sources/orders/). Pare com
`./down.sh`.

> Guia completo de uso (estratégias, EDIFACT, troubleshooting) →
> **[`ORDER_INTAKE.md`](./ORDER_INTAKE.md)**

## Como foi construído

Não foi "pedir para um modelo construir um app". Rodei como uma pequena
organização de engenharia com um **sistema multi-agente próprio**: idear → colocar
a arquitetura **em julgamento** (promotor/defensor/juiz adversariais) → implementar
com agentes especialistas → auditar a entrega. Cada hand-off deixou um artefato
escrito — por isso as decisões deste repo estão registradas, não improvisadas.

➡️ **[`docs/how-it-was-built.md`](./docs/how-it-was-built.md)**

## Documentação

| | |
|--|--|
| 🎯 [O desafio](./docs/challenge/README.md) | o que foi pedido + os quatro clientes |
| ⚖️ [Decisões (ADRs)](./docs/decisions/README.md) | por que é construído assim |
| 🏗️ [Arquitetura](./docs/architecture/README.md) | como as peças se encaixam |
| 📊 [Benchmark](./docs/benchmark/README.md) | comparação de estratégias com dados |
| ✅ [Auditoria de requisitos](./docs/requirements-audit.md) | scorecard honesto |
| 🤖 [Como foi construído](./docs/how-it-was-built.md) | o workflow de agentes de IA |

---

<sub>Construído sobre um starter de workshop (FastAPI + Next.js). O charter
autoritativo do starter é [`WORKSHOP.md`](./WORKSHOP.md); as convenções de
backend/frontend estão nos respectivos arquivos `AGENTS.md`.</sub>
