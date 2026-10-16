import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import markdown
from openai import OpenAI
import streamlit as st

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Squadra di Agenti IA per la Didattica", page_icon="🤖", layout="wide"
)

# ---------------------------------------------------------
# BARRA LATERALE (SIDEBAR): GESTIONE CREDENZIALI
# ---------------------------------------------------------
st.sidebar.header("🔑 Configurazione Credenziali")

openrouter_api_key = st.sidebar.text_input(
    "OpenRouter API Key", type="password", help="Inserisci la tua chiave API di OpenRouter"
)
sender_email = st.sidebar.text_input(
    "Email Gmail Mittente", help="Es. tuonome@gmail.com"
)
email_password = st.sidebar.text_input(
    "App Password Gmail (16 caratteri)",
    type="password",
    help="Password per app generata dalle impostazioni di Google",
)
recipient_email = st.sidebar.text_input(
    "Email Destinatario", help="Indirizzo a cui inviare il report finale"
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 *Nota:* Per Gmail è necessario utilizzare una **Password per le app** di 16 caratteri e non la normale password dell'account."
)

# ---------------------------------------------------------
# INTERFACCIA PRINCIPALE
# ---------------------------------------------------------
st.title("🤖 Squadra di Agenti IA per la Didattica")
st.markdown(
    "Questa applicazione sfrutta un workflow multi-agente tramite **OpenRouter** per analizzare un tema didattico, estrarre punti chiave e redigere un post divulgativo per i docenti, permettendo infine l'invio automatico via email."
)

# Campo di testo per l'argomento della lezione
topic = st.text_input(
    "Inserisci l'argomento o il tema della lezione:",
    placeholder="Es. L'uso critico dell'Intelligenza Artificiale nella didattica filosofica",
)

# Inizializzazione dello stato della sessione per preservare i dati
if "key_points" not in st.session_state:
    st.session_state.key_points = ""
if "blog_post" not in st.session_state:
    st.session_state.blog_post = ""

# ---------------------------------------------------------
# LOGICA MULTI-AGENTE (OPENROUTER)
# ---------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    generate_btn = st.button("🚀 Genera Report con Agenti", use_container_width=True)

if generate_btn:
    # Controllo validazione input preliminari
    if not openrouter_api_key:
        st.error(
            "⚠️ Inserisci la OpenRouter API Key nella barra laterale prima di procedere."
        )
    elif not topic:
        st.error("⚠️ Inserisci un argomento valido per la lezione nell'apposito campo.")
    else:
        try:
            # Inizializzazione del client OpenAI puntando a OpenRouter
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_api_key,
            )

            # AGENTE 1: IL RICERCATORE
            with st.spinner(
                "Agente 1 (Ricercatore) in azione: analisi del tema..."
            ):
                prompt_ricercatore = f"""
                Sei un esperto ricercatore in didattica. Analizza il seguente tema: '{topic}'.
                Restituisce esattamente 3 punti chiave sintetici ed efficaci.
                Usa rigorosamente il grassetto in Markdown per i punti chiave.
                """
                response_1 = client.chat.completions.create(
                    model="openrouter/auto",
                    messages=[{"role": "user", "content": prompt_ricercatore}],
                )
                st.session_state.key_points = response_1.choices[
                    0
                ].message.content

            # AGENTE 2: LO SCRITTORE
            with st.spinner(
                "Agente 2 (Scrittore) in azione: stesura del post divulgativo..."
            ):
                prompt_scrittore = f"""
                Agendo come redattore esperto per docenti, prendi i seguenti 3 punti chiave generati dal ricercatore sull'argomento '{topic}':
                
                {st.session_state.key_points}
                
                Redigi un post divulgativo fluido e coinvolgente per docenti della durata di lettura breve, di circa 100 parole.
                """
                response_2 = client.chat.completions.create(
                    model="openrouter/auto",
                    messages=[{"role": "user", "content": prompt_scrittore}],
                )
                st.session_state.blog_post = response_2.choices[0].message.content

            st.success(
                "✅ Gli agenti hanno completato con successo l'analisi e la stesura del report!"
            )

        except Exception as e:
            st.error(
                f"❌ Errore durante la comunicazione con le API di OpenRouter: {e}"
            )

