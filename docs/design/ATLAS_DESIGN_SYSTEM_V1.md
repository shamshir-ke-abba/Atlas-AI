````markdown
# ATLAS DESIGN SYSTEM V1

**Status:** DESIGN LOCK  
**Version:** 1.0  
**Authority:** Canonical visual + implementation specification  
**Applies to:** `interfaces/web/*`  
**Primary reference:** Current Atlas Design Sheet  
**Implementation rule:** This document is authoritative for exact values and behavior. The design sheet is authoritative for visual composition, hierarchy, proportions, and overall appearance.

---

# 01. BRAND & LOGO

## 1.1 Brand Identity

Atlas is a personal AI assistant presented as precise, reliable software.

Core characteristics:

- Calm
- Intelligent
- Precise
- Reliable
- Technical
- Personal
- Context-aware
- Professional

Atlas must feel like a serious piece of software rather than an AI novelty product.

### Visual concept

The Atlas identity is built around:

**A + trajectory/path + node**

The trajectory represents:

- navigation
- direction
- movement through information
- reasoning paths
- connected context

The node represents:

- a point of information
- context
- a decision
- a destination

The visual language must remain recognizable even when the full logo is not present.

---

# 02. PRIMARY LOGO SYSTEM

## 2.1 Primary Logo

The primary Atlas logo consists of:

- geometric A
- integrated trajectory/path
- node
- ATLAS wordmark

Preferred horizontal lockup:

```text
[Atlas Mark] ATLAS
````

Do not replace the Atlas mark with:

* AI brains
* robots
* orbs
* neural networks
* generic stars
* chat bubbles
* futuristic symbols

## 2.2 Logo Variants

Required variants:

1. Primary logo
2. Logo + ATLAS
3. Logo + AI
4. Wordmark
5. Monochrome
6. Light-background variant
7. Dark-background variant
8. Micro Mark

## 2.3 Wordmark

Primary wordmark:

**ATLAS**

Typography:

* Inter
* SemiBold / 600
* compact tracking
* uppercase

The wordmark must remain visually subordinate to the geometric Atlas mark.

## 2.4 Clear Space

Minimum clear space around the logo:

**equal to the height of the logo node**

No UI element, text, border, or icon may intrude into the clear-space region.

---

# 03. LOGO CONSTRUCTION

## 3.1 Geometry

The Atlas mark is geometric and must maintain:

* consistent A proportions
* consistent stroke relationships
* stable node placement
* stable trajectory angle
* balanced optical weight

The trajectory must visibly interact with the A rather than appear as an unrelated arrow.

## 3.2 Logo Construction Reference

The design sheet shows the logo over a construction grid.

Implementation does not need to reproduce the construction grid.

The construction grid exists to communicate:

* proportional consistency
* alignment
* geometry
* minimum-size behavior

## 3.3 Minimum Sizes

Required references:

| Variant        | Minimum reference |
| -------------- | ----------------: |
| Micro Mark     |              16px |
| Small Mark     |              24px |
| Assistant Mark |              32px |
| Standard Mark  |              48px |
| Large Mark     |              64px |
| Full Logo      |            128px+ |

At small sizes, use a simplified Micro Mark.

Never scale the full complex logo directly to 16px.

---

# 04. MICRO MARK SYSTEM

## 4.1 Purpose

The Micro Mark is the primary conversational Atlas identifier.

It is used for:

* assistant avatar
* favicon
* compact sidebar
* loading states
* tool activity
* assistant status
* mobile UI
* notifications

## 4.2 Sizes

Required sizes:

```text
16px
24px
32px
48px
64px
128px
```

## 4.3 Small-Scale Rules

### 16px

Use simplified geometry.

Prioritize:

* recognizable A
* trajectory
* node
* strong silhouette

Remove visual details that collapse at tiny sizes.

### 24px

Simplified Micro Mark.

### 32px

Standard conversational mark.

### 48px

Full assistant mark may be used.

### 64px+

Full geometry permitted.

### 128px

Full brand mark.

## 4.4 Applications

Required application examples:

* Favicon — 16px
* Mobile App Icon — 48px+
* Desktop App Icon — 128px
* Chat Avatar — 48px
* Assistant Mark
* Monochrome Mark

---

# 05. ASSISTANT MARK & STATE SYSTEM

Atlas does not use a conventional human avatar.

The Atlas Micro Mark is the assistant's identity.

Required states:

```text
IDLE
THINKING
USING TOOL
SEARCHING
RESPONDING
GENERATING
SUCCESS
ERROR
OFFLINE
```

## 5.1 IDLE

Static Micro Mark.

No animation.

## 5.2 THINKING

The Atlas trajectory/node subtly shifts or pulses.

Rules:

* subtle
* functional
* short visual movement
* no glow
* no bouncing
* no generic spinner

Preferred animation:

* node opacity pulse
* trajectory movement
* approximately 1 second cycle

## 5.3 USING TOOL

The trajectory/path provides the activity cue.

Possible behavior:

* subtle 2px translation
* trajectory movement
* node movement

Do not animate the entire UI.

## 5.4 SEARCHING

Search state may use:

* Micro Mark
* search icon
* restrained path movement

## 5.5 RESPONDING

Use the Atlas mark as a stable conversational identity.

No excessive animation.

## 5.6 GENERATING

Use:

* stable Atlas mark
* subtle activity indicator
* restrained generation cursor if required

Do not rely on a generic animated three-dot loader.

## 5.7 SUCCESS

Use:

* settled Atlas mark
* semantic success color where appropriate
* subtle state transition

## 5.8 ERROR

Use:

* Atlas mark
* semantic error treatment
* visible textual explanation

Never communicate error using color alone.

## 5.9 OFFLINE

Atlas mark:

* muted
* approximately 30% opacity

Offline state should be communicated through temporary application status, not repeated messages inserted into conversation history.

---

# 06. COLOR SYSTEM

## 6.1 Color Philosophy

Atlas uses a restrained:

**deep slate + muted teal**

palette.

Functional UI should remain predominantly neutral.

Teal is reserved for:

* brand identity
* active state
* focus
* selected state
* important interactive accents

Do not use:

* neon cyan
* neon green
* cyberpunk gradients
* glowing borders
* excessive semantic colors

---

## 6.2 DARK MODE

### Background

```text
--bg-base: #09090B;
--bg-surface: #121215;
--bg-elevated: #1C1C22;
```

### Borders

```text
--border-subtle: #27272F;
--border-strong: #3F3F4A;
```

### Text

```text
--text-primary: #F4F4F5;
--text-secondary: #A1A1AA;
--text-muted: #82828C;
```

### Brand

```text
--brand-ui: #398C8F;
--brand-text: #4FB8BA;
```

### Semantic

```text
--semantic-success: #4ADE80;
--semantic-warning: #FBBF24;
--semantic-error: #F87171;
--semantic-info: #60A5FA;
```

---

# 07. LIGHT MODE

### Background

```text
--bg-base: #F4F4F5;
--bg-surface: #FFFFFF;
--bg-elevated: #E4E4E7;
```

### Borders

```text
--border-subtle: #E4E4E7;
--border-strong: #D4D4D8;
```

### Text

```text
--text-primary: #09090B;
--text-secondary: #52525B;
--text-muted: #71717A;
```

### Brand

```text
--brand-ui: #2A7376;
--brand-text: #1D5355;
```

### Semantic

```text
--semantic-success: #16A34A;
--semantic-warning: #D97706;
--semantic-error: #DC2626;
--semantic-info: #2563EB;
```

---

# 08. COLOR USAGE

## 8.1 Neutral

Use neutral colors for:

* backgrounds
* surfaces
* cards
* borders
* standard controls
* conversation content

## 8.2 Brand

Use brand colors for:

* Atlas identity
* active sidebar item
* focus
* selected controls
* important links
* assistant-specific activity

Do not use brand teal for every UI element.

## 8.3 Semantic

Success:

```text
#4ADE80 dark
#16A34A light
```

Warning:

```text
#FBBF24 dark
#D97706 light
```

Error:

```text
#F87171 dark
#DC2626 light
```

Information:

```text
#60A5FA dark
#2563EB light
```

Semantic colors must communicate actual states.

---

# 09. TYPOGRAPHY SYSTEM

## 9.1 Fonts

Primary:

**Inter**

Technical:

**JetBrains Mono**

No additional decorative fonts.

## 9.2 Type Scale

```text
Display:       24px / 700
H1:            18px / 600
H2:            16px / 600
Subheading:    16px / 500
Body:          14px / 400
Small:         13px / 400
Label:         12px / 500
Code:          13px / JetBrains Mono
Numbers:       12px
Button:        14px / 600
```

## 9.3 Label Rules

Uppercase labels are reserved for:

* technical metadata
* section labels
* design-system categories
* compact state labels

Do not make normal navigation or conversational text uppercase.

## 9.4 Code

Use JetBrains Mono for:

* code
* technical values
* hex values
* dimensions
* developer-facing metadata

---

# 10. ICONOGRAPHY

## 10.1 Icon Style

Icons must be:

* simple
* technical
* consistent
* line-based
* restrained

Default:

```text
24px grid
1.5px stroke
currentColor
```

## 10.2 Icon Rules

Maintain consistent:

* stroke width
* corner treatment
* optical size
* padding
* alignment

Do not mix:

* filled cartoon icons
* 3D icons
* emoji
* unrelated icon families

## 10.3 Common Icons

Required icon language includes:

* search
* settings
* memory
* tools
* conversations
* calendar
* attachment
* send
* information
* error
* warning
* success
* close
* menu
* expand
* collapse

---

# 11. SPACING & GEOMETRY

## 11.1 Base Grid

Primary spacing unit:

**4px**

Preferred values:

```text
4
8
12
16
24
32
48
64
```

## 11.2 Component Spacing

Reference:

```text
Component padding: 16px
Message spacing: 12px
Section spacing: 24px
```

## 11.3 Corner Radius

Allowed radii:

```text
4px
6px
8px
```

Use the smallest radius that communicates hierarchy.

Avoid excessive pill-shaped UI.

Pills are reserved for:

* compact status
* tool state
* tags
* small semantic indicators

## 11.4 Borders

Default structural border:

```text
1px solid var(--border-subtle)
```

Strong border:

```text
1px solid var(--border-strong)
```

Do not default to 2px borders.

Active state may use:

```text
2px inset accent indicator
```

## 11.5 Shadows

Shadows are rare.

Use them primarily for:

* popovers
* tooltips
* dialogs
* elevated temporary surfaces

Do not use large shadows around normal conversation messages.

---

# 12. CHAT UI

## 12.1 Primary Layout

Desktop:

```text
┌────────────┬──────────────────────┬──────────────┐
│ Sidebar    │ Conversation         │ Context      │
│            │                      │              │
│            │                      │              │
│            │                      │              │
│            │ Composer             │              │
└────────────┴──────────────────────┴──────────────┘
```

The conversation is the primary visual focus.

## 12.2 Conversation Width

Default readable width:

```text
720px
```

Permitted expansion for:

* code
* tables
* web results
* structured tool output

Recommended upper range:

```text
720–760px
```

## 12.3 User Messages

User messages:

* right-aligned
* maximum 80% width
* elevated surface
* subtle border if necessary
* no avatar

Avoid heavy card styling.

## 12.4 Atlas Messages

Atlas messages:

* left-aligned
* full conversational width
* Atlas Micro Mark
* no conventional human avatar
* minimal surface treatment

Atlas responses should feel lighter than user message containers.

## 12.5 Message Spacing

Default:

```text
24px between conversational groups
```

Related content may use smaller internal spacing.

---

# 13. SIDEBAR

## 13.1 Width

Expanded:

```text
260px
```

Collapsed:

```text
64px
```

These are canonical tokens.

## 13.2 Structure

Required navigation:

```text
Atlas
New Chat

