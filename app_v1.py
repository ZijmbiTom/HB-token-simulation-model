import random
import math
import streamlit as st
import matplotlib.pyplot as plt
import os

# We maken ons eigen print statement want we wisselen tussen de streamlit applicatie en de simulatie hier in python
os.environ['USE_STREAMLIT'] = 'False'  # Verander deze waarde indien nodig

# Controleer de omgevingsvariabele om te bepalen of streamlit moet worden gebruikt
USE_STREAMLIT = os.environ.get('USE_STREAMLIT', 'False') == 'True'

def write_output(message):
    if USE_STREAMLIT:
        st.write(message)
    else:
        print(message)

# Token: Een klasse die een enkel token voorstelt.
class Token: 
    def __init__(self, token_id):
        self.token_id = token_id

    def __repr__(self):
        return f"Token({self.token_id})"

# User: Een klasse die een gebruiker voorstelt die tokens kan ontvangen én betalen, met een utility curve.
class User:
    def __init__(self, user_id, balance=None, activity_desire=None):
        self.user_id = user_id
        self.tokens = []
        self.balance = balance if balance is not None else random.normalvariate(10,2)
        self.activity_desire = activity_desire if activity_desire is not None else random.normalvariate(5,1)
        
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

    def buy_utility(self, market_price):
        return (self.balance / market_price) * (1 / self.activity_desire)

    def sell_utility(self, market_price):
        return self.token_count() * market_price * (1 / self.activity_desire)
    
    def __repr__(self):
        return f"User({self.user_id}, Tokens: {self.tokens})"

# Specifieke subklassen voor verschillende typen gebruikers met aangepaste utility-methoden
class FriendsFamilyUser(User):
    def activity_utility(self):
        return super().activity_utility() * 1.5  # We verwachten dat vrienden en family wel vaak mee gaan doen met activiteiten

class TeamAdvisorsUser(User):
    def activity_utility(self):
        return super().activity_utility() * 0.5  # We verwachten dat team advisors niet heel vaak mee gaan doen met activiteiten

class GeneralUser(User):
    def __init__(self, user_id, balance=10, activity_desire=5):
        super().__init__(user_id, balance, activity_desire)  # Hetzelfde als de normale user

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
    def __init__(self, users, initial_price=1.0, elasticity=0.05, buy_threshold = 2.0, sell_threshold = 2.0):
        self.users = users
        self.price = initial_price
        self.demand = 0
        self.supply = 0
        self.elasticity = elasticity
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def update_price(self):
            if self.demand > self.supply:
                self.price *= (1 + self.elasticity)
            elif self.supply > self.demand:
                self.price *= (1 - self.elasticity)
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
                        write_output(f"{buyer.user_id} heeft een token gekocht van {seller.user_id} voor {self.price:.2f} euro.")
                        self.demand += 2
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
                    write_output(f"{seller.user_id} heeft een token verkocht aan {buyer.user_id} voor {self.price:.2f} euro.")
                    self.demand -= 1
                    self.supply += 2
                    return True, "Success"
        return False, "Geen kopers beschikbaar voor de tokens."

    def trade_tokens(self):
            # Let each user attempt to buy or sell based on their utilities
            for buyer in self.users:
                buyer_buy_utility = buyer.buy_utility(self.price)
                if buyer_buy_utility > self.buy_threshold:
                    # Find a seller with high enough sell utility
                    for seller in self.users:
                        seller_sell_utility = seller.sell_utility(self.price)
                        if seller != buyer and seller_sell_utility > self.sell_threshold and seller_sell_utility > buyer_buy_utility:
                            # Attempt to buy from this seller
                            success, message = self.buy_token(buyer)
                            if success:
                                write_output(f"{buyer.user_id} heeft tokens gekocht van {seller.user_id} vanwege hoge buy utility.")
                                break  # Break after successful purchase
                            else:
                                write_output(f"{buyer.user_id} kon geen tokens kopen. Reden: {message}")

    def adjust_market_price(self):
        self.update_price()
        write_output(f"De nieuwe marktprijs voor tokens is {self.price:.2f} euro.")
    
