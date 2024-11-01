'''
HB Token simulation model

Assumptions:
    - Zie configuratie klasse
    
'''

import uuid
import math
import random
import matplotlib.pyplot as plt
import streamlit as st

# Streamlit configuratie
st.title("HB Token Simulation Model")
st.write("Dit model simuleert de distributie en transacties van een token.")

# Gebruik sliders en invoervelden voor gebruikersinput
initial_token_price = st.sidebar.number_input("Initial Token Price", value=0.0001, format="%.6f")
total_supply = st.sidebar.number_input("Total Supply", value=50000000000)
initial_cash_user = st.sidebar.number_input("Initial Cash per User", value=1000)
initial_cash_speculator = st.sidebar.number_input("Initial Cash per Speculator", value=3000)
initial_cash_datapartner = st.sidebar.number_input("Initial Cash for Data Partner", value=100000)
initial_cash_brands = st.sidebar.number_input("Initial Cash for Brands", value=100000)
setup_fee = st.sidebar.number_input("Setup Fee in euro's", value=20)
pool_fee = st.sidebar.number_input("Pool Fee in euro's", value=20)
aantal_gebruikers = st.sidebar.number_input("Aantal gebruikers", value=10000)
groeiratio_gebruiker = st.sidebar.number_input("Groeipercentage gebruikers per maand", value=1)
aantal_speculators = st.sidebar.number_input("Aantal speculators", value=2000)
groeiratio_speculators = st.sidebar.number_input("Groeipercentage speculators per maand", value=1)
ratio_op_de_markt_investeerders = st.sidebar.number_input("Percentage op de markt voor investeerders per maand", value=0)
ratio_op_de_markt_systemen = st.sidebar.number_input("Percentage op de markt voor systemen per maand", value=0.5)
kans_activiteit = st.sidebar.number_input("Kans dat een activiteit succesvol wordt afgerond", value=0.9)
iterations = st.sidebar.number_input("Iterations", value=365)
tge_psa = st.sidebar.number_input("Percentage Public sale op de markt", value=80)
elasticiteit = st.sidebar.number_input("Gevoeligheid van de prijs verandering (tussen 0 en 1)", value=0.5)

# Configuratie klasse
class Configuratie:
    def __init__(self):
        self.initial_token_price = initial_token_price
        self.total_supply = total_supply
        self.initial_cash_user = initial_cash_user
        self.initial_cash_speculator = initial_cash_speculator
        self.initial_cash_datapartner = initial_cash_datapartner
        self.initial_cash_brands = initial_cash_brands
        self.setup_fee = setup_fee
        self.pool_fee = pool_fee
        self.aantal_gebruiker = aantal_gebruikers
        self.aantal_speculators = aantal_speculators
        self.iterations = iterations
        self.groeiratio_gebruiker = groeiratio_gebruiker / 100  # Omdat de input is in percentages
        self.groeiratio_speculators = groeiratio_speculators / 100  # Omdat de input is in percentages
        self.ratio_op_de_markt_investeerders = ratio_op_de_markt_investeerders / 100
        self.ratio_op_de_markt_systemen = ratio_op_de_markt_systemen / 100
        self.kans_activiteit = kans_activiteit
        self.tge_psa = tge_psa
        self.elasticiteit = elasticiteit

class Token:
    '''
    De token klasse die alle eigenschappen van de tokens bijhoudt
    '''
    # Attributen
    def __init__(self, token_supply, initial_token_price, elasticiteit):
        self.__totale_supply = token_supply
        self.__circulerende_supply = 0
        self.__prijs = initial_token_price
        self.__elasticiteit = elasticiteit
        
    # Methodes    
    def maandelijkse_supply_vrijgeven(self, hoeveelheid):
        self.__circulerende_supply += hoeveelheid

    def burn_tokens(self, hoeveelheid):
        self.__circulerende_supply -= hoeveelheid
        
    def bereken_prijs(self, vraag, aanbod):
        if aanbod > 0:
            if vraag >= aanbod:
                nieuwe_prijs_factor = 1 + (self.__elasticiteit*(vraag/aanbod)) 
                self.__prijs *= nieuwe_prijs_factor
            elif aanbod > vraag:
                nieuwe_prijs_factor = 1 - (self.__elasticiteit*(vraag/aanbod)) 
                self.__prijs *= nieuwe_prijs_factor               
        else:
            # Als er geen aanbod is, blijft de prijs hetzelfde om deling door nul te voorkomen
            pass
            
    def update_prijs(self, vraag, aanbod):
        self.bereken_prijs(vraag, aanbod)
        
    def get_prijs(self):
        return self.__prijs
    
    def get_totale_supply(self):
        return self.__totale_supply
    
    def get_circulerende_tokens(self):
        return self.__circulerende_supply
    
class User:
    def __init__(self, id, cash):
        self.id = uuid.uuid4()
        self.cash = cash
        self.tokens = 0 # Elke user begint met 0 tokens
        self.max_koop_bedrag = 5000
        
    def koop_tokens(self, exchange, aantal_tokens, liquidity=None):
        # Liquidity wordt standaard toegewezen als deze niet is opgegeven
        if liquidity is None:
            liquidity = exchange.liquidity  # Verwijst naar een liquidity-klasse die je aan de exchange koppelt
        
        totale_kosten = aantal_tokens * exchange.token.get_prijs()
        
        if totale_kosten > self.max_koop_bedrag:
            aantal_tokens = self.max_koop_bedrag / exchange.token.get_prijs()
        
        # De User koopt tokens via de Exchange
        exchange.koop_tokens(self, aantal_tokens, liquidity)
        
    def verkoop_tokens(self, exchange, aantal_tokens):
        # De User verkoopt tokens via de Exchange
        exchange.verkoop_tokens(self, aantal_tokens)  
        
    # elke user heeft zijn eigen utility functies als optie

