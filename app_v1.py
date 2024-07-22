import random
import math
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Token: Een klasse die een enkel token voorstelt.
class Token: 
    def __init__(self, token_id):
        self.token_id = token_id

    def __repr__(self):
        return f"Token({self.token_id})"

# User: Een klasse die een gebruiker voorstelt die tokens kan ontvangen én betalen, met een utility curve.
class User:
    def __init__(self, user_id, balance=10, activity_desire=5):
        self.user_id = user_id
        self.tokens = []
        self.balance = balance
        self.activity_desire = activity_desire
        
    def receive_tokens(self, token):
        self.tokens.append(token)
        
    def pay_token(self, num_tokens=1):
        if self.token_count() >= num_tokens:
            tokens_paid = [self.tokens.pop(0) for _ in range(num_tokens)]
            return tokens_paid
        else:
            return None

    def token_count(self):
        return len(self.tokens)
        
    def activity_utility(self):
        return self.activity_desire * math.log(1 + 1 * self.token_count() * 2 * self.balance)

    def __repr__(self):
        return f"User({self.user_id}, Tokens: {self.tokens})"

# TokenGenerator: Een klasse die nieuwe tokens genereert en verdeelt aan gebruikers.
class TokenGenerator:
    def __init__(self):
        self.current_id = 0
        
    def generate_token(self):
        token = Token(self.current_id)
        self.current_id += 1
        return token
    
    def assign_token_to_user(self, user, num_tokens=1):
        for _ in range(num_tokens):
            token = self.generate_token()
            user.receive_tokens(token)
        
# De Market klasse beheert het kopen en verkopen van tokens tussen gebruikers.
class Market:
    def __init__(self, users, initial_price=1.0, elasticity=0.05):
        self.users = users
        self.price = initial_price
        self.demand = 0
        self.supply = 0
        self.elasticity = elasticity

    def update_price(self):
        if self.demand > self.supply:
            self.price *= (1 + self.elasticity)   # Verhoog de prijs met 10%
        elif self.supply > self.demand:
            self.price *= (1 - self.elasticity)  # Verlaag de prijs met 10%
        # Reset demand en supply na het aanpassen van de prijs
        self.demand = 0
        self.supply = 0

    def buy_token(self, buyer):
        sellers = self.users[:]
        random.shuffle(sellers)
        for seller in sellers:
            if seller != buyer and seller.token_count() > 0:
                if buyer.balance >= self.price:
                    token = seller.pay_token()
                    if token:
                        buyer.receive_tokens(token[0])
                        buyer.balance -= self.price
                        seller.balance += self.price
                        st.write(f"{buyer.user_id} heeft een token gekocht van {seller.user_id} voor {self.price:.2f} euro.")
                        self.demand += 1
                        self.supply -= 1
                        return True, "Success"
                else:
                    return False, "Niet genoeg geld om een token te kopen."
        return False, "Geen tokens beschikbaar van andere gebruikers."

    def sell_token(self, seller):
        for buyer in self.users:
            if buyer != seller and buyer.balance >= self.price:
                token = seller.pay_token()
                if token:
                    buyer.receive_tokens(token[0])
                    buyer.balance -= self.price
                    seller.balance += self.price
                    st.write(f"{seller.user_id} heeft een token verkocht aan {buyer.user_id} voor {self.price:.2f} euro.")
                    self.demand -= 1
                    self.supply += 1
                    return True, "Success"
        return False, "Geen kopers beschikbaar voor de tokens."

    def adjust_market_price(self):
        self.update_price()
        st.write(f"De nieuwe marktprijs voor tokens is {self.price:.2f} euro.")
    
# Activity Pool: X% kans dat bij deelname je een token krijgt, je kan elke iteratie deelnemen als user        
class ActivityPool:
    def __init__(self, users, token_generator, market, probability=0.4, activity_price=2, received_tokens=5, utility_threshold=10):
        self.users = users
        self.token_generator = token_generator
        self.market = market
        self.probability = probability
        self.activity_price = activity_price
        self.received_tokens = received_tokens
        self.utility_threshold = utility_threshold

    def assign_tokens(self, user):
        tokens_paid = user.pay_token(num_tokens=self.activity_price)
        if tokens_paid:
            st.write(f"{user.user_id} heeft {self.activity_price} token(s) betaald.")
            if random.random() < self.probability:
                self.token_generator.assign_token_to_user(user, num_tokens=self.received_tokens)
                st.write(f"{user.user_id} heeft {self.received_tokens} token(s) gekregen.")
            else:
                st.write(f"{user.user_id} heeft geen tokens gekregen.")
        else:
            st.write(f"{user.user_id} heeft niet genoeg tokens om deel te nemen.")
            # Probeer een token te kopen van een andere gebruiker
            success, message = self.market.buy_token(user)
            if success:
                st.write(f"{user.user_id} heeft een token gekocht om deel te nemen.")
                self.assign_tokens(user)
            else:
                st.write(f"{user.user_id} kon geen token kopen om deel te nemen. Reden: {message}")

    def participate(self, user):
        if user.activity_utility() < self.utility_threshold:
            st.write(f"{user.user_id} heeft besloten niet deel te nemen vanwege lage utility.")
            # Probeer een token te kopen van een andere gebruiker
            success, message = self.market.buy_token(user)
            if success:
                st.write(f"{user.user_id} heeft een token gekocht om zijn utility te verhogen.")
                # Herbereken de utility na het kopen van de token
                if user.activity_utility() >= self.utility_threshold:
                    st.write(f"{user.user_id} heeft nu genoeg utility om deel te nemen.")
                    self.assign_tokens(user)
                else:
                    st.write(f"{user.user_id} heeft nog steeds een te lage utility om deel te nemen.")
            else:
                st.write(f"{user.user_id} kon geen token kopen om deel te nemen. Reden: {message}")
        else:
            self.assign_tokens(user)     
    
