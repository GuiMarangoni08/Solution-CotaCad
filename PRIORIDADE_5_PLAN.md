# Prioridade 5: Polish, Testes e Refinamento

## Estado Atual (2026-06-11)

✅ **Funcionalidade Core Completa:**
- Backend: API endpoints + APScheduler + modelos DB
- Frontend: Context + componentes + 3 páginas
- Fluxo end-to-end: upload DXF → processamento → Excel
- Autenticação: Login/Signup funcionando

⚠️ **Pendências:**
- Testes automatizados (backend e frontend)
- Validação de inputs
- Animações e UX refinement
- Tratamento robusto de erros
- Deploy em produção (manual conforme DEPLOY_INSTRUCTIONS.md)

---

## Tarefas Prioridade 5

### 5.1 Frontend — Validação & UX Melhorias

#### 5.1.1 Validação de Inputs
- [ ] Tamanho máximo de arquivo (2MB limite mencionado)
- [ ] Apenas .dxf permitido
- [ ] Campos obrigatórios no form
- [ ] Validação de email no signup/login

#### 5.1.2 Mensagens de Erro Melhoradas
- [ ] Toasts ou alerts para sucesso/erro
- [ ] Loading states mais claros
- [ ] Timeout mensagens (ex: Excel demorando)
- [ ] Retry automático em caso de falha

#### 5.1.3 UX Polish
- [ ] Animações suaves para status (spinner → check mark)
- [ ] Breadcrumbs em detalhes
- [ ] Botão "Voltar ao Dashboard"
- [ ] Dark mode (opcional)
- [ ] Responsividade mobile

### 5.2 Backend — Validação & Robustez

#### 5.2.1 Validação de DXF
- [ ] Verificar se arquivo é DXF válido
- [ ] Tamanho máximo 2MB (MAX_UPLOAD_MB)
- [ ] Camadas obrigatórias presentes
- [ ] Rejeitar DXF que não é SOL/MAPEAMENTO/TRIPLEX

#### 5.2.2 Error Handling Robusto
- [ ] Try-catch em tasks de background
- [ ] Erro claro em job status se falhar
- [ ] Rollback se Excel falhar na geração
- [ ] Logging estruturado (para debugging)

#### 5.2.3 Performance
- [ ] Otimizar query de levantamentos (índices no DB)
- [ ] Limpar arquivos temp após processamento
- [ ] Cache de tipo detectado (não re-scanear DXF)

### 5.3 Testes

#### 5.3.1 Backend Tests (pytest)

```bash
# Tests a implementar:
- test_auth.py
  - signup com novo usuário
  - signup com email duplicado (erro)
  - login com credenciais corretas
  - login com senha errada (erro)
  - GET /me sem token (401)

- test_levantamentos.py
  - POST /api/levantamentos com DXF válido
  - POST com arquivo inválido (erro)
  - GET /api/levantamentos (lista)
  - GET /api/levantamentos/{id} (detalhe)
  - PATCH /api/levantamentos/{id} (ajustes)
  - POST /api/levantamentos/{id}/gerar-excel

- test_background_tasks.py
  - processar_dxf: DXF SOL
  - processar_dxf: DXF MAPEAMENTO
  - gerar_excel: Excel criado com sucesso
  - Job status transitions: enfileirado → processando → pronto
```

#### 5.3.2 Frontend Tests (vitest ou jest)

```bash
# Tests a implementar:
- auth.test.tsx
  - Login form renders
  - Signup form renders
  - Submit com credenciais válidas
  - Submit com email inválido (erro)

- LevantamentoContext.test.tsx
  - criarLevantamento chama API
  - listarLevantamentos popula state
  - gerarExcel enfileira job

- LevantamentoCard.test.tsx
  - Renderiza card com status
  - Clique navega para detalhe

- DataPreview.test.tsx
  - Renderiza tabela com ambientes
  - Calcula total de área
```

### 5.4 Documentação

#### 5.4.1 README.md
- [ ] Setup local (npm install, python -m venv, etc.)
- [ ] Como rodar dev servers
- [ ] Como fazer deploy
- [ ] Estrutura de pastas

#### 5.4.2 API Documentation
- [ ] OpenAPI/Swagger dos endpoints
- [ ] Exemplos de requisição/resposta
- [ ] Códigos de erro comuns

#### 5.4.3 User Guide
- [ ] Como fazer upload de DXF
- [ ] Como ajustar dados
- [ ] Como gerar e baixar Excel
- [ ] FAQ e troubleshooting

---

## Timeline Estimada

| Tarefa | Esforço | Status |
|--------|---------|--------|
| 5.1 Frontend UX | 3h | TODO |
| 5.2 Backend Validation | 2h | TODO |
| 5.3.1 Backend Tests | 3h | TODO |
| 5.3.2 Frontend Tests | 2h | TODO |
| 5.4 Documentação | 1h | TODO |
| **Total** | **11h** | |

---

## Critérios de Sucesso (MVP Pronto)

✅ **Funcional:**
- [ ] Upload, processamento, Excel gerado com sucesso
- [ ] Todos os status (processando → revisão → pronto) funcionam
- [ ] Validação rejeita arquivos inválidos com mensagem clara
- [ ] Erros são tratados sem crashes

✅ **Testado:**
- [ ] ≥80% cobertura backend
- [ ] ≥50% cobertura frontend (componentes críticos)
- [ ] Teste manual: criar 3 levantamentos diferentes

✅ **Deployado:**
- [ ] Backend rodando no VPS
- [ ] Frontend rodando na Vercel
- [ ] Ambos comunicando corretamente

✅ **Documentado:**
- [ ] README com setup e deploy
- [ ] API docs com exemplos
- [ ] User guide com screenshots

---

## Próximas Fases (Pós-MVP)

- **Fase 6**: Suporte a outros tipos de DXF (MAPEAMENTO, TRIPLEX)
- **Fase 7**: Multi-user collaboration (comments, edits history)
- **Fase 8**: Batch processing e combo projects
- **Fase 9**: Export para outros formatos (PDF, JSON)
- **Fase 10**: Landing page pública e marketing