class Gebruiker(User):
    def __init__(self, id, cash, data_utility, random_factor = None):
        super().__init__(id, cash)
        self.data_utility = data_utility
        self.random_factor = random_factor if random_factor is not None else random.uniform(1, 5)
        self.days_until_available = 0
        
    def activiteit_utility(self, token):    
        value = 1 + 3 * self.tokens + 1 * self.cash + (self.tokens * token.get_prijs())  # Prijs heeft een lichte invloed
            
        # Controleer op negatieve waarde (log mag niet negatief zijn)
        if value <= 0:
           value = 1
         
        return self.random_factor * math.log(value) # we gaan er vanuit dat tokens een grotere invloed hebben op het meedoen van activiteiten

class Speculator(User):
    def __init__(self, id, cash, koop_threshold=None, verkoop_threshold=None, random_factor=None):
        super().__init__(id, cash)
        self.koop_threshold = koop_threshold if koop_threshold is not None else random.normalvariate(5, 1)
        self.verkoop_threshold = verkoop_threshold if verkoop_threshold is not None else random.normalvariate(5, 1)
        self.random_factor = random_factor if random_factor is not None else random.uniform(1, 5)

    def koop_utility(self, token, tokens=None, cash=None, prijs=None):
        if tokens is None:
            tokens = self.tokens
        if cash is None:
            cash = self.cash
        if prijs is None:
            prijs = tokens * token.get_prijs()
        
        value = 1 + 1 * tokens + 2 * cash + prijs 
            
        # Controleer op negatieve waarde (log mag niet negatief zijn)
        if value <= 0:
            value = 1

        return self.random_factor * math.log(value)  
    
    def verkoop_utility(self, token, tokens=None, cash=None, prijs=None):
        if tokens is None:
            tokens = self.tokens
        if cash is None:
            cash = self.cash
        if prijs is None:
            prijs = tokens * token.get_prijs()
            
        value = 1 + 2 * tokens + 1 * cash + prijs 
            
        # Controleer op negatieve waarde (log mag niet negatief zijn)
        if value <= 0:
            value = 1
        
        return self.random_factor * math.log(value)  
    
    def bepaal_aantal_tokens_om_te_handelen(self, token):
        koop_utility = self.koop_utility(token)
        verkoop_utility = self.verkoop_utility(token)

        # Bepaal een willekeurige factor tussen 0 en 0.05
        random_factor = random.uniform(0, 0.05)

        max_cash = 5000  # Maximale hoeveelheid cash om te handelen
        token_prijs = token.get_prijs()
        
        if token_prijs == 0 or random_factor == 0:
            return 0  # Vermijd deling door nul

        if koop_utility > verkoop_utility:
            # Bepaal het aantal tokens om te kopen met maximaal 5% van de cash
            max_cash = self.cash * random_factor
            max_tokens = int(max_cash / token_prijs)
            return min(max_tokens, int(self.cash / token_prijs))
        elif koop_utility < verkoop_utility:
            # Bepaal het aantal tokens om te verkopen met maximaal 5% van de tokens
            max_tokens = int(self.tokens * random_factor)
            return min(max_tokens, int(self.tokens))
        else:
            return 0

class InvestorGroup:
    def __init__(self, totale_supply, allocatie_percentage, tge_percentage, vesting_maanden, verkoop_threshold = None):
        self.totale_allocatie = totale_supply * (allocatie_percentage / 100)
        self.vrijgegeven_tokens = 0
        self.beschikbare_vrijgegeven_tokens = 0        
        self.cash = 0
        self.tokens_op_markt = 0
        self.resterende_tokens = self.totale_allocatie
        self.tge_percentage = tge_percentage
        self.vesting_maanden = vesting_maanden
        self.tokens_per_maand = 0 if vesting_maanden == 0 else (self.totale_allocatie * (1 - tge_percentage / 100)) / vesting_maanden
        self.verkoop_threshold = verkoop_threshold if verkoop_threshold is not None else random.normalvariate(5,1)
        self.vrijgave_per_iteratie = []

    def vrijgave_tokens(self, iteratie):
        if iteratie == 0:
            # TGE Vrijgave
            tge_tokens = self.totale_allocatie * (self.tge_percentage / 100)
            self.vrijgegeven_tokens += tge_tokens
            self.beschikbare_vrijgegeven_tokens += tge_tokens            
            self.resterende_tokens -= tge_tokens
            self.vrijgave_per_iteratie.append(self.vrijgegeven_tokens)
            print(f"Iteratie {iteratie}: {tge_tokens} tokens vrijgegeven (TGE)")
            
        elif iteratie % 30 == 0 and iteratie // 30 <= self.vesting_maanden:
            # Lineaire vesting per maand (elke 30 iteraties)
            self.vrijgegeven_tokens += self.tokens_per_maand
            self.beschikbare_vrijgegeven_tokens += self.tokens_per_maand
            self.resterende_tokens -= self.tokens_per_maand
            self.vrijgave_per_iteratie.append(self.vrijgegeven_tokens)
            print(f"Iteratie {iteratie}: {self.tokens_per_maand} tokens vrijgegeven.")
            
        else:
            self.vrijgave_per_iteratie.append(self.vrijgegeven_tokens)
            
    def verkoop_utility(self, prijs_per_token):
        
        value = 1 + 2 * self.vrijgegeven_tokens + 1 * prijs_per_token # Prijs heeft een lichte invloed
            
        # Controleer op negatieve waarde (log mag niet negatief zijn)
        if value <= 0:
            raise ValueError(f"Waarde voor logaritme is niet positief: {value}")
        
        return math.log(value)  

class FriendsAndFamily(InvestorGroup):
    '''
    We zouden hier nog specifieke aanpassingen kunnen aanmaken in de type investor zoals verschillende utilities
    '''
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 2.5, 30, 12)

class TeamAndAdvisors(InvestorGroup):
    '''
    We zouden hier nog specifieke aanpassingen kunnen aanmaken in de type investor zoals verschillende utilities
    '''
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 19.5, 10, 24)

