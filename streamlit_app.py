import streamlit as st
import random
import stripe
import firebase_admin
from firebase_admin import credentials, firestore

# Configuração da API do Stripe
STRIPE_SECRET_KEY = "sua_chave_secreta_do_stripe"
stripe.api_key = STRIPE_SECRET_KEY

# Configuração do Firebase Firestore
cred = credentials.Certificate("seu_arquivo_json_de_credenciais.json")  # Substitua pelo caminho correto do JSON
firebase_admin.initialize_app(cred)
db = firestore.client()

# Contador de números vendidos e disponíveis
total_numeros = 200
vendidos = db.collection("numeros_vendidos").stream()
numeros_vendidos = len([doc.id for doc in vendidos])
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
        numeros_sorteados = random.sample(range(1, total_numeros + 1), pacotes[pacote_escolhido])
        numeros_str = ", ".join(map(str, numeros_sorteados))
        
        # Salvar no Firestore
        db.collection("clientes").document(email).set({
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "numeros": numeros_str,
            "pagamento_confirmado": False
        })
        for num in numeros_sorteados:
            db.collection("numeros_vendidos").document(str(num)).set({"reservado": True})
        
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
            db.collection("clientes").document(email).update({"pagamento_confirmado": True})
        except Exception as e:
            st.error(f"Payment error: {e}" if language == "English" else f"Erro no pagamento: {e}")

st.subheader(confirmed_clients)
clientes_confirmados = db.collection("clientes").where("pagamento_confirmado", "==", True).stream()
for cliente in clientes_confirmados:
    data = cliente.to_dict()
    st.write(f"✅ {data['nome']} - {data['email']} - Números: {data['numeros']}")
