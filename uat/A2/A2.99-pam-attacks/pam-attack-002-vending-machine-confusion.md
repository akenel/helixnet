# PAM ATTACK #002 — The Vending Machine Confusion

## Setup
New vending machine just installed. Felix said "it's easy."
First customer approaches it while Pam watches from counter.

## The Attack
1. Tourist inserts 10 CHF coin
2. Machine: *beep*
3. Tourist presses B4
4. Machine displays: "PRODUKT NICHT VERFÜGBAR"
5. Tourist looks at Pam
6. Pam: "Umm... try B5?"
7. Tourist presses B5
8. Machine: *whirring sound*
9. Out drops: CBD dog treats
10. Tourist: "I wanted the lighter..."
11. Pam: "Oh! Those are... also great?"
12. Tourist: "I don't have a dog."
13. Pam: "...gift?"
14. Machine: *beeps* "WECHSELGELD: 3.50 CHF"
15. 350 Rappen coins pour out
16. Tourist scrambles to catch coins
17. One rolls under the vending machine
18. Pam: *grabs broom* "I've got it..."
19. Broom knocks into display
20. Lighter falls from B4 slot
21. Pam: "...See? It worked!"

## UAT Points Tested
- Vending machine error messages (DE→EN)
- Wrong product dispensed recovery
- Change handling (coins)
- Physical intervention edge case

## Comedy Rating: ⭐⭐⭐⭐⭐