# Hier komt het ecosystem & mining pool (genaamd systemen) klasse, ook wordt de public sale, en liquidity toegevoegd
class System():
    def __init__(self, totale_supply, allocatie_percentage, tge_percentage, vesting_maanden):
        self.totale_allocatie = totale_supply * (allocatie_percentage / 100)
        self.vrijgegeven_tokens = 0
        self.beschikbare_vrijgegeven_tokens = 0        
        self.tokens_op_markt = 0        
        self.resterende_tokens = self.totale_allocatie
        self.tge_percentage = tge_percentage
        self.vesting_maanden = vesting_maanden
        self.tokens_per_maand = 0 if vesting_maanden == 0 else (self.totale_allocatie * (1 - tge_percentage / 100)) / vesting_maanden
        self.vrijgave_per_iteratie = []

    def vrijgave_tokens(self, iteratie):
        if iteratie == 0:
            # TGE Vrijgave
            tge_tokens = self.totale_allocatie * (self.tge_percentage / 100)
            self.vrijgegeven_tokens += tge_tokens
            self.beschikbare_vrijgegeven_tokens += tge_tokens            
            self.resterende_tokens -= tge_tokens
            self.vrijgave_per_iteratie.append(self.vrijgegeven_tokens)
            print(f"Iteratie {iteratie}: {tge_tokens} tokens vrijgegeven (TGE)")
            
        elif iteratie % 30 == 0 and iteratie // 30 <= self.vesting_maanden:
            # Lineaire vesting per maand (elke 30 iteraties)
            self.vrijgegeven_tokens += self.tokens_per_maand
            self.beschikbare_vrijgegeven_tokens += self.tokens_per_maand            
            self.resterende_tokens -= self.tokens_per_maand
            self.vrijgave_per_iteratie.append(self.vrijgegeven_tokens)
            print(f"Iteratie {iteratie}: {self.tokens_per_maand} tokens vrijgegeven.")
            
        else:
            self.vrijgave_per_iteratie.append(self.vrijgegeven_tokens)

class Ecosystem(System):
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 28, 15, 24)
        
    def ontvang_burn_tokens(self, hoeveelheid):
        self.vrijgegeven_tokens += hoeveelheid
        print(f"Ecosystem ontvangt {hoeveelheid} extra tokens door falen burning activiteit")

class Mining(System):
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 27, 10, 36)
        
    def ontvang_mining_tokens(self, hoeveelheid):
        self.vrijgegeven_tokens += hoeveelheid
        print(f"Mining ontvangt {hoeveelheid} extra tokens door falen mining activiteit")
        
class PublicSaleAirdrop(System):
    def __init__(self, totale_supply, tge_percentage=20):
        super().__init__(totale_supply, allocatie_percentage=13, tge_percentage=tge_percentage, vesting_maanden=12)  

class Liquidity(System):
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 10, 100, 0)   

class Brand:
    def __init__(self, cash):
        self.cash = cash
        self.tokens = 0
        
    def koop_tokens(self, exchange, aantal_tokens, liquidity=None):
        # Liquidity wordt standaard toegewezen als deze niet is opgegeven
        if liquidity is None:
            liquidity = exchange.liquidity  # Verwijst naar een liquidity-klasse die je aan de exchange koppelt
            
        # De DataPartner koopt tokens via de Exchange
        exchange.koop_tokens(self, aantal_tokens, liquidity)

    def betaal_pool_fee(self, token, hb, pool_fee):
        pool_fee_tokens = pool_fee / token.get_prijs()
        
        if self.tokens >= pool_fee_tokens:
            self.tokens -= pool_fee_tokens
            hb.ontvang_setup_fee(token, pool_fee_tokens)
            print(f"Brand heeft de pool fee van {pool_fee_tokens} tokens betaald aan HB.")
        else:
            print("Brand heeft niet genoeg tokens om de pool fee te betalen.")
            return False
        return True

class DataPartner:
    def __init__(self, cash):
        self.cash = cash
        self.tokens = 0

    def koop_tokens(self, exchange, aantal_tokens, liquidity=None):
        # Liquidity wordt standaard toegewezen als deze niet is opgegeven
        if liquidity is None:
            liquidity = exchange.liquidity  # Verwijst naar een liquidity-klasse die je aan de exchange koppelt
            
        # De DataPartner koopt tokens via de Exchange
        exchange.koop_tokens(self, aantal_tokens, liquidity)

    def betaal_setup_fee(self, token, hb, setup_fee):
        setup_fee_tokens = setup_fee / token.get_prijs()
        
        if self.tokens >= setup_fee_tokens:
            self.tokens -= setup_fee_tokens
            hb.ontvang_setup_fee(token, setup_fee_tokens)
            print(f"Data Partner heeft de setup_fee van {setup_fee_tokens} tokens betaald aan HB.")
        else:
            print("Data Partner heeft niet genoeg tokens om de setup_fee te betalen.")
            return False
        return True
    
class HB: # Beheerder van de token
    '''
    Hoeveel cash heeft HB in het begin? Hoe gaan ze om met het kopen en verkopen van tokens?
    '''
    def __init__(self):
        self.totale_fees = 0
        self.totale_burned_tokens = 0
        self.tokens = 0
        self.cash = 0
        
    def burn_tokens(self, token, hoeveelheid):
        token.burn_tokens(hoeveelheid)
        self.totale_burned_tokens += hoeveelheid
    
    def ontvang_setup_fee(self, token, hoeveelheid, percentage_burn = 0.1):
        self.tokens += hoeveelheid * (1 - percentage_burn)
        self.burn_tokens(token, hoeveelheid * percentage_burn)
    
    def koop_tokens(self, bedrag, token):
        if bedrag <= self.cash:
            aantal_tokens = bedrag / token.get_prijs()
            self.tokens += aantal_tokens
            self.cash -= bedrag
        
    def verkoop_tokens(self, aantal_tokens, token):
        if aantal_tokens <= self.tokens:
            self.tokens -= aantal_tokens
            bedrag = aantal_tokens * token.get_prijs()
            self.cash += bedrag

