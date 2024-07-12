import random
import numpy as np
import uuid
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Definiëren van de Token klasse
class Token:
    def __init__(self):
        self.token_id = uuid.uuid4()  # Unieke ID voor elk token

    def __repr__(self):
        return f"Token({self.token_id})"

# Basis User klasse
class User:
    def __init__(self, name, balance=10, activity_desire=5):
        self.name = name
        self.user_id = uuid.uuid4()  # Unieke ID voor elke gebruiker
        self.tokens = []
        self.balance = balance
        self.activity_desire = activity_desire

    def receive_tokens(self, token):
        self.tokens.append(token)  # Gebruiker ontvangt tokens

    def pay_token(self, num_tokens=1):
        if self.token_count() >= num_tokens:
            tokens_paid = [self.tokens.pop(0) for _ in range(num_tokens)]
            return tokens_paid
        return None  # Als de gebruiker niet genoeg tokens heeft

    def token_count(self):
        return len(self.tokens)  # Aantal tokens in bezit van de gebruiker

    def activity_utility(self):
        return (self.token_count() * 2 + self.balance) * self.activity_desire

    def buy_utility(self, market_price):
        return (self.balance / market_price) * self.activity_desire

    def sell_utility(self, market_price):
        return self.token_count() * market_price * (1 / self.activity_desire)

    def __repr__(self):
        return f"User(Name: {self.name}, ID: {self.user_id}, Tokens: {self.tokens}, Balance: {self.balance}, ActivityDesire: {self.activity_desire})"

# Specifieke subklassen voor verschillende typen gebruikers met aangepaste utility-methoden
class FriendsFamilyUser(User):
    def activity_utility(self):
        return super().activity_utility() * 1.5  # 50% hogere activity utility

    def buy_utility(self, market_price):
        return super().buy_utility(market_price) * 1.5  # 50% hogere buy utility

    def sell_utility(self, market_price):
        return super().sell_utility(market_price) * 0.5  # 50% lagere sell utility

class TeamAdvisorsUser(User):
    def activity_utility(self):
        return super().activity_utility() * 1.5  # 50% hogere activity utility

    def buy_utility(self, market_price):
        return super().buy_utility(market_price) * 1.5  # 50% hogere buy utility

    def sell_utility(self, market_price):
        return super().sell_utility(market_price) * 0.5  # 50% lagere sell utility

class GeneralUser(User):
    def __init__(self, name, balance=10, activity_desire=5):
        super().__init__(name, balance, activity_desire)  # Gebruik de initializer van de basis User klasse

# Definiëren van de TokenGenerator klasse
class TokenGenerator:
    def __init__(self):
        self.current_id = 0

    def generate_token(self):
        token = Token()
        return token

    def assign_token_to_user(self, user, num_tokens=1):
        for _ in range(num_tokens):
            token = self.generate_token()
            user.receive_tokens(token)  # Ken tokens toe aan de gebruiker

# Definiëren van de Market klasse
class Market:
    def __init__(self, users, initial_price=1.0):
        self.users = users
        self.price = initial_price
        self.demand = 0
        self.supply = 0

    def update_price(self):
        if self.demand > self.supply:
            self.price *= 1.1
        elif self.supply > self.demand:
            self.price *= 0.9
        self.demand = 0
        self.supply = 0

    def buy_token(self, buyer):
        if buyer.balance >= self.price:
            token = Token()
            buyer.receive_tokens(token)
            buyer.balance -= self.price
            self.demand += 1
            return True, "Success"
        return False, "Not enough balance to buy a token."

    def sell_token(self, seller):
        if seller.token_count() > 0:
            token = seller.pay_token()[0]
            seller.balance += self.price
            self.supply += 1
            return True, "Success"
        return False, "No tokens available to sell."

    def trade_tokens(self):
        for user in self.users:
            if user.sell_utility(self.price) > user.buy_utility(self.price):
                success, message = self.sell_token(user)
                if success:
                    continue
            elif user.buy_utility(self.price) > user.sell_utility(self.price):
                success, message = self.buy_token(user)
                if success:
                    continue

    def adjust_market_price(self):
        self.update_price()

# Definiëren van de ActivityPool klasse
class ActivityPool:
    def __init__(self, users, token_generator, market, probability=0.2, activity_price=2, received_tokens=3, activity_utility_threshold=10):
        self.users = users
        self.token_generator = token_generator
        self.market = market
        self.probability = probability
        self.activity_price = activity_price
        self.received_tokens = received_tokens
        self.activity_utility_threshold = activity_utility_threshold

    def assign_tokens(self, user):
        tokens_paid = user.pay_token(num_tokens=self.activity_price)
        if tokens_paid:
            if random.random() < self.probability:
                for _ in range(self.received_tokens):
                    token = self.token_generator.generate_token()
                    user.receive_tokens(token)
        else:
            success, message = self.market.buy_token(user)
            if success:
                self.assign_tokens(user)

    def participate(self, user):
        if user.activity_utility() >= self.activity_utility_threshold:
            self.assign_tokens(user)

