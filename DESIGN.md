# Reform Cut design guide

Everything you need to rebuild the Reform Cut look in another project. Every value here is copied from the real
styles in `web/index.html` (the signed-in app). `web/auth.html`, `web/admin.html`, `web/landing.html` and
`web/legal.html` use the same colours.

Short version: **warm orange on a dark brown frame, a white rounded work area, flat surfaces, no shadows, and
hover states that change colour only.**

---

## 1. Principles

1. **Flat.** No `box-shadow` anywhere. Separate things with a 1px warm-grey border, a tinted fill
   (`--muted`), or the dark frame showing around the edges.
2. **Hover changes colour only.** Never size, position or shadow. Transitions are
   `background-color .15s ease, border-color .15s ease, color .15s ease`.
3. **One accent.** Orange `#FF8B33` marks what is selected, the main action and progress. Everything else stays
   warm neutral.
4. **Warm neutrals.** Every grey leans brown or pink (`#F7F4F1`, `#EEE8E4`, `#6D6159`). Never use a cool or blue grey.
5. **Text on orange is dark brown** (`--brand-ink #2A1A12`), never white.
6. **Plain language.** Labels and messages read like a person talking ("Drawing a preview of this layout…").
7. **Respect reduced motion**: switch every animation off under `prefers-reduced-motion: reduce`.

---

## 2. Colour palette

Paste this as-is:

```css
:root{
  /* brand orange */
  --brand:#FF8B33;        /* main accent: primary buttons, selected nav, progress, focus ring */
  --brand-press:#F27A1F;  /* primary button while pressed */
  --brand-hi:#FF9A4C;     /* primary button on hover (landing and auth pages call it --brand-hi) */
  --brand-ink:#2A1A12;    /* text and icons ON orange; also the heading colour */
  --brand-soft:#FFF2E8;   /* selected chip / tab / tile background */
  --brand-line:#FFD9BC;   /* border of soft-orange items; text selection */
  --brand-deep:#A9480A;   /* orange text on light backgrounds (links, warnings, icons in tiles) */

  /* the dark frame (sidebar, page edge, toasts) */
  --frame:#1E1612;
  --frame-2:#2C221D;                  /* raised items on the frame, frame hover */
  --frame-line:rgba(255,255,255,.08);  /* dividers on the frame */
  --frame-text:#F4EEEA;
  --frame-dim:#A99A91;

  /* the light work area */
  --bg:#FFFFFF;
  --muted:#F7F4F1;   /* quiet fills: segmented controls, chips, info rows, hover */
  --line:#EEE8E4;    /* card borders, table rows, dividers */
  --line-2:#E1D9D3;  /* input and button borders (a step stronger) */

  /* text */
  --text:#211813;    /* body text */
  --dim:#6D6159;     /* secondary text, labels */
  --faint:#A0948C;   /* hints, placeholders, timestamps */

  /* status */
  --good:#0F8A57; --good-soft:#E6F6EE;
  --bad:#D3343F;  --bad-soft:#FDECEE;
  --live:#E5323F;    /* "live" / recording red */

  /* corner radius */
  --r-lg:16px;  /* main panel, dialogs, composer */
  --r:12px;     /* buttons, cards, inner panels */
  --r-sm:8px;   /* inputs, small badges */

  color-scheme:light;
}
```

### Extra colours used directly in the code