class Activiteiten:
    def __init__(self, probability, activity_threshold):
        self.probability = probability
        self.activity_threshold = activity_threshold

    def bereken_threshold(self, exchange):
        # Basis berekening van de drempelwaarde
        return self.activity_threshold + math.log(1 + exchange.tokens_op_markt / 100000)
    
    def check_en_update_beschikbaarheid(self, gebruiker):
        # Controleren of de gebruiker beschikbaar is
        if gebruiker.days_until_available > 0:
            print(f"{gebruiker.id} is nog {gebruiker.days_until_available} dagen niet beschikbaar")
            return False
    
        # Stel nieuwe dagen op basis van gewichten
        dagen_opties = [7, 14, 21, 28]
        gewichten = [1, 1, 3, 1]
        gebruiker.days_until_available = random.choices(dagen_opties, gewichten)[0]
    
        return True

class StandaardActiviteit(Activiteiten):
    def __init__(self, probability, activity_threshold):
        super().__init__(probability, activity_threshold)

    def deelname_activiteit(self, token, exchange, gebruiker, hb):
        # Controleren of de gebruiker beschikbaar is voor een activiteit        
        if not self.check_en_update_beschikbaarheid(gebruiker):
            return
        
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = self.bereken_threshold(exchange)

        # Controleer of de utility van de gebruiker hoger is dan de threshold
        if gebruiker.activiteit_utility(token) > threshold:
            print("Gebruiker doet mee met de standaard activiteit")
            # Controleer of de gebruiker wint op basis van probability

            # Bereken een willekeurige inleg tussen de 5 en 10 euro
            inleg_cash = random.uniform(5, 10)
            inleg_tokens = inleg_cash / token.get_prijs() # Bereken het aantal tokens dat ingelegd moet worden op basis van cash
            
            # Bereken 1% van de inleg als fee voor HB
            fee_voor_hb = inleg_tokens * 0.01
            hb.tokens += fee_voor_hb            
            
            # Check nog of gebruiker genoeg tokens heeft, anders kopen
            if gebruiker.tokens < inleg_tokens:
                print("Gebruiker heeft niet genoeg geld om aan de activiteit te deelnemen, dus koopt extra tokens")
                missende_tokens = (inleg_tokens - gebruiker.tokens)
                gebruiker.koop_tokens(exchange, missende_tokens)
    
            # Met een bepaalde kans krijgen de deelnemers tokens na hun inleg
            if random.random() < self.probability:
                beloning_tokens = 1.5 * inleg_tokens
                gebruiker.tokens += (beloning_tokens - inleg_tokens)
                print(f"Gebruiker wint {beloning_tokens}")
            else: 
                gebruiker.tokens -= inleg_tokens
                hb.tokens += inleg_tokens * 0.9 # 90% procent van de inleg gaat naar HB als de deelnemer faalt
                hb.burn_tokens(token, inleg_tokens*0.1) # 10% van de inleg wordt geburned
                print(f"Gebruiker verliest {inleg_tokens}")
            
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")
     
class BurningActiviteit(Activiteiten):
    def __init__(self, probability, activity_threshold):
        super().__init__(probability, activity_threshold)
        
    def deelname_activiteit(self, token, exchange, gebruiker, ecosystem):
        
        # Controleren of de gebruiker beschikbaar is voor een activiteit        
        if not self.check_en_update_beschikbaarheid(gebruiker):
            return
        
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = self.bereken_threshold(exchange)

        # Bereken een willekeurige inleg tussen de 5 en 10 euro
        inleg_cash = random.uniform(5, 10)
        inleg_tokens = inleg_cash / token.get_prijs() # Bereken het aantal tokens dat ingelegd moet worden op basis van cash
        
        # Controleer of de utility van de gebruiker hoger is dan de threshold
        if gebruiker.activiteit_utility(token) > threshold:
            print("Gebruiker doet mee met de burning activiteit")
            
            # check nog of gebruiker genoeg tokens heeft, anders kopen
            if gebruiker.tokens < inleg_tokens:
                print("Gebruiker heeft niet genoeg geld om aan de activiteit te deelnemen, dus koopt extra tokens")
                missende_tokens = (inleg_tokens - gebruiker.tokens)
                gebruiker.koop_tokens(exchange, missende_tokens)
                
            if random.random() < self.probability:
                gebruiker.tokens -= inleg_tokens
                token.burn_tokens(inleg_tokens)
                print(f"Gebruiker wint, en {inleg_tokens} tokens worden geburnt")
            else: 
                gebruiker.tokens -= inleg_tokens
                ecosystem.ontvang_burn_tokens(inleg_tokens)
                print(f"Gebruiker verliest, en {inleg_tokens} tokens worden naar het ecosystem gestuurd")
        
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")   

class MiningActiviteit(Activiteiten):
    def __init__(self, probability, activity_threshold):
        super().__init__(probability, activity_threshold)
        
    def deelname_activiteit(self, token, exchange, gebruiker, mining):

        # Controleren of de gebruiker beschikbaar is voor een activiteit        
        if not self.check_en_update_beschikbaarheid(gebruiker):
            return    

        # Gebruik de dynamisch berekende drempelwaarde
        threshold = self.bereken_threshold(exchange)
 
        # Bereken een willekeurige inleg tussen de 5 en 10 euro
        inleg_cash = random.uniform(5, 10)
        inleg_tokens = inleg_cash / token.get_prijs() # Bereken het aantal tokens dat ingelegd moet worden op basis van cash
        
        # Controleer of de utility van de gebruiker hoger is dan de threshold
        if gebruiker.activiteit_utility(token) > threshold:
            print("Gebruiker doet mee met de mining activiteit")
            # Controleer of de gebruiker wint op basis van probability
            
            # check nog of gebruiker genoeg tokens heeft, anders kopen
            if gebruiker.tokens < inleg_tokens:
                print("Gebruiker heeft niet genoeg geld om aan de activiteit te deelnemen, dus koopt extra tokens")
                missende_tokens = (inleg_tokens - gebruiker.tokens)
                gebruiker.koop_tokens(exchange, missende_tokens)
                
            if random.random() < self.probability:
                gebruiker.tokens -= inleg_tokens
                token.burn_tokens(inleg_tokens)
                print(f"Gebruiker wint, en {inleg_tokens} tokens worden geburnt")
            else: 
                gebruiker.tokens -= inleg_tokens
                mining.ontvang_mining_tokens(inleg_tokens)
                print(f"Gebruiker verliest, en {inleg_tokens} tokens worden naar de mining gestuurd")
        
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")   