# Mostra i risultati salvati nello session_state se presenti
if st.session_state.key_points or st.session_state.blog_post:
    st.markdown("### 📊 Risultati Generati dagli Agenti")

    tab1, tab2 = st.tabs(["🔍 Agente 1: Punti Chiave", "✍️ Agente 2: Post Divulgativo"])

    with tab1:
        st.markdown(st.session_state.key_points)

    with tab2:
        st.markdown(st.session_state.blog_post)

# ---------------------------------------------------------
# SISTEMA DI INVIO EMAIL (SMTP GMAIL)
# ---------------------------------------------------------
with col2:
    send_email_btn = st.button("📧 Invia Report via Email", use_container_width=True)

if send_email_btn:
    # Validazione credenziali email e presenza contenuti
    if not sender_email or not email_password or not recipient_email:
        st.error(
            "⚠️ Inserisci tutte le credenziali email (Mittente, App Password, Destinatario) nella barra laterale."
        )
    elif not st.session_state.key_points or not st.session_state.blog_post:
        st.error(
            "⚠️ Prima di inviare l'email, genera i contenuti tramite il pulsante 'Genera Report con Agenti'."
        )
    else:
        with st.spinner("Invio dell'email in corso..."):
            try:
                # Conversione dei testi Markdown generati in HTML pulito
                html_key_points = markdown.markdown(st.session_state.key_points)
                html_blog_post = markdown.markdown(st.session_state.blog_post)

                # Costruzione del template HTML curato ed elegante
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            color: #333333;
                            line-height: 1.6;
                            background-color: #f4f4f9;
                            margin: 0;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 600px;
                            background: #ffffff;
                            margin: 0 auto;
                            padding: 30px;
                            border-radius: 8px;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
                        }}
                        h2 {{
                            color: #1a73e8;
                            border-bottom: 2px solid #eaeaea;
                            padding-bottom: 8px;
                            margin-top: 0;
                        }}
                        .section-ricercatore {{
                            background-color: #e8f0fe;
                            border-left: 5px solid #1a73e8;
                            padding: 15px 20px;
                            margin-bottom: 20px;
                            border-radius: 4px;
                        }}
                        .section-scrittore {{
                            background-color: #e6f4ea;
                            border-left: 5px solid #34a853;
                            padding: 15px 20px;
                            margin-bottom: 20px;
                            border-radius: 4px;
                        }}
                        .footer {{
                            font-size: 12px;
                            color: #777777;
                            text-align: center;
                            margin-top: 30px;
                            border-top: 1px solid #eaeaea;
                            padding-top: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>🤖 Report Didattico: {topic}</h2>
                        
                        <div class="section-ricercatore">
                            <h3 style="margin-top:0; color: #174ea6;">🔍 Agente 1: Punti Chiave (Ricercatore)</h3>
                            {html_key_points}
                        </div>
                        
                        <div class="section-scrittore">
                            <h3 style="margin-top:0; color: #137333;">✍️ Agente 2: Post Divulgativo (Scrittore)</h3>
                            {html_blog_post}
                        </div>
                        
                        <div class="footer">
                            <p>Email generata automaticamente dalla Squadra di Agenti IA per la Didattica.</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                # Configurazione del messaggio email MIME
                msg = MIMEMultipart("alternative")
                msg["Subject"] = (
                    f"🤖 Report Didattico Agenti IA: {topic[:30]}..."
                )
                msg["From"] = sender_email
                msg["To"] = recipient_email

                # Allegato HTML
                part_html = MIMEText(html_content, "html", "utf-8")
                msg.attach(part_html)

                # Connessione sicura SMTP e invio dell'email tramite porta 465 (SSL)
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(sender_email, email_password)
                    server.sendmail(
                        sender_email, recipient_email, msg.as_string()
                    )

                st.success(
                    f"📧 Email inviata con successo a **{recipient_email}**!"
                )

            except Exception as e:
                st.error(f"❌ Errore durante l'invio dell'email: {e}")