# Definiëren van de Reserve klasse en subklassen
class Reserve:
    def __init__(self, name, total_tokens):
        self.name = name
        self.total_tokens = total_tokens

    def __repr__(self):
        return f"Reserve(Name: {self.name}, TotalTokens: {self.total_tokens})"

class PublicSaleAirdrop(Reserve):
    pass

class Ecosystem(Reserve):
    pass

class MiningPool(Reserve):
    pass

class Liquidity(Reserve):
    pass

class InitialRelease:
    def __init__(self, users, reserves, token_generator):
        self.users = users
        self.reserves = reserves
        self.token_generator = token_generator

    def distribute_tokens(self, distribution_plan):
        for category, details in distribution_plan.items():
            total_tokens = details['total_tokens']
            tge_percentage = details['tge_percentage']
            linear_vesting_months = details['linear_vesting_months']
            
            tge_tokens = int(total_tokens * tge_percentage)
            vesting_tokens = total_tokens - tge_tokens
            
            if category in self.users:
                # Verdeel TGE tokens direct naar gebruikerscategorieën
                for _ in range(tge_tokens):
                    user = random.choice(self.users[category])
                    self.token_generator.assign_token_to_user(user)

                # Verdeel resterende tokens lineair over de vesting periode (elke maand = 30 iteraties)
                if linear_vesting_months > 0:
                    monthly_tokens = vesting_tokens // linear_vesting_months
                    for user in self.users[category]:
                        user.vesting_schedule = [monthly_tokens] * linear_vesting_months
            else:
                # Wijs tokens toe aan reserves
                self.reserves[category].total_tokens += total_tokens

        print("Initial token distribution completed.")


# Simulatie van de markt
def simulate_market(activity_pool, iterations):
    for _ in range(iterations):
        for user in activity_pool.users:
            activity_pool.participate(user)
        activity_pool.market.trade_tokens()
        activity_pool.market.adjust_market_price()

def monte_carlo_simulation(num_users, iterations, monte_carlo_runs, probability):
    total_tokens = 500000000  # Totaal aantal tokens

    distribution_plan = {
        "FriendsFamily": {"percentage": 0.025, "tge_percentage": 0.3, "linear_vesting_months": 12},
        "PublicSaleAirdrop": {"percentage": 0.136, "tge_percentage": 0.2, "linear_vesting_months": 12},
        "Ecosystem": {"percentage": 0.28, "tge_percentage": 0.15, "linear_vesting_months": 24},
        "MiningPool": {"percentage": 0.27, "tge_percentage": 0.1, "linear_vesting_months": 38},
        "TeamAdvisors": {"percentage": 0.195, "tge_percentage": 0.1, "linear_vesting_months": 24},
        "Liquidity": {"percentage": 0.1, "tge_percentage": 1.0, "linear_vesting_months": 0}
    }

    results = []
    all_market_prices = []

    for _ in range(monte_carlo_runs):
        # Initialiseer gebruikers en reserves
        friends_family_users = [FriendsFamilyUser(f"ff_user{i+1}") for i in range(100)]
        team_advisors_users = [TeamAdvisorsUser(f"ta_user{i+1}") for i in range(50)]
        general_users = [GeneralUser(f"gen_user{i+1}") for i in range(num_users)]

        all_users = {
            "FriendsFamily": friends_family_users,
            "TeamAdvisors": team_advisors_users,
            "General": general_users
        }

        reserves = {
            "PublicSaleAirdrop": PublicSaleAirdrop("PublicSaleAirdrop", 0),
            "Ecosystem": Ecosystem("Ecosystem", 0),
            "MiningPool": MiningPool("MiningPool", 0),
            "Liquidity": Liquidity("Liquidity", 0)
        }

        token_generator = TokenGenerator()
        initial_release = InitialRelease(all_users, reserves, token_generator)

        # Bereken het distributieplan op basis van het percentage
        distribution_plan_calculated = {
            category: {
                "total_tokens": int(total_tokens * details["percentage"]),
                "tge_percentage": details["tge_percentage"],
                "linear_vesting_months": details["linear_vesting_months"]
            }
            for category, details in distribution_plan.items()
        }

        # Distribute tokens volgens het distributieplan
        initial_release.distribute_tokens(distribution_plan_calculated)

        market = Market(general_users + friends_family_users + team_advisors_users)
        activity_pool = ActivityPool(general_users + friends_family_users + team_advisors_users, token_generator, market, probability=probability)

        market_prices = []

        for iteration in range(iterations):
            # Vrijgave van maandelijkse tokens aan gebruikers
            if iteration % 30 == 0:  # Elke 30 iteraties is een nieuwe maand
                for category in ["FriendsFamily", "TeamAdvisors"]:
                    for user in all_users[category]:
                        if hasattr(user, 'vesting_schedule') and user.vesting_schedule:
                            monthly_tokens = user.vesting_schedule.pop(0)
                            for _ in range(monthly_tokens):
                                token = token_generator.generate_token()
                                user.receive_tokens(token)

            for user in activity_pool.users:
                activity_pool.participate(user)
            activity_pool.market.trade_tokens()
            activity_pool.market.adjust_market_price()
            market_prices.append(market.price)

        all_market_prices.append(market_prices)
        for user in general_users + friends_family_users + team_advisors_users:
            results.append({
                "user_name": user.name,
                "user_id": user.user_id,
                "tokens": user.token_count(),
                "balance": user.balance,
                "final_utility": user.activity_utility()
            })

    return results, all_market_prices