| Use | Value |
|---|---|
| Neutral hover fill (chips, segments, tiles) | `#EDE3DB` |
| Step / row hover | `#F1EBE6`, table row hover `#FCFAF8` |
| Input border on hover | `#D9CCC2`; button border on hover `#D4CAC3` |
| Dark button hover | `#3A2C25` |
| Danger button hover | `#FADDE0` |
| Disabled primary button | background `#F3E7DD`, text `#B9A597` |
| Light orange text on dark (dropdown "add" row, avatars) | `#FFB27A`, hover `#FFC79D` |
| Mid-score badge | `#FFE3CC` |
| Video and thumbnail background | `#17110E`; menu panel `#2A1A12` |
| Muted text on dark panels | `#B9A597`, `#E9DED6` |
| Status lights on the frame | ok `#3DDC97`, error `#FF6B78`, middle `var(--brand)` |
| Warning banner | background `#FFF4E6`, text `#7A3E0C`, bold `#5A2C06` |
| Error box | background `#FDECEC`, text `#A12A2A`, title `#7A1F1F`, remove-hover `#C53030` |
| Notification icon tints | expiry `#FFF1DC` / `#9A5B12`; failure `#FDECEC` / `#C53030`; done `#E9F6EE` / `#1F7A4D` |
| Dialog backdrop | `rgba(14,12,11,.42)`; mobile scrim `rgba(30,22,18,.5)`; tour dim `rgba(20,14,11,.64)` |
| Scrollbar thumb | `#E2D9D7`, rounded, with a 3px white border |

### Which colours go together

- Orange (`--brand`) background → `--brand-ink` text.
- `--brand-soft` background → `--brand-ink` text, `--brand-deep` icon.
- Dark (`--brand-ink` or `--frame`) background → white or `--frame-text` text, orange icon.
- `--good-soft` → `--good`; `--bad-soft` → `--bad`.

---

## 3. Typography

```html
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
```

```css
body{font:14px/1.5 "Geist","Segoe UI",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
button,input,select,textarea{font:inherit;color:inherit}
```

| Role | Size / weight | Colour | Extra |
|---|---|---|---|
| Hero heading | `clamp(21px,5.2vw,28px)` / 700 | `--brand-ink` | `letter-spacing:-.03em; line-height:1.2; text-wrap:balance` |
| Dialog title | 18px / 600 | `--brand-ink` | |
| Settings section | 17px / 600 | `--brand-ink` | |
| Card / page title | 15px / 600 | `--brand-ink` | `letter-spacing:-.01em` |
| Body | 14px / 400 | `--text` | line-height 1.5 |
| Help text | 13px | `--dim` | |
| Field label | 12px / 600 | `--dim` | |
| Hint / timestamp | 12px | `--faint` | |
| Pill / badge | 11–12px / 600 | depends | |
| Big number | 20–28px / 600 | `--brand-ink` | `letter-spacing:-.02em; font-variant-numeric:tabular-nums` |

- **Headings are dark brown (`--brand-ink`), not black.**
- Use `tabular-nums` on every number that changes or sits in a column.
- Weights: 400 body, 500 nav and quiet labels, 600 buttons and headings, 700 hero and avatars.
- The landing page also loads Geist 800 and Inter 300. The caption preview fonts are Archivo Black, Anton and
  Poppins 800 (see section 11).

---

## 4. Layout

```
┌──────────────┬──────────────────────────────────────────┐
│  sidebar     │ ┌──────────────────────────────────────┐ │  ← dark frame (--frame) everywhere
│  240px       │ │ topbar (sticky, 54px)                │ │
│  --frame     │ ├──────────────────────────────────────┤ │
│              │ │ content (max 1280px, centred)        │ │  ← white panel, radius 16px,
│              │ │                                      │ │    8px gap from frame edge
│              │ └──────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────┘
```

```css
body{margin:0;background:var(--frame);overflow:hidden}
.app{display:grid;grid-template-columns:240px minmax(0,1fr);height:100vh}
.app.mini{grid-template-columns:76px minmax(0,1fr)}          /* collapsed sidebar: icons only */
main{background:var(--bg);margin:8px 8px 8px 0;border-radius:var(--r-lg);height:calc(100vh - 16px);overflow-y:auto}
.topbar{position:sticky;top:0;background:var(--bg);display:flex;align-items:center;gap:12px;padding:10px 28px;min-height:54px;border-bottom:1px solid transparent}
.topbar.stuck{border-color:var(--line)}                    /* border appears once the page scrolls */
.content{padding:28px 32px 72px;max-width:1280px;margin:0 auto}
```