class HostActiviteit(Activiteiten):
    def __init__(self, probability, activity_threshold, pool_fee):
        super().__init__(probability=probability, activity_threshold=activity_threshold)
        self.pool_fee = pool_fee

    def setup_activiteit(self, brand, token, hb, exchange):
        pool_fee_tokens = self.pool_fee / token.get_prijs()
        
        # De brand moet eerst de pool fee betalen
        if brand.tokens < pool_fee_tokens:
            # Brand moet tokens kopen van de exchange om de pool fee te kunnen betalen
            missende_pool_fee_tokens = pool_fee_tokens - brand.tokens
            brand.koop_tokens(exchange, missende_pool_fee_tokens)
            
        # Als de brand genoeg tokens heeft, betaalt het de pool fee aan HB
        brand.betaal_pool_fee(token, hb, self.pool_fee)
            
    def deelname_activiteit(self, token, exchange, gebruiker, brand):
        
        # Controleren of de gebruiker beschikbaar is voor een activiteit        
        if not self.check_en_update_beschikbaarheid(gebruiker):
            return            
        
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = 3 * self.bereken_threshold(exchange) # multiply factor van 3 omdat we verwachten dat host activiteiten minder snel gedaan worden
        pool_fee_tokens = self.pool_fee / token.get_prijs()
        beloning = pool_fee_tokens * 0.1 # 5% van de pool_fee kan een gebruiker krijgen
        
        if gebruiker.activiteit_utility(token) > threshold:
            print("Gebruiker doet mee met de host activiteit")
            
            # Controleer of de Brand genoeg tokens heeft om de beloning uit te keren, anders kopen op de markt
            if brand.tokens < beloning:
                # Brand moet tokens kopen van de exchange om de pool fee te kunnen betalen
                missende_beloning_tokens = beloning - brand.tokens
                brand.koop_tokens(exchange, missende_beloning_tokens)
            
            if brand.tokens >= beloning:
                # Controleer of de gebruiker wint op basis van probability
                if random.random() < self.probability:
                    gebruiker.tokens += beloning
                    brand.tokens -= beloning
                    print(f"Gebruiker wint en ontvangt {beloning} tokens van de Brand.")
                else:
                    print("Gebruiker verliest, geen tokens uitbetaald.")
            else:
                print("Brand heeft niet genoeg tokens om de beloning uit te keren.") 
        
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")
  
class DataPool(Activiteiten):
     def __init__(self, probability, data_threshold, setup_fee):
         super().__init__(probability=probability, activity_threshold=data_threshold)
         self.setup_fee = setup_fee
         self.data_threshold = data_threshold
    
     def setup_activiteit(self, datapartner, token, hb, exchange):
         setup_fee_tokens = self.setup_fee / token.get_prijs()
         
         # De Data Partner moet eerst de setup fee betalen
         if datapartner.tokens < setup_fee_tokens:
             # Data Partner moet tokens kopen van de exchange om de setup fee te kunnen betalen
             missende_setup_fee_tokens = setup_fee_tokens - datapartner.tokens
             datapartner.koop_tokens(exchange, missende_setup_fee_tokens)
             
         # Als de data partner genoeg tokens heeft, betaalt het de setup fee aan HB
         datapartner.betaal_setup_fee(token, hb, self.setup_fee)
             
     def deelname_activiteit(self, token, exchange, gebruiker, datapartner):
         
         # Controleren of de gebruiker beschikbaar is voor een activiteit        
         if not self.check_en_update_beschikbaarheid(gebruiker):
             return
         
         # Gebruik de dynamisch berekende drempelwaarde
         threshold = self.bereken_threshold(exchange)
         setup_fee_tokens = self.setup_fee / token.get_prijs()
         beloning = setup_fee_tokens * 0.05 # 5% van de setup_fee kan een gebruiker krijgen
         
         if gebruiker.data_utility > threshold:
             print("Gebruiker doet mee met de data activiteit")
             
             # Controleer of de Datapartner genoeg tokens heeft om de beloning uit te keren, anders kopen op de markt
             if datapartner.tokens < beloning:
                 # Data Partner moet tokens kopen van de exchange om de beloning te kunnen uitkeren
                 missende_beloning_tokens = beloning - datapartner.tokens
                 datapartner.koop_tokens(exchange, missende_beloning_tokens)
             
             if datapartner.tokens >= beloning:
                 # Controleer of de gebruiker wint op basis van probability
                 if random.random() < self.probability:
                     gebruiker.tokens += beloning
                     datapartner.tokens -= beloning
                     print(f"Gebruiker wint en ontvangt {beloning} tokens van de Data Partner.")
                 else:
                     print("Gebruiker verliest, geen tokens uitbetaald.")
             else:
                 print("Data Partner heeft niet genoeg tokens om de beloning uit te keren.")
               
         else:
             print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")     
  
# we moeten nog de data partners en sponsored activiteiten toevoegen 

