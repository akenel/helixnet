# Nano Banana Prompts -- Pizza Planet Postcards
## Banksy x Bauhaus Art Direction

---

## CARD A: "The Oven" (Hero Card)

### Prompt (no base image):
```
Banksy-style stencil art of a wood-fired pizza being pulled from a traditional brick oven with a long wooden peel. High contrast black and white silhouette. Flour dust particles floating in the air. Flames visible inside the oven mouth. Bauhaus geometric color blocks overlaid -- a green triangle, a white circle, and a red rectangle (Italian flag colors) intersecting the composition. Gritty street art texture on aged plaster wall. No text. Landscape orientation 3:2 ratio.
```

### Prompt (with base photo -- use after tonight's visit):
```
Transform this photo into Banksy-style stencil street art. Convert to high contrast black and white silhouette. Add Bauhaus geometric overlays in Italian flag colors (green triangle, white circle, red rectangle). Keep the composition but add gritty plaster wall texture, spray paint drips, and stencil edge artifacts. No text. Maintain landscape 3:2 ratio.
```

### Base photo to shoot tonight:
- The wood-fired oven with flames visible
- A pizza being pulled out on the peel
- Shoot from slightly below, dramatic angle

---

## CARD B: "The Handover" (Street Card)

### Prompt (no base image):
```
Bauhaus geometric art poster of an Italian takeaway pizza scene. A pizza box being handed across a counter, deconstructed into geometric shapes -- circles for the pizza, triangles for hands, rectangles for the counter and box. Color palette: terracotta orange, cream white, deep burgundy, charcoal black. Bold black outlines separating each geometric form. Kandinsky meets Italian street food. Flat design, no gradients, no shadows. Clean vector aesthetic. No text. Landscape orientation 3:2 ratio.
```

### Prompt (with base photo):
```
Deconstruct this photo into Bauhaus geometric art. Replace organic forms with circles, triangles, and rectangles. Use a warm palette of terracotta, cream, burgundy, and charcoal. Bold black outlines between shapes. Kandinsky-style composition. Flat colors, no gradients. No text. Landscape 3:2 ratio.
```

### Base photo to shoot tonight:
- The counter/window where takeaway boxes are handed over
- Or the storefront from across the street
- Capture the human interaction moment

---

## CARD C: "The Hands" (Soul Card)

### Prompt (no base image):
```
Banksy stencil art of two weathered Italian hands kneading pizza dough on a flour-dusted wooden surface. Black and white high contrast silhouette. Subtle Italian flag color wash bleeding through -- green tint on left third, white center, red tint on right third, very faint like watercolor underneath the stencil. Single overhead spotlight creating dramatic shadows. Minimalist composition, lots of negative space. Street art on concrete wall texture. No text. Landscape orientation 3:2 ratio.
```

### Prompt (with base photo):
```
Transform this photo into minimalist Banksy stencil art. High contrast black and white. Add a faint Italian tricolore wash (green-white-red, left to right) bleeding underneath like watercolor. Concrete wall texture. Dramatic shadows. Lots of negative space. No text. Landscape 3:2 ratio.
```

### Base photo to shoot tonight:
- Ciccio's hands working dough (ask permission, people love this)
- Or any close-up of pizza-making hands
- Overhead angle, focus on hands and dough only

---

## GENERAL NB TIPS

1. **Aspect ratio**: Always specify "landscape 3:2 ratio" -- our cards are 137.6 x 93mm
2. **No text in image**: We add text in HTML, AI text always looks bad
3. **High contrast**: Stencil art needs strong black/white separation to print clean
4. **Italian flag colors**: Green #009246, White #F4F5F0, Red #CE2B37 -- reference only, NB will interpret
5. **Resolution**: Generate at highest available resolution
6. **Variations**: Run each prompt 3-4 times, pick the best one

---

## FILE NAMING

Save NB outputs as:
```
images/card-A-oven-v1.png
images/card-A-oven-v2.png
images/card-B-handover-v1.png
images/card-B-handover-v2.png
images/card-C-hands-v1.png
images/card-C-hands-v2.png
```

After tonight's visit, photo-based versions:
```
images/card-A-oven-real-v1.png
images/card-B-handover-real-v1.png
images/card-C-hands-real-v1.png
```

