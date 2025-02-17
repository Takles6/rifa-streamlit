import streamlit as st
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText
import stripe

# Configuração da API do Stripe
STRIPE_SECRET_KEY = "sua_chave_secreta_do_stripe"
stripe.api_key = STRIPE_SECRET_KEY

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("rifa.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT, 
                email TEXT, 
                telefone TEXT, 
                numeros TEXT, 
                pagamento_confirmado INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS numeros_vendidos (
                numero INTEGER PRIMARY KEY)''')
conn.commit()

# Contador de números vendidos e disponíveis
total_numeros = 200
c.execute("SELECT COUNT(*) FROM numeros_vendidos")
numeros_vendidos = c.fetchone()[0]
numeros_disponiveis = total_numeros - numeros_vendidos

# Seleção de idioma
language = st.sidebar.selectbox("Select Language / Selecionar Idioma", ["English", "Português"])

if language == "English":
    title = "🎟️ Easter Raffle - Luize Beauty"
    numbers_available = "🔢 Numbers Available"
    prize_section = "🏆 Prizes"
    prize_info = "🎁 **Deluxe membership - 6 Russian Manicure Sessions** (Value: $600)"
    rules_section = "📜 Rules & Draw Date"
    draw_info = "📅 The draw will take place on **XX/XX/XXXX** live on Instagram."
    confirmation_info = "📩 Only paid numbers will be confirmed in the draw."
    name_label = "Name"
    email_label = "E-mail"
    phone_label = "Phone"
    select_package = "Choose your package"
    reserve_button = "Reserve Numbers"
    payment_section = "💳 Payment"
    payment_method = "Choose payment method"
    confirm_payment = "Confirm Payment"
    confirmed_clients = "📜 Confirmed Clients"
else:
    title = "🎟️ Rifa de Páscoa - Luize Beauty"
    numbers_available = "🔢 Números Disponíveis"
    prize_section = "🏆 Prêmios"
    prize_info = "🎁 **Deluxe membership - 6 Atendimentos de Russian Manicure** (Valor: $600)"
    rules_section = "📜 Regras e Datas do Sorteio"
    draw_info = "📅 Sorteio será realizado no dia **XX/XX/XXXX** ao vivo no Instagram."
    confirmation_info = "📩 Apenas números pagos serão confirmados no sorteio."
    name_label = "Nome"
    email_label = "E-mail"
    phone_label = "Telefone"
    select_package = "Escolha seu pacote"
    reserve_button = "Reservar Números"
    payment_section = "💳 Pagamento"
    payment_method = "Escolha o método de pagamento"
    confirm_payment = "Confirmar Pagamento"
    confirmed_clients = "📜 Clientes Confirmados"

st.title(title)

st.subheader(f"{numbers_available}: {numeros_disponiveis} / {total_numeros}")

st.subheader(prize_section)
st.write(prize_info)

st.subheader(rules_section)
st.write(draw_info)
st.write(confirmation_info)

nome = st.text_input(name_label)
email = st.text_input(email_label)
telefone = st.text_input(phone_label)

pacotes = {
    "1 Número - $10": 1,
    "5 Números - $47": 5,
    "10 Números - $90": 10,
    "20 Números - $170": 20,
    "50 Números - $375": 50,
}

pacote_escolhido = st.selectbox(select_package, list(pacotes.keys()))

if st.button(reserve_button):
    if nome and email and telefone:
        numeros_sorteados = random.sample(set(range(1, total_numeros + 1)) - set(x[0] for x in c.execute("SELECT numero FROM numeros_vendidos").fetchall()), pacotes[pacote_escolhido])
        numeros_str = ", ".join(map(str, numeros_sorteados))
        
        c.execute("INSERT INTO clientes (nome, email, telefone, numeros, pagamento_confirmado) VALUES (?, ?, ?, ?, ?)",
                  (nome, email, telefone, numeros_str, 0))
        for num in numeros_sorteados:
            c.execute("INSERT INTO numeros_vendidos (numero) VALUES (?)", (num,))
        conn.commit()
        
        st.success(f"{numeros_str}. {confirmation_info}")
    else:
        st.error("Please fill in all fields." if language == "English" else "Por favor, preencha todos os campos.")

st.subheader(payment_section)
pagamento_metodo = st.selectbox(payment_method, ["Bank Transfer" if language == "English" else "Transferência Bancária", "Credit Card (Stripe)"])

if st.button(confirm_payment):
    if pagamento_metodo == "Transferência Bancária" or pagamento_metodo == "Bank Transfer":
        st.success("Send proof of payment to validate the reservation." if language == "English" else "Envie o comprovante para validar a reserva.")
    else:
        try:
            pagamento = stripe.PaymentIntent.create(
                amount=int(pacotes[pacote_escolhido] * 10 * 100),
                currency="usd",
                payment_method_types=["card"],
            )
            st.success("Payment successfully processed!" if language == "English" else "Pagamento processado com sucesso!")
            c.execute("UPDATE clientes SET pagamento_confirmado = 1 WHERE email = ?", (email,))
            conn.commit()
        except Exception as e:
            st.error(f"Payment error: {e}" if language == "English" else f"Erro no pagamento: {e}")

st.subheader(confirmed_clients)
c.execute("SELECT nome, email, numeros FROM clientes WHERE pagamento_confirmado = 1")
clientes_confirmados = c.fetchall()
for cliente in clientes_confirmados:
    st.write(f"✅ {cliente[0]} - {cliente[1]} - Números: {cliente[2]}")