# Activity Pool: X% kans dat bij deelname je een token krijgt, je kan elke iteratie deelnemen als user        
class ActivityPool:
    def __init__(self, users, token_generator, market, probability=0.4, activity_price=None, received_tokens=None, utility_threshold=None):
        self.users = users
        self.token_generator = token_generator
        self.market = market
        self.probability = probability
        self.activity_price = activity_price if activity_price is not None else random.randint(1,3)
        self.received_tokens = received_tokens if received_tokens is not None else random.randint(3,6)
        self.utility_threshold = utility_threshold if utility_threshold is not None else random.normalvariate(5,1)

    def assign_tokens(self, user):
        tokens_paid = user.pay_token(num_tokens=self.activity_price)
        if tokens_paid:
            write_output(f"{user.user_id} heeft {self.activity_price} token(s) betaald.")
            if random.random() < self.probability:
                self.token_generator.assign_token_to_user(user, num_tokens=self.received_tokens)
                write_output(f"{user.user_id} heeft {self.received_tokens} token(s) gekregen.")
            else:
                write_output(f"{user.user_id} heeft geen tokens gekregen.")
        else:
            write_output(f"{user.user_id} heeft niet genoeg tokens om deel te nemen.")
            # Probeer een token te kopen van een andere gebruiker
            success, message = self.market.buy_token(user)
            if success:
                write_output(f"{user.user_id} heeft een token gekocht om deel te nemen.")
                self.assign_tokens(user)
            else:
                write_output(f"{user.user_id} kon geen token kopen om deel te nemen. Reden: {message}")

    def participate(self, user):
        # Controleer of de gebruiker genoeg utility heeft om deel te nemen
        if user.activity_utility() >= self.utility_threshold:
            # Controleer of de gebruiker genoeg tokens heeft om deel te nemen
            if user.token_count() >= self.activity_price:
                # Gebruiker heeft genoeg utility en tokens, dus neemt deel
                self.assign_tokens(user)
            else:
                # Gebruiker heeft niet genoeg tokens, probeer tokens te kopen
                success, message = self.market.buy_token(user)
                if success:
                    write_output(f"{user.user_id} heeft een token gekocht om deel te nemen.")
                    # Herbereken de utility na het kopen van de token (hoewel niet nodig voor deelname)
                    self.assign_tokens(user)
                else:
                    write_output(f"{user.user_id} kon geen token kopen om deel te nemen. Reden: {message}")
        else:
            write_output(f"{user.user_id} heeft besloten niet deel te nemen vanwege lage utility.")
     
# Initial Release class: 
class InitialRelease:
    def __init__(self, users, token_generator):
        self.users = users
        self.token_generator = token_generator
        
    def distribute_tokens(self, num_tokens):
        for _ in range(num_tokens):
            user = random.choice(self.users) # voeg de num_tokens op een random manier toe
            self.token_generator.assign_token_to_user(user)
        write_output(f"Inital release of {num_tokens} tokens completed.")        
        
# Functie om gebruikers aan te maken
def create_users(num_friends_family, num_team_advisors, num_general):
    users = []
    for i in range(num_friends_family):
        users.append(FriendsFamilyUser(f"FF_User{i+1}"))
    for i in range(num_team_advisors):
        users.append(TeamAdvisorsUser(f"TA_User{i+1}"))
    for i in range(num_general):
        users.append(GeneralUser(f"G_User{i+1}"))
    return users

# Monte Carlo simulatie
def monte_carlo_simulation(num_friends_family, num_team_advisors, num_general, iterations, monte_carlo_runs):
    """Monte Carlo simulatie voor tokenomics model."""
    all_market_prices = []
    all_balances = []
    all_utilities = []
    
    for run in range(monte_carlo_runs):
        # Create users
        users = create_users(num_friends_family, num_team_advisors, num_general)
        
        # Create a token generator
        token_generator = TokenGenerator()
        
        # Create a market with default elasticity
        market = Market(users)
        
        # Create an InitialRelease and distribute tokens
        initial_release = InitialRelease(users, token_generator)
        initial_release.distribute_tokens(10)
        
        # Create an ActivityPool with default parameters
        activity_pool = ActivityPool(users, token_generator, market)
        
        market_prices = []
        balances = {user.user_id: [] for user in users}
        utilities = {user.user_id: [] for user in users}
        
        # Run the market simulation
        for _ in range(iterations):
            for user in activity_pool.users:
                if random.random() < activity_pool.probability:
                    activity_pool.participate(user)
            activity_pool.market.adjust_market_price()
            market_prices.append(activity_pool.market.price)
            
            for user in users:
                balances[user.user_id].append(user.balance)
                utilities[user.user_id].append(user.activity_utility())
        
        all_market_prices.append(market_prices)
        all_balances.append(balances)
        all_utilities.append(utilities)
    
    return all_market_prices, all_balances, all_utilities

# Streamlit interface
st.title("Tokenomics Simulatie voor $HEALTH")

num_friends_family = st.slider("Aantal Friends & Family gebruikers", 0, 50, 3)
num_team_advisors = st.slider("Aantal Team Advisors gebruikers", 0, 50, 3)
num_general = st.slider("Aantal General gebruikers", 0, 50, 3)
elasticity = st.slider("Elasticiteit", 0.0, 1.0, 0.1)
probability = st.slider("Waarschijnlijkheid van activiteitspool", 0.0, 1.0, 0.4)
iterations = st.slider("Aantal iteraties", 1, 50, 10)
simulations = st.slider("Aantal simulaties", 1, 100, 50)