class Exchange:
    def __init__(self, token, liquidity):
        self.token = token # Referentie naar de token die wordt verhandeld
        self.vraag = 0
        self.aanbod = 0
        self.beschikbare_tokens = 0 # Totaal aantal tokens dat beschikbaar is voor verkoop op de markt
        self.tokens_op_markt = 0
        self.token_houders = {} # Dictionary om bij te houden welke partij hoeveel tokens aanbiedt
        self.liquidity = liquidity

    def koop_tokens(self, koper, aantal_tokens, liquidity):
        totale_kosten = aantal_tokens * self.token.get_prijs()
        
        # Controleer of er genoeg tokens zijn op de exchange
        if aantal_tokens > self.beschikbare_tokens:
            # Voeg tokens van Liquidity toe als er niet genoeg tokens beschikbaar zijn
            if liquidity.vrijgegeven_tokens > 0:
                self.voeg_tokens_toe(liquidity, liquidity.vrijgegeven_tokens, self.token)
                print("Liquidity tokens zijn toegevoegd aan de exchange omdat er niet genoeg tokens beschikbar waren.")
        
        # Controleer opnieuw of er nu genoeg tokens zijn na toevoeging van liquidity
        if aantal_tokens <= self.beschikbare_tokens and koper.cash >= totale_kosten:
            self.beschikbare_tokens -= aantal_tokens
            koper.tokens += aantal_tokens
            koper.cash -= totale_kosten
            self.vraag += aantal_tokens
            print(f"Koper heeft {aantal_tokens} tokens gekocht voor {totale_kosten} cash.")
        else:
            print("Niet genoeg tokens beschikbaar of onvoldoende cash.")
            
    def verkoop_tokens(self, koper, aantal_tokens):
        totale_opbrengst = aantal_tokens * self.token.get_prijs()
        if aantal_tokens <= koper.tokens:
            self.beschikbare_tokens += aantal_tokens
            koper.tokens -= aantal_tokens
            koper.cash += totale_opbrengst
            self.aanbod += aantal_tokens
            print(f"Koper heeft {aantal_tokens} tokens verkocht voor {totale_opbrengst} cash.")
        else:
            print("Niet genoeg tokens om te verkopen.")    

    def voeg_tokens_toe(self, bron, aantal_tokens, token):       
        
        # controleer dat het aantal_tokens dat op de markt wordt gebracht wel groter is dan 0
        if aantal_tokens <= 0:
            print("Aantal tokens moet groter zijn dan 0.")
            return False
            
        # Controleer of de bron een systeem- of investorklasse is
        if not isinstance(bron, (System, InvestorGroup)):
            print("Fout: Bron moet een instantie zijn van System of InvestorGroup klasse.")
            return False

        # Controleer of het aantal tokens dat toegevoegd wordt niet groter is dan de vrijgegeven tokens van de bron
        if aantal_tokens > bron.beschikbare_vrijgegeven_tokens:
            print("Fout: Aantal tokens dat wordt toegevoegd is groter dan het aantal beschikbare vrijgegeven tokens van de bron.")
            return False

        # Controleer of de investeerder zijn tokens op de markt wil brengen
        if isinstance(bron, InvestorGroup) and not bron.tokens_op_de_markt:
            print(f"{bron.__class__.__name__} wil zijn tokens niet op de markt brengen.")
            return False
        
        self.beschikbare_tokens += aantal_tokens
        if bron in self.token_houders:
            self.token_houders[bron] += aantal_tokens
        else:
            self.token_houders[bron] = aantal_tokens
       
        # Cash toekennen aan InvestorGroup wanneer tokens worden toegevoegd
        if isinstance(bron, InvestorGroup):
            cash_verdiend = aantal_tokens * token.get_prijs()
            bron.cash += cash_verdiend
            print(f"{bron.__class__.__name__} heeft {cash_verdiend} cash verdiend door {aantal_tokens} tokens op de markt te brengen.")
        else:
            print("Geen cash ontvangen omdat het een systeem is.")
        
        bron.tokens_op_markt += aantal_tokens
        self.tokens_op_markt += aantal_tokens
        bron.beschikbare_vrijgegeven_tokens -= aantal_tokens        
        token.maandelijkse_supply_vrijgeven(aantal_tokens)
        self.aanbod += aantal_tokens
        print(f"{aantal_tokens} tokens toegevoegd aan de markt door {bron}.")
        print(f"Er zijn {self.beschikbare_tokens} tokens beschikbaar op de markt.")
    
    def update_marktprijs(self):
        # Bereken de prijs op basis van totale vraag en aanbod in de iteratie
        self.token.update_prijs(self.vraag, self.aanbod)
        # Reset vraag en aanbod voor de volgende iteratie
        self.vraag = 0
        self.aanbod = 0
            
# in de simulatie moeten we ook nog een inbouwen dat een gebruiker maar aan 1 activiteit mee kan doen (misschien ook nog toevoegen dat een activiteit x aantal dagen duurt?)        

