# 🎯 PRECISION OBSESSION PROTOCOL

**Manifesto**: *Cada projeto novo é uma oportunidade de aprender e evoluir para 100% de precisão. Não fazemos deploy final até validar contra especificação.*

---

## 📐 Definição: 100% de Precisão

| Métrica | Target | Método Validação |
|---------|--------|------------------|
| **Detecção de Ambientes** | 100% | Comparar lista DXF vs PDF |
| **Área ± tolerância** | ±2% da especificação | `abs(dxf_area - pdf_area) / pdf_area < 0.02` |
| **Identificação de Textos** | 98%+ | Contar textos encontrados vs esperados |
| **Desambiguação** | 100% | Cada "DEP" vs "DEP 01/02/03" correto |
| **Tipos Detectados** | 100% | SOL vs MAPEAMENTO vs TRIPLEX correto |

---

## 🔄 Workflow Obrigatório — "Precision Validation Pipeline"

### **Toda vez que um novo DXF chega:**

```
1. UPLOAD
   └─ Usuario faz upload DXF
   
2. PROCESSAMENTO AUTOMÁTICO
   └─ Sistema extrai dados, gera dados_extraidos
   
3. PRECISÃO AUTOMÁTICA ← NOVO
   ├─ Compara com historico.json (se ORC existe)
   ├─ Gera relatório: ambientes detectados vs esperados
   ├─ Calcula divergências por ambiente
   └─ Sinaliza anomalias: CRÍTICO / AVISO / OK
   
4. REVISÃO MANUAL + FEEDBACK
   ├─ Usuario vê relatório de precisão
   ├─ Ajusta ambientes que divergem
   ├─ Confirma dados finais em dados_ajustados
   └─ Sistema APRENDE: novo registro em historico.json
   
5. EXCEL GERADO
   └─ Dados finais validados
   
6. ANÁLISE PÓS-PROJETO (NOVO)
   ├─ Calcular acurácia final vs PDF original
   ├─ Documentar learnings
   ├─ Atualizar algoritmo se necessário
   └─ Commit: "ORC.XXXXX: 100% precisão — learnings: Y"
```

---

## 📊 Precisão Tracking — Métricas Obrigatórias

### **Em cada levantamento, capturar:**

```python
{
  "id": "lev_123",
  "orc": "21457",
  "precision_metrics": {
    "ambientes_encontrados": 31,
    "ambientes_esperados": 31,
    "taxa_deteccao": 100,  # %
    
    "areas_divergencia": [
      {"ambiente": "DEPÓSITO 01", "pdf": 5.09, "dxf": 3.91, "divergencia_pct": 23.2, "status": "REVISAR"},
      {"ambiente": "CAFÉ", "pdf": 49.35, "dxf": 49.35, "divergencia_pct": 0.0, "status": "OK"},
      ...
    ],
    
    "textos_encontrados": 28,
    "textos_esperados": 31,
    "taxa_texto": 90.3,  # %
    
    "desambiguacoes": [
      {"nome_duplicado": "DEP", "encontrados": 3, "desambiguados": 3, "sucesso": true}
    ],
    
    "erros_criticos": ["ACESSO PEDESTRE: 46% divergência"],
    "avisos": ["Texto WC CLIENTE deslocado, encontrado por proximidade"],
    
    "score_final": 92.5,  # média ponderada de todas métricas
    "pronto_para_producao": false,  # só true se score >= 98
    "data_validacao": "2026-06-11T02:30:00"
  }
}
```

---

## 🚨 Critérios de Aprovação para Deploy

### **Status Obrigatório por divergência:**

| Divergência | Status | Ação |
|-------------|--------|------|
| **0-1%** | ✅ OK | Pode usar sem ajuste |
| **1-3%** | ⚠️ AVISO | Revisar, mas aceitável |
| **3-5%** | 🔴 REVISAR | OBRIGATÓRIO ajuste antes de usar |
| **>5%** | 🚫 CRÍTICO | **NÃO USAR** — investigar causa |

