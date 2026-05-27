# Arquétipos de prompt — metta-pdf

Presets de prompt pra geração de imagens via `nano-banana` CLI, organizados por
arquétipo de cena. Seguem o framework 8-camadas do skill `nano-banana`:
subject + composition + setting + lighting + style anchor + color grade +
camera/lens + negative cues.

Cada arquétipo é uma **base** — o orquestrador injeta o contexto editorial
específico (tipo de cliente, ambiente, atributos do perfil) antes de submeter.

---

## §1. COVER — Hero contextual (landscape, 16:9)

**Quando usar:** primeira página, background full-bleed com overlay dark.
**Slot:** 16:9, ~1024×576 ou 1K. Composição com upper-third de negative space pro título.

### Template base
```
Wide editorial shot of {ENVIRONMENT}, {TIME_OF_DAY}, {KEY_VISUAL_ELEMENT}.
{SUBJECT_DESCRIPTION}, {ACTION}. Compositionally the upper third of the
frame is deliberately negative space for editorial text overlay. {LIGHTING_SETUP}.
Editorial documentary photography in the style of Bloomberg Businessweek,
warm amber and teal cinematic color grade, low contrast, premium magazine
quality. Shot on 24mm f/2.8, deep focus, slight 35mm film grain. Avoid
stock photo cliches, fake smiles, oversaturated colors, readable brand
logos or text, watermarks, illustrations, cartoon style.
```

### Exemplo (treinamento de vendedores em loja de posto)
- ENVIRONMENT: "the interior of a Brazilian highway gas station convenience store"
- TIME_OF_DAY: "blue hour late afternoon"
- KEY_VISUAL_ELEMENT: "shelves of snacks, beverage coolers glowing cool blue, large storefront windows showing pumps and trucks at twilight"
- SUBJECT_DESCRIPTION: "A male attendant in his late 30s in a polo shirt"
- ACTION: "stands behind the counter mid-conversation"
- LIGHTING_SETUP: "Warm tungsten interior key light from camera-right with cool teal rim light from windows behind"

---

## §2. OPENER — Subject + context (square, 1:1)

**Quando usar:** segunda seção (abertura), imagem ao lado de texto lede.
**Slot:** 1:1, ~1024×1024. Sujeito ou cena de relação humana relevante ao tema.

### Template base
```
Editorial medium shot of {SUBJECT_INTERACTION} at {ENVIRONMENT}.
{SUBJECT_A_DESCRIPTION}, {ACTION_A}. {SUBJECT_B_DESCRIPTION}, {ACTION_B}.
{ENVIRONMENT_DETAIL}. {LIGHTING_SETUP}. Documentary editorial photography
in the style of Bloomberg Businessweek, warm amber and teal color grade,
low contrast. Shot on 35mm f/2.0, both subjects in soft focus, candid
moment, Kodak Portra 400 film grain. Avoid stock photo, fake smiles,
readable trademarks, oversaturated colors, illustration.
```

### Exemplo (atendente + cliente em loja de posto)
- SUBJECT_INTERACTION: "an attendant and trucker customer in conversation"
- ENVIRONMENT: "the counter of a Brazilian gas station convenience store"
- SUBJECT_A: "Brazilian male attendant in his late 30s in a polo shirt"
- ACTION_A: "leans across the counter listening attentively"
- SUBJECT_B: "Brazilian truck driver in plaid shirt and baseball cap"
- ACTION_B: "mid-conversation with an open hand gesture"

---

## §3. HERO-STRIP — Reading the scene (landscape, 16:9 → cropped 21:6)

**Quando usar:** seções transitórias, banner horizontal entre h1 e lede.
**Slot:** 16:9 nativo, será cropado pra 21:6 no CSS (perde topo+base).

### Template base
```
Editorial wide shot of {ENVIRONMENT}, {DIVERSE_ELEMENTS_VISIBLE}. In sharp
focus in the foreground, {KEY_SUBJECT}, {ACTION_OF_OBSERVING_OR_READING}.
{ENVIRONMENT_DETAIL}. {LIGHTING_SETUP}. Editorial documentary photography
in the style of Magnum Photos, warm amber and teal color grade, low contrast.
Shot on 35mm f/2.8, subject in focus with background softly blurred, candid
frozen moment, slight Kodak Portra 400 grain. Avoid stock photo, readable
logos or text, americana aesthetic, oversaturated, illustration.
```

### Variantes por tema
- **Leitura de cena**: múltiplos perfis visíveis no fundo, sujeito central observando
- **Reflexão**: sujeito solo, contemplativo, mood quieto
- **Decisão**: sujeito com objeto em foco (tablet, prancheta, café)

