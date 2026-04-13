# 07 - Visualization Primitives

> **Status:** not started
> **Depends on:** 03 (piece image endpoint)
> **Main plan ref:** Preliminary changes #4

---

## Objective

Build reusable Jinja2 macros for the visual components used across the solver UI
and the existing data browser pages. These are shared building blocks, not
standalone pages.

---

## Current state

- Templates exist for pieces, sheets, matches - all use plain HTML tables.
- No Jinja2 macros exist (each template is self-contained).
- No piece images are rendered anywhere (no image endpoint yet, see sub-plan 03).
- Piece detail shows text fields only.

---

## Plan

### Macro file

Create `webapp_resources/templates/macros/piece_macros.html` with reusable
`{% macro ... %}` blocks. Templates include them via:

```jinja2
{% from "macros/piece_macros.html" import piece_card, match_card, grid_cell %}
```

### Macro 1: `piece_card`

A compact card showing a piece thumbnail with metadata badges.

```jinja2
{% macro piece_card(piece, size=100, show_label=true, show_type=true, show_shapes=true) %}
<div class="piece-card" data-piece-id="{{ piece.piece_id }}">
  <div class="piece-card__img">
    <img src="/api/v1/pieces/{{ piece.piece_id }}/img?size={{ size }}"
         alt="Piece {{ piece.piece_id }}"
         loading="lazy"
         width="{{ size }}" height="{{ size }}">
    {% if show_label and piece.label %}
      <span class="piece-card__label">{{ piece.label }}</span>
    {% endif %}
  </div>
  {% if show_type and piece.oriented_piece_type %}
    <span class="badge badge--type">
      {{ piece.oriented_piece_type.piece_type.name }}
    </span>
  {% endif %}
  {% if show_shapes %}
    <div class="piece-card__shapes">
      {% for edge, shape in piece.segment_shapes.items() %}
        <span class="shape-dot shape-dot--{{ shape | lower }}"
              title="{{ edge }}: {{ shape }}">
        </span>
      {% endfor %}
    </div>
  {% endif %}
</div>
{% endmacro %}
```

### Macro 2: `match_card`

Two piece thumbnails side by side with matched edge highlight and score.

```jinja2
{% macro match_card(match, size=80, show_actions=false) %}
<div class="match-card" data-seg1="{{ match.seg_id1 }}" data-seg2="{{ match.seg_id2 }}">
  <div class="match-card__pieces">
    <div class="match-card__piece">
      <img src="/api/v1/pieces/{{ match.seg_id1.piece_id }}/img?size={{ size }}"
           loading="lazy" width="{{ size }}" height="{{ size }}">
      <span class="edge-badge edge-badge--{{ match.seg_id1.edge_pos.value | lower }}">
        {{ match.seg_id1.edge_pos.value }}
      </span>
    </div>
    <div class="match-card__vs">vs</div>
    <div class="match-card__piece">
      <img src="/api/v1/pieces/{{ match.seg_id2.piece_id }}/img?size={{ size }}"
           loading="lazy" width="{{ size }}" height="{{ size }}">
      <span class="edge-badge edge-badge--{{ match.seg_id2.edge_pos.value | lower }}">
        {{ match.seg_id2.edge_pos.value }}
      </span>
    </div>
  </div>
  <div class="match-card__score {{ 'score--good' if match.similarity < 0.3 else ('score--ok' if match.similarity < 0.7 else 'score--bad') }}">
    {{ "%.3f" | format(match.similarity) }}
  </div>
  {% if show_actions %}
    <div class="match-card__actions">
      <button class="btn btn--accept" data-action="accept">Accept</button>
      <button class="btn btn--reject" data-action="reject">Reject</button>
    </div>
  {% endif %}
</div>
{% endmacro %}
```

### Macro 3: `grid_cell`

A single cell in the solver grid canvas. Used in a grid layout by the solver template.

```jinja2
{% macro grid_cell(pos, placement=none, slot_type=none, is_target=false) %}
<div class="grid-cell
            {{ 'grid-cell--filled' if placement else 'grid-cell--empty' }}
            {{ 'grid-cell--target' if is_target else '' }}"
     data-pos="{{ pos }}"
     {% if not placement %}onclick="selectSlot('{{ pos }}')"{% endif %}>
  {% if placement %}
    {% set piece_id, orientation = placement %}
    <img src="/api/v1/pieces/{{ piece_id }}/img?size=80"
         style="transform: rotate({{ orientation }}deg)"
         loading="lazy">
    <span class="grid-cell__label">{{ piece_id }}</span>
  {% else %}
    {% if slot_type %}
      <span class="grid-cell__type">{{ slot_type }}</span>
    {% endif %}
  {% endif %}
</div>
{% endmacro %}
```

### Macro 4: `score_badge`

Inline score display with color coding.

```jinja2
{% macro score_badge(score) %}
{% set confidence = 1.0 / (1.0 + score) %}
<span class="score-badge"
      style="background-color: {{ 'hsl(' ~ (confidence * 120) | int ~ ', 70%, 50%)' }}">
  {{ "%.3f" | format(score) }}
</span>
{% endmacro %}
```

### CSS additions

Add to `webapp_resources/static/css/style.css` (or create a new `components.css`):

```css
/* Piece card */
.piece-card { display: inline-block; text-align: center; margin: 4px; }
.piece-card__img { position: relative; }
.piece-card__label { position: absolute; top: 2px; left: 2px; background: rgba(0,0,0,.7); color: #fff; padding: 1px 4px; font-size: 11px; border-radius: 2px; }

/* Shape dots */
.shape-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin: 1px; }
.shape-dot--in { background: #3b82f6; }
.shape-dot--out { background: #ef4444; }
.shape-dot--edge { background: #9ca3af; }
.shape-dot--weird { background: #eab308; }

/* Match card */
.match-card { display: flex; align-items: center; gap: 8px; padding: 8px; border: 1px solid #e5e7eb; border-radius: 4px; margin: 4px 0; }
.match-card__pieces { display: flex; align-items: center; gap: 4px; }

/* Score colors */
.score--good { color: #16a34a; }
.score--ok { color: #ca8a04; }
.score--bad { color: #dc2626; }

/* Grid cell */
.grid-cell { width: 90px; height: 90px; border: 1px solid #d1d5db; display: flex; align-items: center; justify-content: center; cursor: pointer; position: relative; }
.grid-cell--empty { border-style: dashed; background: #f9fafb; }
.grid-cell--filled { border-style: solid; background: #fff; }
.grid-cell--target { border-color: #3b82f6; border-width: 2px; }
.grid-cell__type { font-size: 10px; color: #9ca3af; text-transform: uppercase; }
```

---

## Integration with existing templates

After macros are created, the existing templates (`pieces.html`, `piece_detail.html`,
`matches.html`) can optionally be updated to use them. This is cosmetic and
can be done incrementally. The primary consumer is the solver UI (sub-plan 08).

---

## File touchmap

| File | Change |
|------|--------|
| `webapp_resources/templates/macros/piece_macros.html` | **NEW** - all macros |
| `webapp_resources/static/css/components.css` | **NEW** - component styles |
| `webapp_resources/templates/base.html` | Link `components.css` in `<head>` |

---

## Test strategy

- Manual visual test: create a test page that renders each macro with sample data
- Verify lazy loading works (images load on scroll)
- Verify score color coding matches thresholds
- Verify grid cell click handler fires (browser devtools)
- Cross-browser: Chrome + Firefox minimum