### **Score Mínimo para "Production Ready":**
- **98+**: Pronto para usar diretamente
- **90-97**: Pronto COM ajustes do usuário
- **<90**: Não release — debug necessário

---

## 💾 Histórico Expandido — historico.json Versão 2

Cada novo projeto adiciona **automaticamente**:

```json
{
  "orc": "21457",
  "cliente": "OR",
  "tipologia": "stand",
  "data_processamento": "2026-06-11",
  "ambiente_contagem": 31,
  
  "precision_report": {
    "score_geral": 92.5,
    "ambientes_confirmados": 19,
    "ambientes_estimados": 12,
    "divergencias_encontradas": 3,
    "divergencia_max": 46.2,  // ACESSO PEDESTRE
    "divergencia_media": 8.3
  },
  
  "learnings": [
    "Texto 'WC CLIENTE' aparece a 1.8m do polígono — adicionar buffer de 2m",
    "Ambiente 'DEPÓSITO' aparece 3x — usar ordem: maior primeiro",
    "ACESSO PEDESTRE no DXF é 46% maior que PDF — verificar se inclui vias públicas"
  ],
  
  "proxima_validacao": "Se receber ORC.21457 R02, comparar contra este baseline"
}
```

---

## 🔧 Implementação — O que é Novo

### **Backend: Novo Endpoint**

```python
# POST /api/levantamentos/{id}/validar-precisao
# Compara dados_extraidos vs historico.json baseline
# Retorna: precision_metrics + recomendações

{
  "score": 92.5,
  "status": "REVISAR",
  "divergencias": [
    {
      "ambiente": "DEPÓSITO 01",
      "pdf_area": 5.09,
      "dxf_area": 3.91,
      "divergencia_pct": 23.2,
      "recomendacao": "Medir in loco ou ajustar DXF"
    }
  ],
  "pronto_para_producao": false
}
```

### **Frontend: Nova Seção em Detalhe**

```
┌─────────────────────────────────────┐
│ RELATÓRIO DE PRECISÃO               │
├─────────────────────────────────────┤
│ Score Geral: 92.5/100 ⚠️ REVISAR   │
├─────────────────────────────────────┤
│ Ambientes Detectados: 31/31 ✅      │
│ Taxa de Texto: 90.3% ⚠️             │
│ Divergência Máxima: 46.2% 🚫        │
├─────────────────────────────────────┤
│ AMBIENTES COM DIVERGÊNCIA:          │
│ ❌ DEPÓSITO 01: 23.2% (PDF: 5.09m²) │
│ ⚠️  ACESSO: 46.2% (PDF: 103m²)      │
│ ⚠️  WC CLIENTE: Texto deslocado     │
├─────────────────────────────────────┤
│ [Ajustar Dados] [Gerar Relatório]   │
└─────────────────────────────────────┘
```

### **Estrutura de Dados: Campo Novo**

```python
# Em models.py, adicionar:
class Levantamento(Base):
    ...
    # Novo campo
    precision_metrics = Column(JSON, nullable=True)
    # Exemplo:
    # {
    #   "score": 92.5,
    #   "status": "REVISAR",
    #   "divergencias": [...]
    # }
```

---

## 📋 Checklist por Projeto — "Obsession Ritual"

**OBRIGATÓRIO antes de liberar levantamento para a equipe:**

- [ ] Levantamento processado e status = "revisão"
- [ ] Chamou endpoint `/validar-precisao`
- [ ] Score ≥ 90 (caso contrário, investigar)
- [ ] Todos os "CRÍTICO" foram revisados
- [ ] Usuário confirmou dados_ajustados
- [ ] Excel gerado com dados_ajustados
- [ ] Documentado em histórico: "ORC.XXXXX — 98% — learnings: [...]"
- [ ] Se houve erro >5%: investigado e documentado root cause
- [ ] ✅ Pronto para usar