---

## THE PIPELINE

```
Tonight (before visit):     Prompt-only → NB → prototype images → test print
Tonight (at Pizza Planet):  Shoot base photos (oven, counter, hands)
After visit:                Plug USB → Tigs pulls photos → photo-based prompts → NB → final images
Monday:                     Print full kit at ISOTTO
```

*"Ciccio ha sfamato mezza Trapani" -- and now his postcards feed the tourists.*

---

## ROUND 2: REAL PHOTO-BASED CARDS (Visit 1 - Feb 1, 2026)

Source photos from tonight's visit. Upload each photo to NB and paste the prompt.

---

## CARD D: "La Squadra" (The Crew)

### Source photo: `artifacts/photo_6_2026-02-01_19-28-54.jpg`
The full kitchen -- 4-5 guys in white, wood-fired oven blazing center frame, stacked pizza boxes.

### NB Prompt:
```
Transform this photo into Banksy-style street art stencil. High contrast black and white silhouette treatment on the figures. Keep the flames in the oven as the only warm colour element -- deep orange and red glow. The rest is pure black and white stencil on aged concrete wall texture. Spray paint drip effects on the bottom edge. Preserve the composition and energy of the scene -- multiple figures working around the central oven. No text. Landscape orientation 3:2 ratio.
```

### Card back theme:
- Series name: "La Squadra"
- Quote: "Cinque uomini, un forno, una missione." / "Five men, one oven, one mission."

---

## CARD E: "Il Maestro" (The Master)

### Source photo: `artifacts/photo_10_2026-02-01_19-28-54.jpg`
The bearded guy with tattooed arms at the register, crew visible behind at the oven.

### NB Prompt:
```
Transform this photo into Bauhaus geometric art. Deconstruct the central figure into bold geometric shapes -- circles for the head, triangles for the torso, rectangles for the arms and counter. Use a palette of charcoal black, warm terracotta, cream white, and deep burgundy. The oven glow in the background becomes an abstract orange circle. Bold black outlines between all shapes. Kandinsky meets Italian street food. Flat colours, no gradients, no shadows. No text. Landscape orientation 3:2 ratio.
```

### Card back theme:
- Series name: "Il Maestro"
- Quote: "Dietro ogni grande pizza, un grande pizzaiolo." / "Behind every great pizza, a great pizzaiolo."

---

## CARD F: "La Preparazione" (The Prep)

### Source photo: `artifacts/photo_8_2026-02-01_19-28-54.jpg`
Overhead prep line -- raw dough, toppings in steel containers, three pizzas being assembled.

### NB Prompt:
```
Transform this overhead food preparation photo into minimalist Banksy stencil art. Convert to high contrast black and white. The circular pizzas become bold black disc shapes. The steel topping containers become geometric rectangles. Add a subtle Italian tricolore wash bleeding underneath -- green tint left, white center, red tint right -- very faint like watercolor under the stencil. Overhead perspective, dramatic contrast between the white dough and dark surface. Flour dust as spray paint texture. No text. Landscape orientation 3:2 ratio.
```

### Card back theme:
- Series name: "La Preparazione"
- Quote: "L'arte inizia prima del forno." / "The art begins before the oven."

---

## FILE NAMING (Round 2)

Save NB outputs as:
```
images/card-D-crew-v1.jpg
images/card-E-maestro-v1.jpg
images/card-F-prep-v1.jpg
```

---

## THE 6-CARD COLLECTION

| Card | Name | Source | Style | QR Channel |
|------|------|-------|-------|------------|
| A | The Oven | NB prompt-only | Banksy stencil | Google Maps |
| B | The Handover | NB prompt-only | Bauhaus geometric | TripAdvisor |
| C | The Hands | NB prompt-only | Banksy minimal | Facebook |
| D | La Squadra | Real photo #6 | Banksy + colour oven | Google Maps |
| E | Il Maestro | Real photo #10 | Bauhaus deconstruction | TripAdvisor |
| F | La Preparazione | Real photo #8 | Banksy + tricolore wash | Facebook |

Cards A-C: Generic pizza art (works for any pizzeria)
Cards D-F: Authentic Pizza Planet (only works for Ciccio's crew)

*The collector wants all six.*
