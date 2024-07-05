import random
import numpy as np
import uuid
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# check

class Token:
    def __init__(self):
        self.token_id = uuid.uuid4()

    def __repr__(self):
        return f"Token({self.token_id})"

class User:
    def __init__(self, name, balance=10, activity_desire=5):
        self.name = name
        self.user_id = uuid.uuid4()
        self.tokens = []
        self.balance = balance
        self.activity_desire = activity_desire

    def receive_tokens(self, token):
        self.tokens.append(token)

    def pay_token(self, num_tokens=1):
        if self.token_count() >= num_tokens:
            tokens_paid = [self.tokens.pop(0) for _ in range(num_tokens)]
            return tokens_paid
        return None

    def token_count(self):
        return len(self.tokens)

    def activity_utility(self):
        return (self.token_count() * 2 + self.balance) * self.activity_desire

    def buy_utility(self, market_price):
        return (self.balance / market_price) * self.activity_desire

    def sell_utility(self, market_price):
        return self.token_count() * market_price * (1 / self.activity_desire)

    def __repr__(self):
        return f"User(Name: {self.name}, ID: {self.user_id}, Tokens: {self.tokens}, Balance: {self.balance}, ActivityDesire: {self.activity_desire})"

class TokenGenerator:
    def __init__(self):
        self.current_id = 0

    def generate_token(self):
        token = Token()
        return token

    def assign_token_to_user(self, user, num_tokens=1):
        for _ in range(num_tokens):
            token = self.generate_token()
            user.receive_tokens(token)

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

class InitialRelease:
    def __init__(self, users, token_generator):
        self.users = users
        self.token_generator = token_generator

    def distribute_tokens(self, num_tokens):
        for _ in range(num_tokens):
            user = random.choice(self.users)
            self.token_generator.assign_token_to_user(user)
        print(f"Initial release of {num_tokens} tokens completed.")

def simulate_market(activity_pool, iterations):
    for _ in range(iterations):
        for user in activity_pool.users:
            activity_pool.participate(user)
        activity_pool.market.trade_tokens()

def monte_carlo_simulation(num_users, iterations, monte_carlo_runs, probability):
    results = []
    all_market_prices = []

    for _ in range(monte_carlo_runs):
        users = [User(f"user{i+1}") for i in range(num_users)]
        token_generator = TokenGenerator()
        market = Market(users)
        initial_release = InitialRelease(users, token_generator)
        initial_release.distribute_tokens(10)
        activity_pool = ActivityPool(users, token_generator, market, probability=probability)

        market_prices = []

        for _ in range(iterations):
            for user in activity_pool.users:
                activity_pool.participate(user)
            activity_pool.market.trade_tokens()
            market_prices.append(market.price)

        all_market_prices.append(market_prices)
        for user in users:
            results.append({
                "user_name": user.name,
                "user_id": user.user_id,
                "tokens": user.token_count(),
                "balance": user.balance,
                "final_utility": user.activity_utility()
            })

    return results, all_market_prices

# Streamlit app
st.title("Monte Carlo Simulation for $HEALTH")

num_users = st.slider("Number of Users", 5, 1000, 500)
iterations = st.slider("Iterations per Run", 10, 100, 50)
monte_carlo_runs = st.slider("Monte Carlo Runs", 10, 100, 50)
probability = st.slider("Activity Pool Probability", 0.0, 1.0, 0.2)

if st.button("Run Simulation"):
    with st.spinner("Running simulation..."):
        results, all_market_prices = monte_carlo_simulation(num_users, iterations, monte_carlo_runs, probability)

    st.success("Simulation completed!")

    # Calculate average market price
    avg_market_prices = [np.mean(prices) for prices in all_market_prices]
    overall_avg_market_price = np.mean(avg_market_prices)
    st.write(f"Average market price after Monte Carlo simulation: {overall_avg_market_price:.2f}")

    # Plot the market prices
    fig, ax = plt.subplots()
    for market_prices in all_market_prices:
        ax.plot(market_prices, label='Market Price')
    
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Market Price')
    ax.set_title('Market Price over Iterations')
    ax.set_ylim(bottom=1)  # Ensure y-axis starts at 1 or higher
    st.pyplot(fig)

    # Display sample results
    sample_results = results[:10]
    for result in sample_results:
        st.write(f"{result['user_name']} has {result['tokens']} tokens and a balance of {result['balance']} euros. (ID: {result['user_id']})")