Recent / Conversations
Tools
Memory
Settings
```

Profile does not require a separate primary navigation destination.

## 13.3 Sidebar States

Every interactive sidebar item supports:

```text
Default
Hover
Active
Focused
Disabled
```

## 13.4 Active State

Active conversation:

* subtle elevated surface
* 2px inset brand indicator
* readable primary text
* no glow

## 13.5 Collapsed Sidebar

Collapsed mode shows:

* Micro Mark
* icons
* tooltips where needed

Never rely on icons alone when ambiguity would harm usability.

---

# 14. MESSAGE COMPONENT SYSTEM

Required message/component examples:

```text
User
Atlas
System
Tool
Error
Loading
Code
Quote
Link
List
Warning
Success
```

## 14.1 Default

Neutral surface and text.

## 14.2 Focused

Visible keyboard focus.

## 14.3 Selected

Brand-accented selection.

## 14.4 Streaming

Streaming state must be visually subtle.

Avoid large animated loaders.

## 14.5 Error

Use:

* error border/accent
* error icon
* explanatory text

Do not use color alone.

## 14.6 Code

Code blocks:

* elevated surface
* JetBrains Mono
* readable contrast
* horizontal scrolling where necessary
* no excessive decoration

## 14.7 Quote

Use a subtle leading indicator/border.

## 14.8 Link

Use brand text color.

Links must remain visibly identifiable.

---

# 15. INPUT / COMPOSER

## 15.1 Composer

The composer is a primary application control.

Target height:

```text
48px minimum
```

Maximum input growth:

```text
200px
```

The composer should remain visually quiet.

## 15.2 States

Required:

```text
Normal
Focused
Typing
Disabled
Processing
Error
```

## 15.3 Focus

Focus state:

* visible 2px focus ring or equivalent accessible treatment
* brand color
* no glow

## 15.4 Controls

Composer may contain:

* attachment
* tool/action controls
* send

Controls should remain compact.

## 15.5 Processing

During processing:

* preserve composer structure
* disable conflicting controls
* show restrained activity
* do not replace the entire composer with a generic loader

---

# 16. TOOL-USE VISUAL LANGUAGE

Tool activity is part of the conversation but must not dominate it.

## 16.1 Active Tool

Use compact inline treatment:

```text
Using Calculator…
Searching the web…
Checking calendar…
Reading memory…
Processing context…
```

## 16.2 Completed Tool

Use:

```text
✓ Calculator
✓ Searched the web
✓ Checked calendar
✓ Read memory
```

## 16.3 Failed Tool

Use:

```text
Tool failed
```

with semantic error treatment.

## 16.4 Tool States

Required:

```text
Active
Completed
Failed
Expanded
```

## 16.5 Visual Rules

Tool UI must be:

* small
* quiet
* inline
* readable
* expandable when detailed information is useful

Do not create a giant tool workspace for ordinary tool calls.

---

# 17. MEMORY / CONTEXT

Memory and context are important but secondary.

They must not dominate normal conversation.

## 17.1 Context Drawer

Desktop width:

```text
280px
```

Default:

**collapsed or secondary**

## 17.2 Sections

Required:

```text
Relevant Conversation
Memory
Active Context
Active Tools
Stored Information
```

## 17.3 Memory

Memory represents information Atlas has retained for longer-term use.

Example:

```text
Memory
Project preferences
Preferred tools
Important recurring information
```

## 17.4 Context

Context represents information relevant to the current conversation.

Example:

```text
Active Context
Current project
Current conversation
Relevant documents
Current task
```

## 17.5 Active Tools

Shows tools currently being used.

## 17.6 Visual Rules

Memory/context UI must be:

* text-first
* productivity-oriented
* restrained
* collapsible

Do not use:

* neural graphs
* brain graphics
* sci-fi HUDs
* glowing node networks
* consciousness visualizations

---

# 18. THINKING / MOTION SYSTEM

Motion exists to communicate function.

It should never exist merely for decoration.

## 18.1 Timing

Primary motion values:

```text
Fast: 100ms
Functional: 150ms
Panel: 250ms
Thinking cycle: ~1000ms
```

## 18.2 Easing

Preferred:

```text
ease-out
```

Avoid:

* bounce
* elastic spring
* dramatic acceleration
* exaggerated transitions

## 18.3 Allowed Animation Properties

Prefer:

```text
opacity
transform
```

Avoid expensive animation of:

* layout
* filters
* large shadows
* blur

## 18.4 Thinking

Thinking may use:

* opacity pulse
* trajectory movement
* subtle 2px translation

Never use a generic loading spinner as the primary Atlas identity.

## 18.5 Reduced Motion

When reduced motion is enabled:

* remove nonessential animation
* preserve state visibility
* preserve functionality
* do not simply make every transition 0ms
* thinking becomes static or minimally changing

---

# 19. MICRO-INTERACTIONS

Required states:

```text
Hover
Focus
Pressed
Selected
Disabled
Loading
Processing
Error
Success
```

## 19.1 Hover

Approx:

```text
100ms
```

Subtle surface/border change.

## 19.2 Focus

Always visibly accessible.

Minimum:

```text
2px focus indicator
```

## 19.3 Pressed

Slight visual compression or surface shift.

No bounce.

## 19.4 Selected

Use brand accent and clear surface differentiation.

## 19.5 Disabled

Reduce:

* contrast
* interaction affordance

Do not make disabled text completely unreadable.

## 19.6 Loading

Use restrained activity indicator.

## 19.7 Processing

Use subtle activity within the relevant component.

## 19.8 Error

Use semantic error treatment plus textual information.

## 19.9 Success

Use semantic success treatment where meaningful.

---

# 20. DASHBOARD / HOME

The Dashboard/Home view is an optional entry point and must remain product-oriented.

## 20.1 Content

Possible sections:

```text
Welcome
Recent conversations
Tools
Memory
Context
Empty state
```

## 20.2 Visual Character

The dashboard must feel like:

* a workspace
* a starting point
* a conversation launcher

It must NOT feel like:

* analytics software
* enterprise BI
* game HUD
* futuristic command center

---

# 21. EMPTY / LOADING / ERROR STATES

## 21.1 Empty Conversation

Recommended:

* centered Atlas logo
* 48px full mark
* approximately 20% opacity
* short welcome text

Example:

```text
How can I help?
```

Keep the screen calm.

## 21.2 Loading

Use restrained activity.

Do not show giant spinners.

## 21.3 Generating

Use:

* Atlas activity
* subtle generation indication
* optional cursor

## 21.4 Tool Loading

Use inline tool state.

Example:

```text
Using Calculator…
```

## 21.5 Network Error

Use an inline error block.

Example:

```text
Connection unavailable.
Retry
```

Use a semantic error treatment.

## 21.6 Tool Error

Show:

* failed tool
* concise explanation
* recovery action when available

## 21.7 Offline

Offline should appear in application status/header.

Do not continuously inject:

```text
Connection lost
```

into conversation history.

---

# 22. LIGHT + DARK MODE

## 22.1 Dark Mode

Primary Atlas experience.

Characteristics:

* deep near-black base
* restrained slate surfaces
* muted teal accent
* high readability
* subtle borders

## 22.2 Light Mode

Characteristics:

* off-white base
* white surfaces
* soft gray borders
* dark text
* darker muted teal

## 22.3 Shared Rules

Both modes must preserve:

* same hierarchy
* same component dimensions
* same typography
* same logo
* same spacing
* same interaction states
* same semantic meanings

Do not create two visually unrelated applications.

---

# 23. RESPONSIVE DESIGN

## 23.1 Desktop

Breakpoint:

```text
>1024px
```

Layout:

```text
Sidebar
Conversation
Context Drawer
```

Recommended:

```text
Sidebar: 260px
Context: 280px
Conversation: flexible
```

## 23.2 Tablet

Use:

```text
64px sidebar
Conversation
Context overlay/drawer
```

Context can slide over the conversation.

## 23.3 Mobile

Sidebar is hidden behind a menu.

Use:

* mobile header
* conversation
* slide-over context
* bottom composer

Composer padding:

```text
8px
```

User messages:

```text
max-width: 90%
```

## 23.4 Mobile Context

Context drawer width:

```text
280px
```

It should slide over the conversation.

Do not squeeze the conversation to fit a permanent context column.

## 23.5 Touch Targets

Interactive controls should have adequate touch area.

Do not create tiny controls merely to preserve desktop density.

---

# 24. ACCESSIBILITY

Accessibility is part of the visual system.

## 24.1 Required States

Demonstrate:

```text
Keyboard Focus
Focus Ring
Disabled
Error
Contrast
Reduced Motion
```

## 24.2 Focus

Minimum visible focus indicator:

```text
2px
```

## 24.3 Color

Do not rely exclusively on color to communicate:

* errors
* success
* warnings
* selected state

Use:

* icons
* labels
* borders
* text
* structure

as appropriate.

## 24.4 Contrast

The token system must be validated against actual component backgrounds.

Do not assume every token pairing is automatically WCAG compliant.

Critical text must remain readable.

## 24.5 Reduced Motion

Respect:

```text
prefers-reduced-motion
```

Disable nonessential motion while preserving state communication.

## 24.6 Keyboard

All interactive UI must be keyboard accessible.

Required:

* visible focus
* logical tab order
* keyboard-accessible drawers
* keyboard-accessible buttons
* keyboard-accessible controls

---

# 25. BRAND APPLICATIONS

Required applications:

```text
Browser Favicon
Desktop App Icon
Chat Avatar
Website Header
Sidebar
Notification
Tool State
Settings Screen
```

## 25.1 Favicon

Use simplified 16px Micro Mark.

## 25.2 Desktop Icon

Use full recognizable Atlas mark.

## 25.3 Chat Avatar

Use Micro Mark.

## 25.4 Website Header

Use:

```text
Atlas mark + Atlas
```

Keep header restrained.

## 25.5 Notification

Use:

* Atlas Micro Mark
* concise title
* concise message
* semantic state when relevant

## 25.6 Tool State

Use Micro Mark or appropriate icon alongside compact tool text.

## 25.7 Settings

Settings should use normal application hierarchy.

Do not turn Settings into a futuristic control panel.

---

# 26. DO / DON'T

## 26.1 DO

```text
Restrained UI
Clean hierarchy
Technical precision
Readable typography
Consistent spacing
Subtle accents
Professional software
Quiet interactions
Useful context
Atlas-specific identity
```

## 26.2 DON'T

```text
Neon
Cyberpunk
Glassmorphism
Giant AI orb
Excessive gradients
Excessive cards
Generic AI loaders
Glowing effects
Clutter
Random typography
Sci-fi HUD
Decorative particle effects
```

---

# 27. COMPONENT DENSITY

Atlas uses high information density in design-system references but controlled density in the application.

## Design Sheet

May be:

* dense
* multi-column
* information-rich
* technical

## Actual Application

Should be:

* calm
* readable
* spacious enough to scan
* hierarchy-first

Do not interpret the dense design sheet as a requirement to make every application screen dense.

---

# 28. SURFACE HIERARCHY

Use three primary surface levels.

```text
Background
Surface
Elevated
```

## Background

Primary application canvas.

## Surface

Used for:

* sidebar
* normal controls
* contextual areas

## Elevated

Used for:

* user messages
* selected components
* temporary UI
* popovers
* important controls

Avoid wrapping every component in a visible card.

---

# 29. HEADER / APPLICATION CHROME

Header should communicate:

* Atlas identity
* connection state
* current conversation/context
* essential controls

Do not use a permanent giant status dashboard.

Avoid:

```text
MODEL
TOOLS
CONVERSATION
WEB
CLOCK
```

as a permanently visible dashboard unless the information is actually required.

Status should be compact and contextual.

---

# 30. CONTEXTUAL STATUS

Atlas may show compact application status such as:

```text
Online
Local
Using Calculator…
Searching the web…
Generating…
Offline
```

Status should be:

* temporary
* contextual
* compact

Do not create persistent visual noise.

---

# 31. PERFORMANCE RULES

## 31.1 No Backdrop Blur

Do not use:

```css
backdrop-filter
```

for ordinary Atlas UI.

Glassmorphism is explicitly prohibited.

## 31.2 Animation

Prefer:

```text
transform
opacity
```

Avoid:

* expensive filters
* continuous decorative animation
* layout animation

## 31.3 SVG

Use inline SVG for interface icons and Atlas marks where appropriate.

Keep SVGs lightweight.

## 31.4 Rendering

Avoid excessive DOM nesting purely for visual decoration.

## 31.5 Mobile

Avoid effects that significantly increase rendering cost.

---

# 32. Z-INDEX SYSTEM

Use a small controlled hierarchy.

```text
Base:      1
Sidebar:   10
Popover:   20
Drawer:    30
Modal:     50
```

Do not invent arbitrary z-index values throughout the application.

---

# 33. UI STATE MACHINE

Atlas UI states must follow this conceptual model:

```text
IDLE
  ↓
