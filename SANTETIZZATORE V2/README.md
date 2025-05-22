# SANTETIZZATORE V2

## Demo Animazione di Caricamento

Questa è la schermata iniziale di caricamento per l'app infotainment SANTETIZZATORE, progettata per Raspberry Pi.

### Come Eseguire
1. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```
2. Aggiungi le tue risorse:
   - Inserisci la tua GIF dell'icona dell'aureola animata come `assets/halo_icon.gif`
   - Inserisci la tua GIF dello spinner di caricamento come `assets/loading_spinner.gif`
3. Avvia l'app:
   ```bash
   python main.py
   ```

### Personalizzazione
- Aggiorna le GIF nella cartella `assets/` per cambiare l'animazione.
- Modifica colori, font e layout in `main.py` secondo le esigenze del tuo dispositivo.

---

## Processo di Traduzione e Scelte di Implementazione

Questa versione dell'app e della documentazione è stata completamente tradotta in italiano. Tutti i testi visibili all'utente, i messaggi, i commenti e la documentazione sono stati sostituiti con l'italiano. 

- **Metodo**: La traduzione è stata effettuata direttamente nel codice (hardcoded), senza l'uso di sistemi di localizzazione come gettext o Qt Linguist, poiché l'applicazione deve funzionare solo in italiano.
- **Asset e Font**: Le cartelle `assets` e `fonts` sono rimaste invariate, poiché i collegamenti alle risorse sono già integrati nel codice.
- **Funzionalità**: Nessuna logica di programma è stata modificata durante la traduzione; solo i testi e i commenti sono stati aggiornati. 