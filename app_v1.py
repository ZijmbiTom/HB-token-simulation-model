import random
import math
import streamlit as st
import matplotlib.pyplot as plt
import os

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
        
    def receive_tokens(self, quantity):
        self.tokens.extend([Token(i) for i in range(quantity)])
        
    def pay_token(self, quantity):
        if self.token_count() >= quantity:
            return [self.tokens.pop(0) for _ in range(quantity)]
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

# Order klasse om koop- en verkooporders te definiëren
class Order:
    def __init__(self, user, price, quantity, order_type):
        self.user = user
        self.price = price
        self.quantity = quantity
        self.order_type = order_type  # 'buy' of 'sell'        

# De Market klasse beheert het kopen en verkopen van tokens tussen gebruikers.
class Market:
    def __init__(self, users, initial_price=1.0, elasticity=0.05, utility_factor=0.1):
        self.users = users
        self.price = initial_price
        self.elasticity = elasticity
        self.utility_factor = utility_factor
        self.buy_orders = []
        self.sell_orders = []

    def calculate_order_prices(self, user):
        buy_utility = user.buy_utility(self.price)
        sell_utility = user.sell_utility(self.price)

        # Calculating buy and sell prices with adjusted variation
        buy_price = self.price * (1 - buy_utility * self.utility_factor + random.uniform(-0.05, 0.05))*1.2
        sell_price = self.price * (1 + sell_utility * self.utility_factor + random.uniform(-0.05, 0.05))*0.8

        return buy_price, sell_price

    def place_orders(self):
        self.buy_orders.clear()
        self.sell_orders.clear()
        for user in self.users:
            buy_price, sell_price = self.calculate_order_prices(user)

            if buy_price < self.price and user.balance >= buy_price:
                quantity = int(user.balance / buy_price)  # Maximum number of tokens the user can buy
                if quantity > 0:
                    order = Order(user, buy_price, quantity, 'buy')
                    self.buy_orders.append(order)

            if sell_price > self.price:
                quantity = user.token_count()
                if quantity > 0:
                    order = Order(user, sell_price, quantity, 'sell')
                    self.sell_orders.append(order)

        # Sort orders by price
        self.buy_orders.sort(key=lambda x: x.price, reverse=True)  # Highest buy price first
        self.sell_orders.sort(key=lambda x: x.price)  # Lowest sell price first

    def print_order_book(self):
        write_output("Orderboek:")
        write_output("Kooporders:")
        for order in self.buy_orders:
            write_output(f"Gebruiker: {order.user.user_id}, Aantal: {order.quantity}, Prijs: {order.price:.2f}")

        write_output("Verkooporders:")
        for order in self.sell_orders:
            write_output(f"Gebruiker: {order.user.user_id}, Aantal: {order.quantity}, Prijs: {order.price:.2f}")

    def match_orders(self):
        while self.buy_orders and self.sell_orders:
            best_buy = self.buy_orders[0]
            best_sell = self.sell_orders[0]
    
            # Check if there is a match
            if (
                best_buy.price >= best_sell.price and 
                best_buy.user != best_sell.user
            ):
                trade_quantity = min(best_buy.quantity, best_sell.quantity)
                best_buy.user.receive_tokens(trade_quantity)
                best_sell.user.pay_token(trade_quantity)
                best_buy.user.balance -= trade_quantity * best_sell.price
                best_sell.user.balance += trade_quantity * best_sell.price
    
                # Print details of the trade
                write_output(
                    f"Trade executed: {trade_quantity} tokens from {best_sell.user.user_id} "
                    f"to {best_buy.user.user_id} at price {best_sell.price:.2f}"
                )
    
                best_buy.quantity -= trade_quantity
                best_sell.quantity -= trade_quantity
    
                # Remove fully matched orders
                if best_buy.quantity == 0:
                    self.buy_orders.pop(0)
                if best_sell.quantity == 0:
                    self.sell_orders.pop(0)
            else:
                break

    def adjust_market_price(self):
        if len(self.buy_orders) > len(self.sell_orders):
            self.price *= (1 + self.elasticity)
        elif len(self.sell_orders) > len(self.buy_orders):
            self.price *= (1 - self.elasticity)
        write_output(f"De nieuwe marktprijs voor tokens is {self.price:.2f} euro.")

    def clear_orders(self):
        self.buy_orders.clear()
        self.sell_orders.clear()

# Activity Pool: X% kans dat bij deelname je een token krijgt, je kan elke iteratie deelnemen als user        
class ActivityPool:
    def __init__(self, users, market, probability=0.4, activity_price=None, received_tokens=None, utility_threshold=None):
        self.users = users
        self.market = market
        self.probability = probability
        self.activity_price = activity_price if activity_price is not None else random.randint(1,3)
        self.received_tokens = received_tokens if received_tokens is not None else random.randint(3,6)
        self.utility_threshold = utility_threshold if utility_threshold is not None else random.normalvariate(5,1)

    def assign_tokens(self, user):
        tokens_paid = user.pay_token(self.activity_price)
        if tokens_paid:
            write_output(f"{user.user_id} heeft {self.activity_price} token(s) betaald.")
            if random.random() < self.probability:
                user.receive_tokens(self.received_tokens)
                write_output(f"{user.user_id} heeft {self.received_tokens} token(s) gekregen.")
            else:
                write_output(f"{user.user_id} heeft geen tokens gekregen.")
        else:
            write_output(f"{user.user_id} heeft niet genoeg tokens om deel te nemen.")
            # Probeer een token te kopen van een andere gebruiker
            # Hier gebruiken we de orders in plaats van directe koopfunctie
            self.market.place_orders()
            self.market.match_orders()

    def participate(self, user):
        # Controleer of de gebruiker genoeg utility heeft om deel te nemen
        if user.activity_utility() >= self.utility_threshold:
            # Controleer of de gebruiker genoeg tokens heeft om deel te nemen
            if user.token_count() >= self.activity_price:
                # Gebruiker heeft genoeg utility en tokens, dus neemt deel
                self.assign_tokens(user)
            else:
                # Gebruiker heeft niet genoeg tokens, probeer tokens te kopen
                # Hier gebruiken we de orders in plaats van directe koopfunctie
                self.market.place_orders()
                self.market.match_orders()
        else:
            write_output(f"{user.user_id} heeft besloten niet deel te nemen vanwege lage utility.")
     
