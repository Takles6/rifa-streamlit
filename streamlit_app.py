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
conn = sqlite3.connect("rifa.db")
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

def enviar_email(email, nome, numeros):
    remetente = "seu_email@gmail.com"
    senha = "sua_senha"
    
    mensagem = f"Olá {nome},\n\nObrigado por participar da nossa rifa! Seus números da sorte são: {numeros}. \n\nBoa sorte!\n\nEquipe Russian Manicure"
    msg = MIMEText(mensagem)
    msg["Subject"] = "Confirmação da Rifa"
    msg["From"] = remetente
    msg["To"] = email
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(remetente, senha)
        server.sendmail(remetente, email, msg.as_string())
        server.quit()
        st.success("E-mail de confirmação enviado!")
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")

# Contador de números vendidos e disponíveis
total_numeros = 200
c.execute("SELECT COUNT(*) FROM numeros_vendidos")
numeros_vendidos = c.fetchone()[0]
numeros_disponiveis = total_numeros - numeros_vendidos

# Streamlit UI
st.title("🎟️ Rifa de páscoa Luize Beauty")

st.subheader(f"🔢 Números Disponíveis: {numeros_disponiveis} / {total_numeros}")

st.subheader("🏆 Prêmios")
st.write("🎁 **Deluxe membership - 6 Atendimentos de Russian Manicure** (Valor: $600)")

st.subheader("📜 Regras e Datas do Sorteio")
st.write("📅 Sorteio será realizado no dia **XX/XX/XXXX** ao vivo no Instagram.")
st.write("✅ O número sorteado será escolhido aleatoriamente e publicado em nossas redes sociais.")
st.write("📩 Apenas números pagos serão confirmados no sorteio.")

nome = st.text_input("Nome")
email = st.text_input("E-mail")
telefone = st.text_input("Telefone")

# Pacotes fechados de números
pacotes = {
    "1 Número - $10": 1,
    "5 Números - $47": 5,
    "10 Números - $90": 10,
    "20 Números - $170": 20,
    "50 Números - $375": 50,
}

pacote_escolhido = st.selectbox("Escolha seu pacote", list(pacotes.keys()))

if st.button("Reservar Números"):
    if nome and email and telefone:
        numeros_sorteados = random.sample(set(range(1, total_numeros + 1)) - set(c.execute("SELECT numero FROM numeros_vendidos").fetchall()), pacotes[pacote_escolhido])
        numeros_str = ", ".join(map(str, numeros_sorteados))
        
        # Salvar no banco de dados
        c.execute("INSERT INTO clientes (nome, email, telefone, numeros, pagamento_confirmado) VALUES (?, ?, ?, ?, ?)",
                  (nome, email, telefone, numeros_str, 0))
        for num in numeros_sorteados:
            c.execute("INSERT INTO numeros_vendidos (numero) VALUES (?)", (num,))
        conn.commit()
        
        st.success(f"Números reservados: {numeros_str}. Faça o pagamento para confirmar.")
    else:
        st.error("Por favor, preencha todos os campos.")

# Área de pagamento
st.subheader("💳 Pagamento")
pagamento_metodo = st.selectbox("Escolha o método de pagamento", ["Transferência Bancária", "Cartão de Crédito (Stripe)"])

if st.button("Confirmar Pagamento"):
    if pagamento_metodo == "Transferência Bancária":
        st.success("Envie o comprovante para validar a reserva.")
    else:
        try:
            pagamento = stripe.PaymentIntent.create(
                amount=int(pacotes[pacote_escolhido] * 10 * 100),  # Converter para centavos
                currency="usd",
                payment_method_types=["card"],
            )
            st.success("Pagamento processado com sucesso!")
            c.execute("UPDATE clientes SET pagamento_confirmado = 1 WHERE email = ?", (email,))
            conn.commit()
            enviar_email(email, nome, numeros_str)
        except Exception as e:
            st.error(f"Erro no pagamento: {e}")

# Mostrar lista de clientes pagantes
st.subheader("📜 Clientes Confirmados")
c.execute("SELECT nome, email, numeros FROM clientes WHERE pagamento_confirmado = 1")
clientes_confirmados = c.fetchall()
for cliente in clientes_confirmados:
    st.write(f"✅ {cliente[0]} - {cliente[1]} - Números: {cliente[2]}")