# Aangepaste functies en klassen (zoals hierboven geïmplementeerd)

# Functie om initial release per groep te berekenen
def get_initial_release(distribution_plan, total_tokens):
    initial_release = {
        category: {
            "initial_tokens": int(total_tokens * details["percentage"]),
            "tge_tokens": int(total_tokens * details["percentage"] * details["tge_percentage"]),
            "vesting_tokens": int(total_tokens * details["percentage"] * (1 - details["tge_percentage"]))
        }
        for category, details in distribution_plan.items()
    }
    return initial_release

# Streamlit app configuratie
st.title("Monte Carlo Simulatie voor $HEALTH Tokens")

# Invoerparameters
total_tokens = st.number_input("Totaal aantal Tokens", value=500000000)
num_users = st.slider("Aantal Gebruikers", 5, 1000, 500)
iterations = st.slider("Iteraties per Run (Dagen)", 10, 300, 150)
monte_carlo_runs = st.slider("Monte Carlo Runs", 10, 100, 50)
probability = st.slider("Activiteiten Deelname Waarschijnlijkheid", 0.0, 1.0, 0.9)

if st.button("Voer Simulatie Uit"):
    with st.spinner("Simulatie wordt uitgevoerd..."):
        results, all_market_prices = monte_carlo_simulation(num_users, iterations, monte_carlo_runs, probability)

    st.success("Simulatie voltooid!")

    # Bereken initial release
    distribution_plan = {
        "FriendsFamily": {"percentage": 0.025, "tge_percentage": 0.3, "linear_vesting_months": 12},
        "PublicSaleAirdrop": {"percentage": 0.136, "tge_percentage": 0.2, "linear_vesting_months": 12},
        "Ecosystem": {"percentage": 0.28, "tge_percentage": 0.15, "linear_vesting_months": 24},
        "MiningPool": {"percentage": 0.27, "tge_percentage": 0.1, "linear_vesting_months": 38},
        "TeamAdvisors": {"percentage": 0.195, "tge_percentage": 0.1, "linear_vesting_months": 24},
        "Liquidity": {"percentage": 0.1, "tge_percentage": 1.0, "linear_vesting_months": 0}
    }
    initial_release_stats = get_initial_release(distribution_plan, total_tokens)

    # Toon initiële tokenverdeling per groep
    st.subheader("Initiële Tokenverdeling per Groep")
    initial_release_df = pd.DataFrame(initial_release_stats).T
    st.dataframe(initial_release_df)

    # Bereken gemiddelde marktprijs voor elke iteratie
    avg_market_prices = np.mean(all_market_prices, axis=0)
    overall_avg_market_price = np.mean(avg_market_prices)
    st.write(f"Gemiddelde Marktprijs na Monte Carlo Simulatie: {overall_avg_market_price:.2f}")

    # Plot de marktprijzen
    st.subheader("Marktprijs Ontwikkeling over Iteraties")
    fig, ax = plt.subplots()
    for i, market_prices in enumerate(all_market_prices):
        ax.plot(market_prices, label=f'Run {i+1}')
    ax.set_xlabel('Iteratie (Dag)')
    ax.set_ylabel('Marktprijs')
    ax.set_title('Marktprijs Ontwikkeling over Iteraties')
    ax.legend()
    st.pyplot(fig)

    # Toon voorbeeldresultaten
    st.subheader("Voorbeeld Resultaten")
    sample_results = results[:10]
    for result in sample_results:
        st.write(f"{result['user_name']} heeft {result['tokens']} tokens en een balans van {result['balance']} euros. (ID: {result['user_id']})")

    # Verdere inzichten
    st.subheader("Verdere Inzichten")
    total_tokens_in_market = sum(user['tokens'] for user in results)
    avg_balance_per_user = np.mean([user['balance'] for user in results])
    st.write(f"Totaal aantal tokens in de markt: {total_tokens_in_market}")
    st.write(f"Gemiddelde balans per gebruiker: {avg_balance_per_user:.2f} euros")