if st.button("Start simulatie"):
    with st.spinner("Simulatie wordt uitgevoerd..."):
        # Monte Carlo simulatie
        all_market_prices, all_balances, all_utilities = monte_carlo_simulation(num_friends_family, num_team_advisors, num_general, iterations, simulations)
        
        st.write("Simulatie voltooid.")
        
        # Plot de marktprijzen
        st.subheader("Marktprijs Ontwikkeling over Iteraties")
        fig, ax = plt.subplots()
        for i, market_prices in enumerate(all_market_prices):
            ax.plot(market_prices, label=f'Run {i+1}')
        ax.set_xlabel('Iteratie (Dag)')
        ax.set_ylabel('Marktprijs')
        ax.set_title('Marktprijs Ontwikkeling over Iteraties')
        ax.legend(prop={'size': 6})
        st.pyplot(fig)
        
        # Plot de balans per user
        st.subheader("Balans Ontwikkeling per User over Iteraties")
        fig, ax = plt.subplots()
        for user_id in all_balances[0].keys():
            for i, balances in enumerate(all_balances):
                ax.plot(balances[user_id], label=f'{user_id} Run {i+1}')
        ax.set_xlabel('Iteratie (Dag)')
        ax.set_ylabel('Balans')
        ax.set_title('Balans Ontwikkeling per User over Iteraties')
        ax.legend(prop={'size': 6})
        st.pyplot(fig)
        
        # Plot de utility per user
        st.subheader("Utility Ontwikkeling per User over Iteraties")
        fig, ax = plt.subplots()
        for user_id in all_utilities[0].keys():
            for i, utilities in enumerate(all_utilities):
                ax.plot(utilities[user_id], label=f'{user_id} Run {i+1}')
        ax.set_xlabel('Iteratie (Dag)')
        ax.set_ylabel('Utility')
        ax.set_title('Utility Ontwikkeling per User over Iteraties')
        ax.legend(prop={'size': 6})
        st.pyplot(fig)

# Simulatie functie
def simulate_activity(activity_pool, initial_release, market, iterations):
    # Algemene informatie
    write_output("Algemene Informatie:")
    write_output(f"- Activity Threshold: {activity_pool.utility_threshold:.2f}")
    write_output(f"- Buy Threshold: {market.buy_threshold:.2f}")
    write_output(f"- Sell Threshold: {market.sell_threshold:.2f}")
    write_output("")  # Lege regel voor leesbaarheid
    
    # Basisinformatie van de users
    for user in activity_pool.users:  # Gebruik bestaande activity_pool gebruikers
        write_output(f"Basisinformatie voor {user.user_id}:")
        write_output(f"- Balance: {user.balance:.2f}")
        write_output(f"- Aantal tokens: {user.token_count()}")
        write_output(f"- Activity Desire: {user.activity_desire:.2f}")
        write_output(f"- Activity Utility: {user.activity_utility():.2f}")
        write_output(f"- Buy Utility: {user.buy_utility(market.price):.2f}")  # Geef de marktprijs door
        write_output(f"- Sell Utility: {user.sell_utility(market.price):.2f}")  # Geef de marktprijs door
        write_output("")  # Lege regel voor leesbaarheid
    
    for i in range(iterations):
        write_output(f"--- Iteratie {i+1} ---")
        write_output(f"Huidige marktprijs: {market.price:.2f}\n")

        # Laat gebruikers eerst tokens kopen/verkopen op basis van utilities
        market.trade_tokens()

        for user in activity_pool.users:
            write_output(f"{user.user_id} heeft {user.token_count()} tokens.")
            write_output(f"{user.user_id} heeft {user.balance:.2f} balance.")
            write_output(f"{user.user_id} heeft {user.activity_utility():.2f} utility.")
            write_output(f"{user.user_id} Buy Utility: {user.buy_utility(market.price):.2f}")  # Geef de marktprijs door
            write_output(f"{user.user_id} Sell Utility: {user.sell_utility(market.price):.2f}")  # Geef de marktprijs door
            # Laat gebruiker deelnemen en print de resultaten via write_output
            activity_pool.participate(user)
            write_output("")  # Een lege regel voor leesbaarheid

        # Pas de marktprijs aan en print het resultaat
        market.adjust_market_price()
        write_output(f"Nieuwe marktprijs: {market.price:.2f}")

        # Print vraag en aanbod na elke iteratie
        write_output(f"Vraag naar tokens: {market.demand}")
        write_output(f"Aanbod van tokens: {market.supply}\n")

    write_output("Simulatie voltooid.")

# Voorbeeld van het aanroepen van de simulatiefunctie
def main_simulation():
    # Maak gebruikers aan
    users = create_users(num_friends_family=1, num_team_advisors=1, num_general=2)
    
    # Maak een token generator
    token_generator = TokenGenerator()
    
    # Maak een markt aan met default elasticiteit
    market = Market(users, initial_price=1.0, elasticity=0.05)
    
    # Maak een InitialRelease en verdeel tokens
    initial_release = InitialRelease(users, token_generator)
    initial_release.distribute_tokens(50)  
    
    # Maak een ActivityPool aan met default parameters
    activity_pool = ActivityPool(users, token_generator, market, probability=0.2)
    
    # Voer de simulatie uit voor 10 iteraties
    simulate_activity(activity_pool, initial_release, market, iterations=5)

# Roep de main_simulation functie aan om de simulatie te starten
main_simulation()


   