---

## §4. PROFILE — Retrato de persona (portrait, 4:5)

**Quando usar:** páginas Perfil N — magazine 2-col com foto à esquerda.
**Slot:** 4:5 portrait, ~1024×1280. Sujeito ocupando 60-70% do frame.

### Template base
```
Editorial medium shot portrait of {SUBJECT_DESCRIPTION_DETAILED},
{CHARACTERISTIC_POSE}. {ENVIRONMENT_CONTEXT_WITH_TOOLS_OR_VEHICLE}.
{EXPRESSION_AND_BODY_LANGUAGE}. {LIGHTING_SETUP}. Documentary candid
portraiture in the style of {MAGAZINE_REFERENCE}, warm amber and teal
cinematic grade, low contrast, slightly desaturated. Shot on 50mm f/2.0,
shallow depth of field with subject in razor focus, Kodak Portra 400
emulation. Avoid stock photo, fake smile, posed corporate headshot,
readable trademarks, americana aesthetic, illustration.
```

### Variantes por perfil
- **Operacional/braçal** (caminhoneiro, mecânico, lavrador): roupas casual de trabalho, pele bronzeada, cap/boné, golden hour, magazine ref: Magnum Photos
- **Executivo/corporativo**: business casual, ambiente urbano, midday clean light, magazine ref: WSJ Mansion / Exame
- **Técnico/operacional uniformizado**: polo de empresa, ferramentas (tablet, prancheta), overcast neutro, magazine ref: Forbes corporate

---

## §5. QUOTE-PHOTO — Momento de conexão (landscape, 16:9)

**Quando usar:** quote-photo layout — imagem fica de fundo do quote box.
**Slot:** 16:9, ~1024×576. Cena de conexão humana íntima, ambos sujeitos no frame.

### Template base
```
Editorial close-up of a respectful moment of connection between
{SUBJECT_A_BRIEF} and {SUBJECT_B_BRIEF} at {ENVIRONMENT}.
{INTIMATE_ACTION_DESCRIPTION}. Both faces share the frame, neither dominates.
{LIGHTING_SETUP}. Editorial documentary in the style of Wall Street Journal
portraits, warm amber and teal cinematic grade, low contrast. Shot on 50mm
f/2.0, both subjects in soft focus, candid intimate moment, Kodak Portra
400 grain. Avoid stock photo, fake smiles, readable logos or text,
oversaturated, illustration.
```

---

## §6. CONTENT-ONLY (raro)

**Quando usar:** raramente — só se a página de fundamento tiver MUITO espaço
e o tema for visualmente forte. Default = sem imagem (DS limpo + tipografia).

Pula a sugestão automática. User pode pedir explicitamente.

---

## §7. Negative prompt universal

Sempre concatenar no fim do prompt:
```
Avoid stock photo cliches, fake smiles, plastic-looking skin, oversaturated
colors, text or logos visible (no readable brands, no readable signage),
watermarks, illustrations, cartoon style, lifestyle ad gloss, americana
aesthetic, posed corporate model headshot, fluorescent flat lighting.
```

---

## §8. Identidade visual Metta (DNA embarcado)

O DS Metta puxa pra:
- **Color grade**: warm amber + cool teal (clássico teal-and-orange)
- **Lighting**: golden hour ou warm tungsten + cool rim, evitar fluorescent
- **Lens**: 35mm f/2.0 - 50mm f/2.8, shallow depth of field
- **Film stock reference**: Kodak Portra 400 emulation, leve grain
- **Pessoas**: brasileiras, 35-55 anos quando empresário, diverso por gênero/etnia
- **Mood**: editorial documental, candid, premium mas acessível
- **Refs**: Bloomberg Businessweek (corporate), Magnum Photos (documental), WSJ Mansion (lifestyle), Forbes (corporate), Trip / Exame / Você S/A (brasileiras)

Tudo isso já está embutido nos templates §1-§5.

---

## §9. Como o suggest_images.py usa

1. Recebe `enriched_sections` do classifier
2. Pra cada seção elegível (layout in {cover, opener-spread, hero-strip, profile-spread, quote-photo}):
   - Identifica arquétipo do prompt base (§1-§5)
   - Extrai contexto da seção (título + parágrafos + tags) pra preencher os SLOTS do template
   - Gera prompt completo
   - Define aspect_ratio + size do slot
3. Retorna lista `[{section_title, layout, prompt, aspect, size, slot_filename}]`

O orquestrador então mostra essa lista pro user aprovar/editar antes de
disparar o `generate_images.py`.