---

## 🎓 Exemplo Real: Precisão de ORC.21457

### **Baseline (do histórico.json):**
```
Ambientes: 31 confirmados
Áreas: 19 exatos, 12 estimados
Score esperado: 90-95%
```

### **Processamento No Sistema:**
```
1. Upload DXF → Extrai 31 ambientes
2. Compara com histórico.json → 3 divergências detectadas
3. Relatório:
   - CAFÉ: 0% divergência ✅
   - DEPÓSITO 01: 23% divergência ⚠️
   - ACESSO PEDESTRE: 46% divergência 🚫
4. Score: 92.5
5. Recomendação: REVISAR antes de usar
```

### **Ação do Usuário:**
```
1. Vê que DEPÓSITO 01 está errado (23%)
2. Abre DXF manualmente, vê que é mesmo 3.91m²
3. Nota: "PDF diz 5.09m² mas DXF desenha 3.91m² — divergência real, não erro"
4. Adiciona nota: "Verificar in loco — posso estar errado"
5. Confirma dados
6. Sistema aprende: DEPÓSITO 01 é "alta confiança" (divergência explicada)
```

---

## 🚀 Implementação — Fases

### **FASE 1: MVP (hoje, 30min)**
- [ ] Criar endpoint `/validar-precisao` (compara com histórico.json)
- [ ] Adicionar `precision_metrics` ao modelo
- [ ] Mostrar score na UI (básico)
- [ ] Deploy

### **FASE 2: Obsession Dashboard (próxima semana, 2h)**
- [ ] Seção visual de precisão na página de detalhe
- [ ] Relatório detalhado por ambiente
- [ ] Histórico de precisão por ORC
- [ ] Alertas automáticos se score < 90

### **FASE 3: Machine Learning (próximas semanas)**
- [ ] Usar histórico de divergências para treinar modelo
- [ ] Predizer precisão **antes** do processamento
- [ ] Auto-sugerir ajustes com base em padrões

---

## 📖 Documentação por Projeto

**Template obrigatório ao finalizar cada ORC:**

```markdown
# ORC.21457 — Precision Report

**Data**: 2026-06-11
**Score Final**: 92.5/100
**Status**: REVISADO ✅

## Métricas
- Ambientes: 31/31 (100%)
- Taxa Texto: 90.3% (28/31)
- Divergência Média: 8.3%

## Divergências Encontradas
1. **DEPÓSITO 01**: 23% (PDF=5.09m² vs DXF=3.91m²)
   - Root cause: DXF pode estar desatualizado
   - Ação: Verificar in loco
   
2. **ACESSO PEDESTRE**: 46% (PDF=103m² vs DXF=150m²)
   - Root cause: DXF inclui área de vias públicas
   - Ação: Usar PDF como baseline

## Learnings
- Textos deslocados: buscar em raio de 2m
- Múltiplos "DEP": ordenar por área
- Sempre comparar com PDF quando divergência > 5%

## Próxima Revisão
Se receber ORC.21457 R02 (revisão 2), usar este relatório como baseline.
```

---

## 💡 Filosofia

**"Precisão não é um luxo, é o core do QuanttunAI."**

- Cada projeto novo traz **conhecimento** que melhora a próxima
- Divergências não são falhas, são **oportunidades de aprender**
- 100% é o padrão, não o exceção
- A obsessão é **sistemática**, não aleatória

---

## 📞 Escalation

**Se score < 90:**
1. Usuário não consegue resolver → escalate para Dev
2. Dev investiga root cause
3. Atualiza algoritmo
4. Documenta no PRECISION_OBSESSION.md
5. Próximo projeto: problema não acontece mais

---

## 🎯 KPI: Precision Obsession

| Métrica | Target |
|---------|--------|
| % de projetos com score ≥ 98 | 90% |
| Tempo médio até 100% | <2 iterações |
| Root causes resolvidos | 100% |
| Learnings por projeto | ≥2 |