**Spacing.** Gaps of 2, 4, 6, 8, 10, 12, 14, 16, 18, 22, 28 and 32px. Most often: 8px between buttons, 16px between
cards, 22px inside cards, 28–32px page padding.

**Breakpoints**

| Width | What changes |
|---|---|
| ≤ 1100px | Stat tiles go to 2 columns; two-column grids stack |
| ≤ 900px | The sidebar becomes a 280px slide-in drawer with a scrim; the main panel loses its margin and radius; a menu button appears |
| ≤ 760px | Top tabs drop below the title, full width |
| ≤ 640px | Content padding 18px 14px; clip grid 2 columns; tables become stacked cards; cards padding 16px |
| ≤ 560px | Long button labels are hidden; the primary composer button goes full width; two-column forms stack |

---

## 5. Sidebar (the dark frame)

```css
.side{background:var(--frame);color:var(--frame-text);padding:14px 10px 12px;display:flex;flex-direction:column}
.nav h4{font-size:12px;font-weight:500;color:var(--frame-dim);padding:14px 10px 4px}      /* group heading */
.nav-item{display:flex;align-items:center;gap:10px;min-height:34px;padding:0 10px;border-radius:7px;
  border:0;background:transparent;color:var(--frame-text);font-size:14px;font-weight:500}
.nav-item svg{width:17px;height:17px;color:var(--frame-dim)}
.nav-item:hover{background:var(--frame-2)}
.nav-item.on{background:var(--brand);color:var(--brand-ink);font-weight:600}             /* selected = solid orange */
.nav-item.on svg{color:var(--brand-ink)}
.nav-item.on:hover{background:#FF9A4C}
.count{font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;background:rgba(255,255,255,.1)}
.nav-item.on .count{background:rgba(42,26,18,.14);color:var(--brand-ink)}
.side-card{background:var(--frame-2);border-radius:var(--r);padding:12px 14px;font-size:12px;color:var(--frame-dim)}
.side-foot{border-top:1px solid var(--frame-line);padding-top:12px}
```

- Logo 36px high at the top. The square mark (34px) replaces it when the sidebar is collapsed.
- The selected nav item switches its icon to the **filled** version (see section 10).
- Avatars on the frame: 26px circle, `rgba(255,139,51,.18)` background, `#FFB27A` initials, 11px / 700.

---

## 6. Buttons

```css
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:38px;padding:0 14px;
  border-radius:var(--r);border:1px solid var(--line-2);background:#fff;color:var(--text);
  font-weight:600;white-space:nowrap;cursor:pointer;
  transition:background-color .15s ease,border-color .15s ease,color .15s ease}
.btn:hover{background:var(--muted);border-color:#D4CAC3}
.btn:active{background:var(--muted)}
.btn:disabled{opacity:.45;pointer-events:none}

.btn.primary{background:var(--brand);border-color:var(--brand);color:var(--brand-ink)}
.btn.primary:hover{background:#FF9A4C;border-color:#FF9A4C}
.btn.primary:active{background:var(--brand-press);border-color:var(--brand-press)}
.btn.primary:disabled{background:#F3E7DD;color:#B9A597}

.btn.dark{background:var(--brand-ink);border-color:var(--brand-ink);color:#fff}
.btn.dark svg{color:var(--brand)}
.btn.dark:hover{background:#3A2C25;border-color:#3A2C25}

.btn.danger{background:var(--bad-soft);border-color:transparent;color:var(--bad)}
.btn.danger:hover{background:#FADDE0}

.btn.ghost{background:transparent;border-color:transparent;color:var(--dim)}
.btn.ghost:hover{background:var(--muted);color:var(--text)}

/* sizes */
.btn.sm{height:32px;padding:0 11px;font-size:13px;gap:6px}  .btn.sm svg{width:16px;height:16px}
.btn.lg{height:44px;padding:0 20px;font-size:15px}
.btn.icon{width:32px;padding:0}                              /* square icon button, use with .sm */

/* bare icon button (toolbars, sidebar) */
.icon-btn{width:36px;height:36px;display:grid;place-items:center;border-radius:var(--r);border:0;background:transparent;color:var(--dim)}
.icon-btn:hover{background:var(--muted);color:var(--text)}
```