THINKING
  ↓
GENERATING
  ↓
RESPONDING
```

Tool branch:

```text
THINKING
  ↓
USING TOOL
  ↓
TOOL RESULT
  ↓
RESPONDING
```

Search branch:

```text
THINKING
  ↓
SEARCHING
  ↓
RESULT
  ↓
RESPONDING
```

Success:

```text
ACTION
  ↓
SUCCESS
```

Failure:

```text
ACTION
  ↓
ERROR
```

Connection:

```text
ONLINE
  ↓
OFFLINE
```

Offline is an application state, not a conversational message.

---

# 34. IMPLEMENTATION PRIORITY

When implementing the design, follow this order:

## Phase 1 — Foundation

Implement:

* CSS variables
* typography
* spacing
* radii
* borders
* surfaces
* semantic colors
* dark/light modes

## Phase 2 — Brand

Implement:

* Atlas logo
* Micro Mark
* favicon
* assistant mark
* state visuals

## Phase 3 — Application Shell

Implement:

* sidebar
* header
* conversation area
* context drawer

## Phase 4 — Conversation

Implement:

* user message
* Atlas response
* system message
* streaming
* code
* links
* lists
* errors
* success

## Phase 5 — Composer

Implement:

* normal
* focused
* typing
* processing
* disabled
* error

## Phase 6 — Tools

Implement:

* active tool
* completed tool
* failed tool
* expandable tool details

## Phase 7 — Memory / Context

Implement:

* relevant conversation
* memory
* active context
* active tools
* stored information

## Phase 8 — Motion

Implement:

* thinking
* tool activity
* generation
* transitions
* reduced motion

## Phase 9 — Responsive

Implement:

* desktop
* tablet
* mobile

## Phase 10 — Accessibility

Implement:

* focus
* keyboard navigation
* reduced motion
* contrast
* semantic states

---

# 35. NON-NEGOTIABLE IMPLEMENTATION RULES

1. Do not redesign Atlas.
2. Do not introduce a new visual language.
3. Do not replace the Atlas logo.
4. Do not introduce an AI orb.
5. Do not introduce neon.
6. Do not introduce cyberpunk styling.
7. Do not introduce glassmorphism.
8. Do not introduce giant gradients.
9. Do not use generic AI avatars.
10. Do not use generic loading spinners as Atlas identity.
11. Do not create a permanent status dashboard.
12. Do not make every message a heavy card.
13. Do not make Memory a sci-fi visualization.
14. Do not make Tool UI dominate the conversation.
15. Do not break existing Atlas backend functionality for visual changes.
16. Do not modify AtlasBrain for a UI-only change.
17. Do not modify AtlasModel for a UI-only change.
18. Do not modify ToolManager for a UI-only change.
19. Do not modify ConversationService for a UI-only change.
20. Do not change existing API contracts unless explicitly required.
21. Preserve streaming behavior.
22. Preserve conversation persistence.
23. Preserve tool execution.
24. Preserve memory behavior.
25. Preserve model routing.
26. Preserve existing error handling.
27. Keep the UI responsive.
28. Keep the UI keyboard accessible.
29. Respect reduced motion.
30. Do not use `backdrop-filter`.
31. Do not add unnecessary dependencies.
32. Do not rewrite unrelated backend code.
33. Inspect existing implementation before modifying it.
34. Test after each focused implementation phase.
35. Preserve working functionality.

---

# 36. VISUAL SOURCE OF TRUTH

The Atlas Design Sheet defines:

* overall visual appearance
* composition
* component relationships
* hierarchy
* logo presentation
* state presentation
* density
* responsive visual intent
* brand applications

This Markdown document defines:

* exact colors
* exact sizes
* exact spacing
* exact typography
* exact component behavior
* exact responsive rules
* exact accessibility requirements
* exact implementation constraints

If the image and this document disagree on an exact numeric value:

**THIS DOCUMENT WINS.**

If the image communicates a visual relationship that is not explicitly described numerically:

**PRESERVE THE VISUAL RELATIONSHIP.**

---

# 37. CURRENT VISUAL REFERENCE STRUCTURE

The canonical Atlas design reference contains the following major sections:

```text
01 Brand & Logo
02 Logo Construction
03 Micro Mark System
04 Assistant Mark System
05 Color System
06 Typography
07 Iconography
08 Spacing / Geometry
09 Chat UI
10 Sidebar
11 Message Components
12 Input / Composer
13 Tool Use & Memory / Context
14 Responsive Design
15 Thinking / Motion
16 Micro-interactions
17 Dashboard / Home
18 Empty / Loading / Error
19 Light + Dark Mode
20 Accessibility
21 Brand Applications
22 Do / Don't
```

These sections represent the complete visual system.

---

# 38. DESIGN PRINCIPLE

The most important Atlas principle:

> **Atlas should look like a highly refined software product, not like an AI visual effect.**

The interface communicates intelligence through:

* clarity
* context
* precision
* useful activity states
* consistent interaction
* restrained visual language

It does not communicate intelligence through:

* glowing objects
* futuristic decoration
* animated backgrounds
* giant AI symbols
* excessive motion
* visual spectacle

---

# 39. FINAL VISUAL TARGET

The finished Atlas application should visually feel like:

```text
Linear
+
VS Code
+
Notion
+
Atlas-specific identity
```

but must not copy any of them directly.

The final character is:

```text
CALM
INTELLIGENT
PRECISE
RELIABLE
TECHNICAL
PERSONAL
```

---

# 40. FINAL DESIGN LOCK

The Atlas design system is considered locked when all of the following are true:

```text
[ ] Atlas A + trajectory/node identity is preserved
[ ] Micro Mark works at 16px
[ ] Full logo works at large sizes
[ ] Dark mode matches canonical palette
[ ] Light mode matches canonical palette
[ ] Inter is the primary font
[ ] JetBrains Mono is the technical font
[ ] 4px spacing system is used
[ ] 4/6/8px radii are used
[ ] Structural borders are 1px
[ ] Sidebar is 260px expanded
[ ] Sidebar is 64px collapsed
[ ] Context drawer is 280px
[ ] Conversation width is approximately 720–760px
[ ] User messages remain visually restrained
[ ] Atlas messages use Micro Mark identity
[ ] Tool UI remains inline and quiet
[ ] Memory remains productivity-oriented
[ ] Assistant states use Atlas-specific visuals
[ ] Thinking animation is subtle
[ ] No generic AI spinner as primary identity
[ ] No neon
[ ] No cyberpunk
[ ] No glassmorphism
[ ] No AI orb
[ ] No excessive gradients
[ ] No excessive cards
[ ] No permanent status dashboard
[ ] Desktop layout works
[ ] Tablet layout works
[ ] Mobile layout works
[ ] Keyboard navigation works
[ ] Focus states are visible
[ ] Reduced motion works
[ ] Errors are not color-only
[ ] Existing backend behavior remains intact
[ ] Existing API contracts remain intact
[ ] No unnecessary dependencies are introduced
```

---

# 41. IMPLEMENTATION DIRECTIVE

When an implementation agent reads this document:

1. Read this entire document before modifying UI.
2. Inspect the existing web implementation.
3. Compare the existing implementation against this specification.
4. Identify the smallest focused change required.
5. Implement one coherent phase at a time.
6. Test the application after each phase.
7. Preserve backend behavior.
8. Preserve API contracts.
9. Preserve Atlas core architecture.
10. Never invent a competing visual direction.
11. Use the current Atlas Design Sheet as the visual reference.
12. Use this document for exact implementation values.
13. If a visual detail is ambiguous, choose the restrained option.
14. If a choice introduces visual noise, do not make it.
15. If a choice makes Atlas look more like generic AI software, reject it.

---

# 42. FINAL RULE

**DO NOT REDESIGN ATLAS.**

**DO NOT SIMPLIFY THE DESIGN SYSTEM.**

**DO NOT REMOVE THE INFORMATION-RICH VISUAL LANGUAGE.**

**DO NOT TURN ATLAS INTO A GENERIC CHAT UI.**

Implement the existing Atlas visual system faithfully:

**A + trajectory + node**

**deep slate + muted teal**

**Inter + JetBrains Mono**

**sidebar + conversation + contextual information**

**Micro Mark assistant identity**

**quiet tools**

**restrained memory/context**

**subtle functional motion**

**professional software aesthetic**

**no visual spectacle.**

This document and the approved Atlas Design Sheet together constitute the canonical Atlas UI design specification.