# Initial Release class: 
class InitialRelease:
    def __init__(self, users):
        self.users = users
        
    def distribute_tokens(self, num_tokens):
        for _ in range(num_tokens):
            user = random.choice(self.users) # voeg de num_tokens op een random manier toe
            user.receive_tokens(1)
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

# Simulatie functie
def simulate_activity(activity_pool, initial_release, market, iterations):
    # Algemene informatie
    write_output("Algemene Informatie:")
    write_output(f"- Activity Threshold: {activity_pool.utility_threshold:.2f}")
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

        # Plaats orders en match deze
        market.place_orders()
        market.print_order_book()
        market.match_orders()
        market.adjust_market_price()
        market.clear_orders()

        for user in activity_pool.users:
            write_output(f"{user.user_id} heeft {user.token_count()} tokens.")
            write_output(f"{user.user_id} heeft {user.balance:.2f} balance.")
            write_output(f"{user.user_id} heeft {user.activity_utility():.2f} utility.")
            write_output(f"{user.user_id}- Buy Utility: {user.buy_utility(market.price):.2f}")  # Geef de marktprijs door
            write_output(f"{user.user_id}- Sell Utility: {user.sell_utility(market.price):.2f}")  # Geef de marktprijs door
            
            # Laat gebruiker deelnemen en print de resultaten via write_output
            activity_pool.participate(user)
            write_output("")  # Een lege regel voor leesbaarheid

        # Pas de marktprijs aan en print het resultaat
        market.adjust_market_price()
        write_output(f"Nieuwe marktprijs: {market.price:.2f}")

        # Print vraag en aanbod na elke iteratie
        write_output(f"Vraag naar tokens: {len(market.buy_orders)}")
        write_output(f"Aanbod van tokens: {len(market.sell_orders)}\n")

    write_output("Simulatie voltooid.")

# Voorbeeld van het aanroepen van de simulatiefunctie
def main_simulation():
    # Maak gebruikers aan
    users = create_users(num_friends_family=1, num_team_advisors=1, num_general=2)
    
    # Maak een markt aan met default elasticiteit
    market = Market(users, initial_price=1.0, elasticity=0.05)
    
    # Maak een InitialRelease en verdeel tokens
    initial_release = InitialRelease(users)
    initial_release.distribute_tokens(50)  
    
    # Maak een ActivityPool aan met default parameters
    activity_pool = ActivityPool(users, market, probability=0.2)
    
    # Voer de simulatie uit voor 10 iteraties
    simulate_activity(activity_pool, initial_release, market, iterations=5)

# Roep de main_simulation functie aan om de simulatie te starten
main_simulation()

# Monte Carlo simulatie
def monte_carlo_simulation(num_friends_family, num_team_advisors, num_general, iterations, monte_carlo_runs):
    """Monte Carlo simulatie voor tokenomics model."""
    all_market_prices = []
    all_balances = []
    all_utilities = []

    for run in range(monte_carlo_runs):
        # Maak gebruikers aan
        users = create_users(num_friends_family, num_team_advisors, num_general)
        
        # Maak een markt aan met default elasticiteit
        market = Market(users, initial_price=1.0, elasticity=0.05)
        
        # Maak een InitialRelease en verdeel tokens
        initial_release = InitialRelease(users)
        initial_release.distribute_tokens(10)
        
        # Maak een ActivityPool aan met default parameters
        activity_pool = ActivityPool(users, market, probability=0.2)
        
        market_prices = []
        balances = {user.user_id: [] for user in users}
        utilities = {user.user_id: [] for user in users}
        
        # Voer de marktsimulatie uit
        for _ in range(iterations):
            # Plaats orders en match deze
            market.place_orders()
            market.match_orders()
            market.adjust_market_price()
            market.clear_orders()
            
            for user in activity_pool.users:
                if random.random() < activity_pool.probability:
                    activity_pool.participate(user)
            
            # Sla de huidige marktprijs, balans en utility op
            market_prices.append(market.price)
            for user in users:
                balances[user.user_id].append(user.balance)
                utilities[user.user_id].append(user.activity_utility())
        
        all_market_prices.append(market_prices)
        all_balances.append(balances)
        all_utilities.append(utilities)
    
    return all_market_prices, all_balances, all_utilities

# Hoe je de monte_carlo_simulation kunt aanroepen
num_friends_family = 1
num_team_advisors = 1
num_general = 2
iterations = 10
simulations = 5

all_market_prices, all_balances, all_utilities = monte_carlo_simulation(num_friends_family, num_team_advisors, num_general, iterations, simulations)

# Resultaten bekijken
print("Marktprijzen per iteratie:")
for i, prices in enumerate(all_market_prices):
    print(f"Run {i+1}: {prices}")

print("\nBalans per gebruiker per iteratie:")
for user_id in all_balances[0].keys():
    for i, balances in enumerate(all_balances):
        print(f"{user_id} Run {i+1}: {balances[user_id]}")

print("\nUtility per gebruiker per iteratie:")
for user_id in all_utilities[0].keys():
    for i, utilities in enumerate(all_utilities):
        print(f"{user_id} Run {i+1}: {utilities[user_id]}")

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