| Variant | When to use it |
|---|---|
| `primary` (orange) | The one main action on a screen: Make clips, Save |
| default (white, outlined) | Secondary actions |
| `dark` | A strong action that should not compete with orange: Go live, Upgrade |
| `danger` (soft red) | Delete or remove. Never a solid red button |
| `ghost` | Cancel, low-priority actions inside dialogs and bars |

Icons inside buttons are 18px (16px in `.sm`), with an 8px gap before the label.

---

## 7. Form fields

```css
input:not([type=checkbox],[type=radio],[type=file],[type=range]),select,textarea{
  width:100%;height:40px;padding:0 12px;background:#fff;border:1px solid var(--line-2);
  border-radius:var(--r-sm);outline:none;transition:border-color .15s ease}
textarea{height:auto;padding:10px 12px;resize:vertical}
input:hover,select:hover,textarea:hover{border-color:#D9CCC2}
input:focus,select:focus,textarea:focus{border-color:var(--brand)}       /* focus = orange border, no glow */
::placeholder{color:var(--faint)}

label.f{display:flex;flex-direction:column;gap:7px;font-size:12px;color:var(--dim);font-weight:600}  /* label above field */
.fields{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px}
```

**Switch** (a checkbox restyled):

```css
label.sw{display:flex;align-items:center;gap:12px;cursor:pointer;font-weight:600}
label.sw input{appearance:none;width:38px;height:22px;border-radius:999px;background:#DCD2D0;position:relative;margin:0}
label.sw input::after{content:"";position:absolute;top:3px;left:3px;width:16px;height:16px;border-radius:50%;background:#fff;transition:transform .15s}
label.sw input:checked{background:var(--brand)}
label.sw input:checked::after{transform:translateX(16px)}
label.sw small{display:block;color:var(--dim);font-size:12px;font-weight:400}   /* explanation under the label */
```

**Check chip** (a checkbox shown as a pill button):

```css
label.ck{display:inline-flex;align-items:center;gap:8px;height:36px;padding:0 13px;border-radius:var(--r);
  background:#fff;border:1px solid var(--line-2);font-weight:500}
label.ck:has(input:checked){background:var(--brand-soft);border-color:var(--brand-line);color:var(--brand-ink)}
label.ck input{accent-color:var(--brand)}
```

**Segmented control** (2–4 choices, each with an optional small note underneath):

```css
.seg{display:flex;gap:4px;background:#fff;border-radius:10px;padding:4px}          /* on a --muted panel */
.seg button{flex:1;display:flex;flex-direction:column;align-items:center;padding:7px 6px;border:0;border-radius:7px;
  background:transparent;color:var(--dim);font-size:13px;font-weight:600}
.seg button small{font-size:11px;font-weight:500;color:var(--faint)}
.seg button:hover{background:#EDE3DB;color:var(--text)}
.seg button[aria-pressed=true]{background:var(--brand-soft);color:var(--brand-ink)}
.seg button[aria-pressed=true] small{color:#B8693A}
```

**Range slider**: a 6px track with an orange fill set through `--p`, and a white thumb with a 6px orange ring.

```css
input[type=range]{appearance:none;height:6px;border-radius:999px;
  background:linear-gradient(90deg,var(--brand) 0 var(--p,5%),var(--line) var(--p,5%) 100%)}
input[type=range]::-webkit-slider-thumb{appearance:none;width:22px;height:22px;border-radius:50%;background:#fff;border:6px solid var(--brand)}
```

Native checkboxes and radios: `accent-color:var(--brand)`.

---

## 8. Surfaces and components

**Card**

```css
.card{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:22px;margin-bottom:16px}
.card>h2{font-size:15px;font-weight:600;color:var(--brand-ink);margin-bottom:4px}
.help{color:var(--dim);font-size:13px}
.danger-card{border-color:#F3C9C4} .danger-card h2{color:var(--bad)}
```