# start simulatie
# Voeg een knop toe om de simulatie te starten
if st.button("Start Simulatie"):
    
    # Configuratie instellen
    config = Configuratie()
    token = Token(config.total_supply, config.initial_token_price, elasticiteit=config.elasticiteit)
    liquidity = Liquidity(config.total_supply)
    exchange = Exchange(token=token, liquidity=liquidity)

    # Initialiseer HB (beheerder van de tokens)
    hb = HB()

    # Initialiseer de verschillende investeerdersgroepen
    FaF = FriendsAndFamily(config.total_supply)
    TaA = TeamAndAdvisors(config.total_supply)
    PSA = PublicSaleAirdrop(config.total_supply, tge_percentage=config.tge_psa)  # Bijvoorbeeld 25% in plaats van 20%
    Min = Mining(config.total_supply)
    Eco = Ecosystem(config.total_supply)

    # Initialiseer de datapartners en merken
    DP = DataPartner(config.initial_cash_datapartner)
    Bra = Brand(config.initial_cash_brands)

    # Initialiseer de activiteiten
    StandaardActiviteit1 = StandaardActiviteit(probability=0.9, activity_threshold=10)
    BurningActiviteit1 = BurningActiviteit(probability=0.9, activity_threshold=12)
    MiningActiviteit1 = MiningActiviteit(probability=0.9, activity_threshold=14)

    DataPool1 = DataPool(probability=1, data_threshold=30, setup_fee=config.setup_fee)
    HostActiviteit1 = HostActiviteit(probability=0.8, activity_threshold=20, pool_fee=config.pool_fee)

    activiteiten = [StandaardActiviteit1, BurningActiviteit1, MiningActiviteit1, DataPool1, HostActiviteit1]

    # Initialiseer de gebruikers
    gebruikers = []
    aantal_gebruiker = config.aantal_gebruiker
    for i in range(aantal_gebruiker):
        gebruiker = Gebruiker(id, cash=config.initial_cash_user, data_utility=75)
        gebruikers.append(gebruiker)

    # Initialiseer de speculators
    specs = []
    aantal_spec = config.aantal_speculators
    for i in range(aantal_spec):
        spec = Speculator(id, cash=config.initial_cash_speculator)
        specs.append(spec)

    # Start de eerste iteratie
    iteratie = 0
    FaF.vrijgave_tokens(iteratie)
    TaA.vrijgave_tokens(iteratie)
    PSA.vrijgave_tokens(iteratie)
    Min.vrijgave_tokens(iteratie)
    Eco.vrijgave_tokens(iteratie)
    liquidity.vrijgave_tokens(iteratie)
    
    # Dictionary om vrijgave van tokens bij te houden per iteratie voor elke groep
    vrijgave_per_iteratie = {
        "FriendsAndFamily": [],
        "TeamAndAdvisors": [],
        "PublicSaleAirdrop": [],
        "Mining": [],
        "Ecosystem": [],
        "Liquidity": []
    }
    
    # Dictionary om de utilities van activiteiten bij te houden
    activiteiten_utilities = {
        "Standaard": [],
        "Burning": [],
        "Mining": [],
        "Datapool": [],
        "Sponsored": []
    }
    
    # Lijsten om utilities van gebruikers en speculators bij te houden
    gebruiker_utilities = []
    speculator_koop_utilities = []
    speculator_verkoop_utilities = []
 
    # Lijst voor beschikbare tokens van de liquidity klasse per iteratie
    liquidity_tokens_over_time = []
    
    # Lijst voor de marktprijs over tijd
    marktprijs_over_time = []
    
    # Dictionary om het aantal tokens per klasse op de markt bij te houden
    tokens_op_markt_per_klasse = {
        "FriendsAndFamily": [],
        "TeamAndAdvisors": [],
        "PublicSaleAirdrop": [],
        "Mining": [],
        "Ecosystem": []
    }    
 
    # Hoofd iteratielus voor de simulatie
    iterations = config.iterations
    
    # Voeg een progress bar toe
    progress_bar = st.progress(0)
    status_text = st.empty()

    for iteratie in range(iterations):
         status_text.text(f"Iteratie {iteratie + 1} van {iterations} is bezig...")
         progress_bar.progress((iteratie + 1) / iterations)

         # Token vrijgave door de verschillende groepen per iteratie
         FaF.vrijgave_tokens(iteratie)
         TaA.vrijgave_tokens(iteratie)
         PSA.vrijgave_tokens(iteratie)
         Min.vrijgave_tokens(iteratie)
         Eco.vrijgave_tokens(iteratie)
         liquidity.vrijgave_tokens(iteratie)
     
         # Vrijgave opslaan in dictionary
         vrijgave_per_iteratie["FriendsAndFamily"].append(FaF.vrijgave_per_iteratie[-1])
         vrijgave_per_iteratie["TeamAndAdvisors"].append(TaA.vrijgave_per_iteratie[-1])
         vrijgave_per_iteratie["PublicSaleAirdrop"].append(PSA.vrijgave_per_iteratie[-1])
         vrijgave_per_iteratie["Mining"].append(Min.vrijgave_per_iteratie[-1])
         vrijgave_per_iteratie["Ecosystem"].append(Eco.vrijgave_per_iteratie[-1])
         vrijgave_per_iteratie["Liquidity"].append(liquidity.vrijgave_per_iteratie[-1])
     
         # Voeg tokens toe aan de exchange vanuit de verschillende groepen
         exchange.voeg_tokens_toe(PSA, PSA.beschikbare_vrijgegeven_tokens, token)
         exchange.voeg_tokens_toe(FaF, FaF.beschikbare_vrijgegeven_tokens * config.ratio_op_de_markt_investeerders, token)
         exchange.voeg_tokens_toe(TaA, TaA.beschikbare_vrijgegeven_tokens * config.ratio_op_de_markt_investeerders, token)
         exchange.voeg_tokens_toe(Min, Min.beschikbare_vrijgegeven_tokens * config.ratio_op_de_markt_systemen, token)
         exchange.voeg_tokens_toe(Eco, Eco.beschikbare_vrijgegeven_tokens * config.ratio_op_de_markt_systemen, token)
     
         # Groeimodel voor gebruikers
         if iteratie % 30 == 0:
             nieuw_aantal_gebruikers = int(len(gebruikers) * (1 + config.groeiratio_gebruiker))
             extra_gebruikers = nieuw_aantal_gebruikers - len(gebruikers)
         
             # Voeg nieuwe gebruikers toe
             for i in range(extra_gebruikers):
                 gebruiker = Gebruiker(id, cash=config.initial_cash_user, data_utility=75)
                 gebruikers.append(gebruiker)
     
         # Utilities van gebruikers bijhouden
         gebruiker_utilities_iteratie = [gebruiker.activiteit_utility(token) for gebruiker in gebruikers]
         gebruiker_utilities.append(sum(gebruiker_utilities_iteratie) / len(gebruikers))  # Gemiddelde utility van alle gebruikers
     
         # Utilities van speculators bijhouden
         speculator_koop_utilities_iteratie = [spec.koop_utility(token) for spec in specs]
         speculator_verkoop_utilities_iteratie = [spec.verkoop_utility(token) for spec in specs]
     
         speculator_koop_utilities.append(sum(speculator_koop_utilities_iteratie) / len(specs))  # Gemiddelde koop utility van alle speculators
         speculator_verkoop_utilities.append(sum(speculator_verkoop_utilities_iteratie) / len(specs))  # Gemiddelde verkoop utility van alle speculators

         # Elke iteratie betalen HostActiviteit en DataPool de setup fee
         HostActiviteit1.setup_activiteit(Bra, token, hb, exchange)
         DataPool1.setup_activiteit(DP, token, hb, exchange)
     
         # Gebruikers doen mee aan activiteiten
         for gebruiker in gebruikers:
             activiteit = random.choice(activiteiten)
             if isinstance(activiteit, StandaardActiviteit):
                 activiteit.deelname_activiteit(token, exchange, gebruiker, hb)
             elif isinstance(activiteit, BurningActiviteit):
                 activiteit.deelname_activiteit(token, exchange, gebruiker, Eco)
             elif isinstance(activiteit, MiningActiviteit):
                 activiteit.deelname_activiteit(token, exchange, gebruiker, Min)
             elif isinstance(activiteit, DataPool):
                 activiteit.deelname_activiteit(token, exchange, gebruiker, DP)
             elif isinstance(activiteit, HostActiviteit):
                 activiteit.deelname_activiteit(token, exchange, gebruiker, Bra)
         
             # Update de beschikbaarheid van de gebruiker voor de volgende activiteit
             if gebruiker.days_until_available > 0:
                 gebruiker.days_until_available -= 1
     
         # Activiteiten utilities bijhouden
         activiteiten_utilities["Standaard"].append(activiteiten[0].bereken_threshold(exchange))
         activiteiten_utilities["Burning"].append(activiteiten[1].bereken_threshold(exchange))
         activiteiten_utilities["Mining"].append(activiteiten[2].bereken_threshold(exchange))
         activiteiten_utilities["Datapool"].append(activiteiten[3].bereken_threshold(exchange))
         activiteiten_utilities["Sponsored"].append(activiteiten[4].bereken_threshold(exchange))
     
         # Groeimodel voor speculators
         if iteratie % 30 == 0:
             nieuw_aantal_speculators = int(len(specs) * (1 + config.groeiratio_speculators))
             extra_speculators = nieuw_aantal_speculators - len(specs)
         
             # Voeg nieuwe speculators toe
             for i in range(extra_speculators):
                 spec = Speculator(id, cash=config.initial_cash_speculator)
                 specs.append(spec)        
     
         # Laat speculators handelen
         for spec in specs:
             handelbare_tokens = spec.bepaal_aantal_tokens_om_te_handelen(token)
             if spec.koop_utility(token) > spec.verkoop_utility(token):
                 spec.koop_tokens(exchange, handelbare_tokens)
             elif spec.verkoop_utility(token) > spec.koop_utility(token):
                 spec.verkoop_tokens(exchange, handelbare_tokens)
     
         # Update de marktprijs
         exchange.update_marktprijs()

         # Houd de beschikbare tokens van de liquidity klasse bij
         liquidity_tokens_over_time.append(liquidity.beschikbare_vrijgegeven_tokens)
         
         # Houd de marktprijs per iteratie bij
         marktprijs_over_time.append(token.get_prijs())
        
         # Houd het aantal tokens op de markt per klasse bij
         tokens_op_markt_per_klasse["FriendsAndFamily"].append(FaF.tokens_op_markt)
         tokens_op_markt_per_klasse["TeamAndAdvisors"].append(TaA.tokens_op_markt)
         tokens_op_markt_per_klasse["PublicSaleAirdrop"].append(PSA.tokens_op_markt)
         tokens_op_markt_per_klasse["Mining"].append(Min.tokens_op_markt)
         tokens_op_markt_per_klasse["Ecosystem"].append(Eco.tokens_op_markt)

    status_text.text("Simulatie voltooid!")
    progress_bar.progress(1.0)

    # Bereken de finale marktprijs en de percentuele verandering ten opzichte van de initiële tokenprijs
    finale_marktprijs = token.get_prijs()
    initial_price = config.initial_token_price
    percentuele_verandering = ((finale_marktprijs - initial_price) / initial_price) * 100
    
    # Print de eindresultaten
    st.write(f"Finale Marktprijs: {finale_marktprijs:.6f}")
    st.write(f"Percentuele Verandering ten opzichte van de Initiële Token Prijs: {percentuele_verandering:.2f}%")
    st.write(f"Totaal aantal tokens op de markt: {exchange.tokens_op_markt}")
    st.write(f"Totaal aantal geburnde tokens: {hb.totale_burned_tokens}")
    st.write(f"Totaal aantal tokens HB: {hb.tokens}")
    
    # Toon de vrijgave van tokens per iteratie
    st.write("Vrijgave van Tokens per Iteratie")
    st.line_chart(vrijgave_per_iteratie)
    
    # Toon de marktprijs over tijd in Streamlit
    st.write("Marktprijs van de Token over Tijd")
    st.line_chart(marktprijs_over_time)
    
    # Toon de beschikbare tokens van de liquidity klasse over tijd
    st.write("Beschikbare Tokens van de Liquidity Klasse over Tijd")
    st.line_chart(liquidity_tokens_over_time)
    
    # Toon het aantal tokens op de markt per klasse over tijd
    for klasse, tokens_per_iteratie in tokens_op_markt_per_klasse.items():
        st.write(f"Tokens op de markt - {klasse}")
        st.line_chart(tokens_per_iteratie)
    
    # Maak de matplotlib-plot met stippellijnen voor activiteit utilities
    plt.figure(figsize=(10, 6))
    
    # Plot de activiteit utilities met stippellijnen
    plt.plot(activiteiten_utilities["Standaard"], label="Standaard", linestyle='--')
    plt.plot(activiteiten_utilities["Burning"], label="Burning", linestyle='--')
    plt.plot(activiteiten_utilities["Mining"], label="Mining", linestyle='--')
    plt.plot(activiteiten_utilities["Datapool"], label="Datapool", linestyle='--')
    plt.plot(activiteiten_utilities["Sponsored"], label="Sponsored", linestyle='--')
    
    # Voeg de gebruiker en speculator utilities toe met doorlopende lijnen
    plt.plot(gebruiker_utilities, label="Gemiddelde Gebruiker Utility")
    plt.plot(speculator_koop_utilities, label="Gemiddelde Speculator Koop Utility")
    plt.plot(speculator_verkoop_utilities, label="Gemiddelde Speculator Verkoop Utility")
    
    # Voeg labels, titel en legenda toe
    plt.xlabel("Iteraties")
    plt.ylabel("Utility")
    plt.title("Ontwikkeling van Utilities per Iteratie")
    plt.legend()
    
    # Toon de plot in Streamlit
    st.pyplot(plt)