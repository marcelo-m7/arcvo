# Arcvo Agent Guide

Este arquivo descreve o contrato atual para agentes no projeto Arcvo.

## Produto Canonico

Arcvo tem dois dominios:

- Acervo YouTube/eLearning no Odoo remoto.
- Agentes Arcvo rastreados no Odoo por meio do addon `arcvo_agents`.

Nao use os nomes antigos `agent_registry`, `autonomous_agents` ou modelos `agent.*`.
O contrato oficial usa modelos `arcvo.*`.

## Estrutura

- `backend/app/api/routes`: rotas FastAPI.
- `backend/app/services`: regras de aplicacao.
- `backend/app/integrations`: clientes externos.
- `frontend/src/features`: telas React.
- `odoo/addons/arcvo_agents`: addon Odoo canonico.
- `odoo/frozen_addons`: addons preservados, fora do deploy ativo.

## Regras De Trabalho

- Odoo remoto `https://marcelo-m7.com`, DB `odoo19`, e o alvo oficial.
- Nao imprimir segredos de `.env` ou `.env.local`.
- Nao criar docs de fase ou promessas de autonomia sem implementacao real.
- Quando alterar agentes, atualize backend, frontend e addon Odoo juntos.