**Inner panel / option box**: `background:var(--muted); border-radius:12px; padding:12px 14px 14px`. Anything
inside it (segments, number boxes) is white. When the panel itself is white, swap it: the inside items use `--muted`.

**Stat tile**

```css
.tile{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:16px 18px}
.tile i{width:32px;height:32px;border-radius:var(--r-sm);background:var(--brand-soft);color:var(--brand-deep);display:grid;place-items:center}
.tile b{font-size:26px;font-weight:600;letter-spacing:-.03em;font-variant-numeric:tabular-nums;color:var(--brand-ink)}
.tile span{font-size:13px;color:var(--dim)}
```

**Pills and badges**

```css
.pill{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px;background:var(--muted);color:var(--dim)}
.pill.ok{color:var(--good);background:var(--good-soft)}
.pill.bad{color:var(--bad);background:var(--bad-soft)}
.pill.warn{color:var(--brand-deep);background:var(--brand-soft)}
.pill.live{color:#fff;background:var(--live)}
.pill.brand{color:var(--brand-ink);background:var(--brand)}
.dot{width:7px;height:7px;border-radius:50%;background:currentColor;animation:pulse 1.3s infinite}   /* live dot inside a pill */
```

**Chips** (filter and option toggles in a toolbar): 34px high, fully rounded, `--muted` background, `--dim` text,
13px / 500. Hover `#EDE3DB`. Selected: `--brand-soft` background with `--brand-ink` text.

**Tabs**: two styles.

- *Underline tabs* (`.tabs` / `.tabbtn`): 46px high, `--faint` text. The selected tab gets `--brand-ink` text,
  an orange icon, and a 3px orange bar along the bottom that grows in (`tabin`, .28s).
- *Pill tabs* (`.utabs` in the topbar): a `--muted` track with 3px padding. An orange indicator slides under the
  selected tab (`transition: transform .32s cubic-bezier(.3,.7,.2,1)`), and its text turns `--brand-ink`.

A count after a tab name (`.n`): 11px / 600 pill in `--muted`. On the selected tab it turns `--brand-soft`.

**Progress bar**

```css
.bar{height:6px;background:var(--muted);border-radius:999px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--brand);border-radius:999px;transition:width .8s ease}
```

**Empty state**: `border:1px dashed var(--line-2); border-radius:12px; padding:48px 20px; text-align:center`,
with a 56px illustration, a bold `--brand-ink` title and `--dim` text.

**Note / info row**: `--muted` background, 12px radius, 13px `--dim` text, `--brand-deep` icon on the left.

**Loading skeleton**

```css
.sk{background:linear-gradient(90deg,#EFE7E1 0%,#F8F3EF 50%,#EFE7E1 100%);background-size:200% 100%;animation:shimmer 1.2s linear infinite}
@keyframes shimmer{from{background-position:200% 0}to{background-position:-200% 0}}
```

**Spinner badge** (`.working`): an 11px orange label on `rgba(255,139,51,.14)`, with a 10px ring that has one
transparent side and spins at .8s.

**Tables**: headers 12px / 500 `--faint`, no background. Cells have `padding:12px 10px` and a 1px `--line` top
border. Row hover `#FCFAF8`. Numbers right-aligned with tabular-nums. On phones a table becomes stacked cards,
with each cell's label taken from `data-l`.

**Key / value list** (`.kv`): two columns (180px and the rest), 13px `--dim` key, 14px `--text` value, `--line`
divider between rows.

**Dropdown menu** (dark): `background:#2A1A12; border-radius:12px; padding:6px`, items `#E9DED6`, 13px / 500.
Hover `rgba(255,255,255,.08)`. The selected item shows an orange tick. It opens with a fade and a 6px slide, .18s.
No border or shadow: the dark panel stands out against the white page on its own.

**Light dropdown** (lists inside forms): white with a `--line-2` border, 12px radius, a `--muted` header row.
Hover `--muted`; selected `--brand-soft` with `--brand-deep` 600 text.