# Initial Release class: 
class InitialRelease:
    def __init__(self, users, token_generator):
        self.users = users
        self.token_generator = token_generator
        
    def distribute_tokens(self, num_tokens):
        for _ in range(num_tokens):
            user = random.choice(self.users) # voeg de num_tokens op een random manier toe
            self.token_generator.assign_token_to_user(user)
        st.write(f"Inital release of {num_tokens} tokens completed.")        
        

# Functie om resultaten te analyseren en te visualiseren
def analyze_and_visualize_results(results):
    # Converteer de resultaten naar een DataFrame
    data = []
    for sim_index, final_states in enumerate(results):
        for state in final_states:
            data.append({
                'simulation': sim_index,
                'user_id': state['user_id'],
                'tokens': state['tokens'],
                'balance': state['balance']
            })
    
    df = pd.DataFrame(data)
    
    # Analyseer de spreiding en verwachtingen
    summary = df.groupby('user_id').agg({
        'tokens': ['mean', 'std'],
        'balance': ['mean', 'std']
    })
    summary.columns = ['_'.join(col) for col in summary.columns]
    
    st.write("Samenvatting van de resultaten per gebruiker:")
    st.write(summary)
    
    # Visualisatie van de resultaten
    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='tokens', kde=True)
    plt.title('Distributie van Tokens over Simulaties')
    plt.xlabel('Aantal Tokens')
    plt.ylabel('Frequentie')
    st.pyplot(plt)

    plt.figure(figsize=(12, 6))
    sns.histplot(data=df, x='balance', kde=True)
    plt.title('Distributie van Balances over Simulaties')
    plt.xlabel('Balance')
    plt.ylabel('Frequentie')
    st.pyplot(plt)

# Monte Carlo Simulatie functie
def monte_carlo_simulation(activity_pool, initial_release, iterations, simulations=1000):
    initial_release.distribute_tokens(20)
    
    results = []
    
    for _ in range(simulations):
        user_states = []
        for user in activity_pool.users:
            user_states.append({
                'user_id': user.user_id,
                'tokens': user.token_count(),
                'balance': user.balance
            })
        
        for _ in range(iterations):
            for user in activity_pool.users:
                if random.random() < activity_pool.probability:
                    activity_pool.participate(user)
            activity_pool.market.adjust_market_price()
        
        final_states = []
        for user in activity_pool.users:
            final_states.append({
                'user_id': user.user_id,
                'tokens': user.token_count(),
                'balance': user.balance
            })
        
        results.append(final_states)
        
        # Reset user states for next simulation
        for state, user in zip(user_states, activity_pool.users):
            user.tokens = [Token(i) for i in range(state['tokens'])]
            user.balance = state['balance']
    
    return results

# Streamlit interface
st.title("Tokenomics Simulatie voor $HEALTH")

num_users = st.slider("Aantal gebruikers", 1, 50, 3)
elasticity = st.slider("Elasticiteit", 0.0, 1.0, 0.1)
probability = st.slider("Waarschijnlijkheid van activiteitspool", 0.0, 1.0, 0.4)
iterations = st.slider("Aantal iteraties", 1, 50, 10)
simulations = st.slider("Aantal simulaties", 1, 100, 50)

if st.button("Start simulatie"):
    with st.spinner("Simulatie wordt uitgevoerd..."):
        # Maak users aan
        users = [User(f"User{i+1}") for i in range(num_users)]
    
        # Maak een token generator aan 
        token_generator = TokenGenerator()
    
        # Creëer een markt met opgegeven elasticiteit
        market = Market(users, elasticity=elasticity)
    
        # Maak een ActivityPool aan met opgegeven probability
        activity_pool = ActivityPool(users, token_generator, market, probability=probability)
    
        # Maak een InitialRelease aan
        initial_release = InitialRelease(users, token_generator)
    
        # Monte Carlo simulatie
        results = monte_carlo_simulation(activity_pool, initial_release, iterations, simulations)
       
        st.write("Simulatie voltooid.")
       
        # Analyseer en visualiseer de resultaten
        analyze_and_visualize_results(results)
       
        # Toon enkele resultaten
        for user in users:
            st.write(f"{user.user_id} heeft {user.token_count()} tokens en {user.balance} balance.")