**Sticky save bar**: `background:var(--brand-ink)`, 14px radius, sticks to the bottom (16px up), and slides up
12px when there are unsaved changes.

**Selection bar** (`#selbar`): fixed at the bottom centre, `#1F140D` background, `rgba(255,178,122,.25)` border,
14px radius.

---

## 9. Dialogs, toasts and popovers

```css
dialog{border:1px solid var(--line);background:#fff;border-radius:var(--r-lg);padding:0;max-width:calc(100vw - 32px)}
dialog::backdrop{background:rgba(14,12,11,.42);animation:fadein .16s ease}
.dlg{padding:24px;width:450px;display:flex;flex-direction:column;gap:14px}
.dlg h2{font-size:18px;font-weight:600;color:var(--brand-ink)}
.dlg-foot{display:flex;justify-content:flex-end;gap:8px}     /* Cancel (ghost), then the primary action */
```

**Toast** (short message, bottom right): dark (`--frame` background, `--frame-text` text), 12px radius, 12px 16px
padding, at most 380px wide. An 8px dot at the start shows the kind: orange for info, `#3DDC97` for done,
`#FF6B78` for an error. It rises in over .2s.

**Notification card** (`.ntoast`): white, 340px, 12px radius, 34px tinted icon square on the left (9px radius),
13px / 600 title and 12px `--dim` text. It slides in from the right
(`cubic-bezier(.2,.8,.2,1)`, .35s).

**Popover** (`.pop`): white, `--line` border, 14px radius, at most 360px wide. Fades in and rises 8px over .18s.

---

## 10. Icons

- **Set:** Phosphor icons (MIT licence), drawn on a `viewBox="0 0 256 256"`, inline SVG, `fill:currentColor`.
- **Two weights:** regular for everything; *fill* only for the selected sidebar item (named `name_f`).
- **Sizes:** 18px by default, 17px in nav and tabs, 16px in small buttons and chips, 14px in tight spots.
- Icons take the colour of their text; give them their own colour only to make a point (an orange icon on a
  dark button, a `--brand-deep` icon in a soft tile).

```js
const ic = n => `<svg viewBox="0 0 256 256" aria-hidden="true">${I[n]}</svg>`;   // I = {name: '<path d="..."/>'}
```

```css
svg{width:18px;height:18px;flex:none;fill:currentColor}
```

**Logo**: `web/brand/logo.svg` (for dark backgrounds), `logo-light.svg` (for light backgrounds), and `favicon.svg`.
The mark is a rounded square (radius about 25% of its width) in `#FF8B33`, with artwork in `#310001` and
`#FBF7F8`. The email logo is `logo-email.png`.

---

## 11. Caption styles (video overlays)

These are drawn onto the clips and shown as small previews in the app:

| Style | Font | Highlight colour | Capitals |
|---|---|---|---|
| Bounce | Archivo Black | `#FFFF00` | Yes |
| Hype | Anton | `#FF3C3C` | Yes |
| Clean | Poppins 800 | `#6BD7FF` | No |

Preview boxes are 54px high on `#1E1612`, with white text and a 1px black outline
(`-webkit-text-stroke:1px #000; paint-order:stroke fill`).

---

## 12. Motion

```css
@keyframes rise   {from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}  /* new items appear */
@keyframes fadein {from{opacity:0}}                                                        /* dialogs */
@keyframes pulse  {50%{opacity:.3}}                                                        /* live dots, 1.3s infinite */
@keyframes spin   {to{transform:rotate(360deg)}}                                           /* spinners, .8s linear */
@keyframes tabin  {from{transform:scaleX(.3);opacity:0}to{transform:none;opacity:1}}       /* tab underline */
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
```

| Kind | Duration and easing |
|---|---|
| Hover colour | .15s ease |
| Menus, popovers | .18s ease |
| Item appearing (`rise`) | .2–.3s ease |
| Panels opening (grid rows 0fr → 1fr) | .3–.32s ease |
| Sliding indicators, the tour | .32–.5s `cubic-bezier(.22,.8,.24,1)` |

Open and close panels by animating `grid-template-rows: 0fr → 1fr`, not by animating height.

---

## 13. Accessibility basics

- Focus ring: `:focus-visible{outline:2px solid var(--brand);outline-offset:2px}`. Text fields show their orange
  border instead.
- Toggle buttons use `aria-pressed`; dropdown items use `aria-selected`; decorative icons use `aria-hidden="true"`.
- Use `[hidden]{display:none!important}` so `hidden` always wins.
- Text selection colour: `::selection{background:var(--brand-line)}`.
- Every image needs `alt`; thumbnails that only decorate get `alt=""`.

---

## 14. Do and don't

| Do | Don't |
|---|---|
| Separate things with a 1px `--line` border or a `--muted` fill | Use `box-shadow` |
| Change only colour on hover | Grow, lift or move things on hover |
| Use one orange primary button per screen | Put several orange buttons side by side |
| Put dark brown text on orange | Put white text on orange |
| Use warm greys from the palette | Use cool greys (`#999`, `#ccc`, slate) |
| Use 999px for pills and 12px for cards and buttons | Mix in other radius values |
| Use soft red for delete buttons | Use a solid red button |
| Write short, friendly labels | Use jargon in buttons and errors |

---

## 15. Starter page

A minimal page with the frame, a card and the main buttons, to copy into a new project:

```html
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--brand:#FF8B33;--brand-press:#F27A1F;--brand-ink:#2A1A12;--brand-soft:#FFF2E8;--brand-line:#FFD9BC;--brand-deep:#A9480A;
  --frame:#1E1612;--frame-2:#2C221D;--frame-text:#F4EEEA;--frame-dim:#A99A91;
  --bg:#fff;--muted:#F7F4F1;--line:#EEE8E4;--line-2:#E1D9D3;--text:#211813;--dim:#6D6159;--faint:#A0948C;
  --r-lg:16px;--r:12px;--r-sm:8px}
*{box-sizing:border-box}
body{margin:0;background:var(--frame);color:var(--text);font:14px/1.5 "Geist","Segoe UI",system-ui,sans-serif}
.app{display:grid;grid-template-columns:240px 1fr;height:100vh}
.side{color:var(--frame-text);padding:14px 10px}
.nav-item{display:block;padding:7px 10px;border-radius:7px;color:var(--frame-text);text-decoration:none;font-weight:500;transition:background-color .15s}
.nav-item:hover{background:var(--frame-2)}.nav-item.on{background:var(--brand);color:var(--brand-ink);font-weight:600}
main{background:var(--bg);margin:8px 8px 8px 0;border-radius:var(--r-lg);padding:28px 32px;overflow:auto}
h1{font-size:15px;font-weight:600;color:var(--brand-ink);margin:0 0 16px}
.card{border:1px solid var(--line);border-radius:var(--r);padding:22px}
.btn{display:inline-flex;align-items:center;gap:8px;height:38px;padding:0 14px;border-radius:var(--r);border:1px solid var(--line-2);
  background:#fff;color:var(--text);font:inherit;font-weight:600;cursor:pointer;transition:background-color .15s,border-color .15s,color .15s}
.btn:hover{background:var(--muted);border-color:#D4CAC3}
.btn.primary{background:var(--brand);border-color:var(--brand);color:var(--brand-ink)}.btn.primary:hover{background:#FF9A4C;border-color:#FF9A4C}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
@media (max-width:900px){.app{grid-template-columns:1fr}.side{display:none}main{margin:0;border-radius:0}}
</style></head><body>
<div class="app">
  <nav class="side"><a class="nav-item on" href="#">Home</a><a class="nav-item" href="#">Clips</a></nav>
  <main><h1>Home</h1><div class="card"><button class="btn primary">Make clips</button> <button class="btn">Cancel</button></div></main>
</div>
</body></html>
```
