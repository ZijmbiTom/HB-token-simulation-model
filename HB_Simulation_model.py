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
initial_token_price = st.sidebar.number_input("Initial Token Price", value=0.0001)
total_supply = st.sidebar.number_input("Total Supply", value=500000000000)
initial_cash_user = st.sidebar.number_input("Initial Cash per User", value=1000)
initial_cash_speculator = st.sidebar.number_input("Initial Cash per Speculator", value=3000)
initial_cash_datapartner = st.sidebar.number_input("Initial Cash for Data Partner", value=10000)
initial_cash_brands = st.sidebar.number_input("Initial Cash for Brands", value=10000)
setup_fee = st.sidebar.number_input("Setup Fee", value=10000)
pool_fee = st.sidebar.number_input("Pool Fee", value=10000)
aantal_gebruikers = st.sidebar.number_input("Aantal gebruikers", value=1000)
groeiratio_gebruiker = st.sidebar.number_input("Groeipercentage gebruikers per dag", value=1)
aantal_speculators = st.sidebar.number_input("Aantal speculators", value=1000)
groeiratio_speculators = st.sidebar.number_input("Groeipercentage speculators per dag", value=1)
iterations = st.sidebar.number_input("Iterations", value=1000)

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

class Token:
    '''
    De token klasse die alle eigenschappen van de tokens bijhoudt
    '''
    # Attributen
    def __init__(self, token_supply, initial_token_price):
        self.__totale_supply = token_supply
        self.__circulerende_supply = 0
        self.__prijs = initial_token_price
    
    # Methodes    
    def maandelijkse_supply_vrijgeven(self, hoeveelheid):
        self.__circulerende_supply += hoeveelheid

    def burn_tokens(self, hoeveelheid):
        self.__circulerende_supply -= hoeveelheid
        
    def bereken_prijs(self, vraag, aanbod):
        if aanbod > 0:
            elasticiteit = vraag / aanbod # Eenvoudige prijs berekening
            self.__prijs *= elasticiteit
        else:
            self.__prijs = self.__prijs
            
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
        
    def koop_tokens(self, exchange, aantal_tokens, liquidity=None):
        # Liquidity wordt standaard toegewezen als deze niet is opgegeven
        if liquidity is None:
            liquidity = exchange.liquidity  # Verwijst naar een liquidity-klasse die je aan de exchange koppelt
        
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
        self.random_factor = random_factor if random_factor is not None else random.uniform(1, 3)
        
    def aciviteit_utility(self, token):    
        value = 1 + 2 * self.tokens + 1 * self.cash + (self.tokens * token.get_prijs())  # Prijs heeft een lichte invloed
            
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

        if koop_utility > verkoop_utility:
            # Bereken hoeveel tokens nodig zijn om het verschil te overbruggen
            delta_tokens = 0
            while self.verkoop_utility(token, tokens = (self.tokens + delta_tokens)) < koop_utility:
                delta_tokens += 1  # Verhoog de tokens met kleine stappen om te verfijnen
            return delta_tokens
        elif koop_utility < verkoop_utility:
            # Bereken hoeveel tokens nodig zijn om het verschil te overbruggen
            delta_tokens = 0
            while self.koop_utility(token, tokens = (self.tokens - delta_tokens)) < verkoop_utility:
                delta_tokens += 1  # Verlaag de tokens met kleine stappen om te verfijnen
            return delta_tokens  # Negatief omdat het verkopen betreft
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
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 13, 20, 12)        

class Liquidity(System):
    def __init__(self, totale_supply):
        super().__init__(totale_supply, 10, 100, 0)   

class Brand:
    def __init__(self, cash):
        self.cash = cash
        self.tokens = 0
        
    def koop_tokens(self, exchange, aantal_tokens):
        totale_kosten = aantal_tokens * exchange.token.get_prijs()
        if self.cash >= totale_kosten:
            exchange.verkoop_tokens(self, aantal_tokens)
            self.tokens += aantal_tokens
            self.cash -= totale_kosten
            print(f"Brand heeft {aantal_tokens} tokens gekocht voor {totale_kosten} cash.")
        else:
            print(f"Brand heeft niet genoeg cash om {aantal_tokens} tokens te kopen.")

    def betaal_pool_fee(self, token, hb, pool_fee):
        if self.tokens >= pool_fee:
            self.tokens -= pool_fee
            hb.ontvang_setup_fee(token, pool_fee)
            print(f"Brand heeft de pool fee van {pool_fee} tokens betaald aan HB.")
        else:
            print("Brand heeft niet genoeg tokens om de pool fee te betalen.")
            return False
        return True

class DataPartner:
    def __init__(self, cash):
        self.cash = cash
        self.tokens = 0
        
    def koop_tokens(self, exchange, aantal_tokens):
        totale_kosten = aantal_tokens * exchange.token.get_prijs()
        if self.cash >= totale_kosten:
            exchange.verkoop_tokens(self, aantal_tokens)
            self.tokens += aantal_tokens
            self.cash -= totale_kosten
            print(f"Data Partner heeft {aantal_tokens} tokens gekocht voor {totale_kosten} cash.")
        else:
            print(f"Data Partner heeft niet genoeg cash om {aantal_tokens} tokens te kopen.")

    def betaal_setup_fee(self, token, hb, setup_fee):
        if self.tokens >= setup_fee:
            self.tokens -= setup_fee
            hb.ontvang_setup_fee(token, setup_fee)
            print(f"Data Partner heeft de setup_fee van {setup_fee} tokens betaald aan HB.")
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
    def __init__(self, inleg, beloning, probability, activity_threshold):
        self.inleg = inleg
        self.beloning = beloning
        self.probability = probability
        self.activity_threshold = activity_threshold

    def bereken_threshold(self, exchange):
        # Basis berekening van de drempelwaarde
        return self.activity_threshold + math.log(1 + exchange.tokens_op_markt / 100000)

class StandaardActiviteit(Activiteiten):
    def __init__(self, inleg, beloning, probability, activity_threshold):
        super().__init__(inleg, beloning, probability, activity_threshold)

    def deelname_activiteit(self, token, exchange, gebruiker, hb):
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = self.bereken_threshold(exchange)

        # Controleer of de utility van de gebruiker hoger is dan de threshold
        if gebruiker.aciviteit_utility(token) > threshold:
            print("Gebruiker doet mee met de standaard activiteit")
            # Controleer of de gebruiker wint op basis van probability
            
            # Check nog of gebruiker genoeg tokens heeft, anders kopen
            if gebruiker.tokens < self.inleg:
                print("Gebruiker heeft niet genoeg geld om aan de activiteit te deelnemen, dus koopt extra tokens")
                missende_tokens = (self.inleg - gebruiker.tokens)
                gebruiker.koop_tokens(exchange, missende_tokens)
    
            # Met een bepaalde kans krijgen de deelnemers tokens na hun inleg
            if random.random() < self.probability:
                gebruiker.tokens += (self.beloning - self.inleg)
                print("Gebruiker wint")
            else: 
                gebruiker.tokens -= self.inleg
                hb.tokens += self.inleg * 0.9 # 90% procent van de inleg gaat naar HB als de deelnemer faalt
                hb.burn_tokens(token, self.inleg*0.1) # 10% van de inleg wordt geburned
                print("Gebruiker verliest")
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")
     
# ik wil beloning altijd op 0 zetten, dus kijken hoe dat moet
class BurningActiviteit(Activiteiten):
    def __init__(self, inleg, beloning, probability, activity_threshold):
        super().__init__(inleg, 0, probability, activity_threshold)
        
    def deelname_activiteit(self, token, exchange, gebruiker, ecosystem):
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = self.bereken_threshold(exchange)
        
        # Controleer of de utility van de gebruiker hoger is dan de threshold
        if gebruiker.aciviteit_utility(token) > threshold:
            print("Gebruiker doet mee met de burning activiteit")
            
            # check nog of gebruiker genoeg tokens heeft, anders kopen
            if gebruiker.tokens < self.inleg:
                print("Gebruiker heeft niet genoeg geld om aan de activiteit te deelnemen, dus koopt extra tokens")
                missende_tokens = (self.inleg - gebruiker.tokens)
                gebruiker.koop_tokens(exchange, missende_tokens)
                
            if random.random() < self.probability:
                gebruiker.tokens -= self.inleg
                token.burn_tokens(self.inleg)
                print("Gebruiker wint, en de tokens worden geburnt")
            else: 
                gebruiker.tokens -= self.inleg
                ecosystem.ontvang_burn_tokens(self.inleg)
                print("Gebruiker verliest, en de tokens worden naar het ecosystem gestuurd")
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")   

class MiningActiviteit(Activiteiten):
    def __init__(self, inleg, beloning, probability, activity_threshold):
        super().__init__(inleg, 0, probability, activity_threshold)
        
    def deelname_activiteit(self, token, exchange, gebruiker, mining):
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = self.bereken_threshold(exchange)
        
        # Controleer of de utility van de gebruiker hoger is dan de threshold
        if gebruiker.aciviteit_utility(token) > threshold:
            print("Gebruiker doet mee met de mining activiteit")
            # Controleer of de gebruiker wint op basis van probability
            
            # check nog of gebruiker genoeg tokens heeft, anders kopen
            if gebruiker.tokens < self.inleg:
                print("Gebruiker heeft niet genoeg geld om aan de activiteit te deelnemen, dus koopt extra tokens")
                missende_tokens = (self.inleg - gebruiker.tokens)
                gebruiker.koop_tokens(exchange, missende_tokens)
                
            if random.random() < self.probability:
                gebruiker.tokens -= self.inleg
                token.burn_tokens(self.inleg)
                print("Gebruiker wint, en de tokens worden geburnt")
            else: 
                gebruiker.tokens -= self.inleg
                mining.ontvang_mining_tokens(self.inleg)
                print("Gebruiker verliest, en de tokens worden naar de mining gestuurd")
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")   

class HostActiviteit(Activiteiten):
    def __init__(self, beloning, probability, activity_threshold, pool_fee):
        super().__init__(inleg=0, beloning=beloning, probability=probability, activity_threshold=activity_threshold)
        self.pool_fee = pool_fee

    def setup_activiteit(self, brand, token, hb, exchange):
        # De brand moet eerst de pool fee betalen
        if brand.tokens < self.pool_fee:
            # Brand moet tokens kopen van de exchange om de pool fee te kunnen betalen
            missende_pool_fee_tokens = self.pool_fee - brand.tokens
            brand.koop_tokens(exchange, missende_pool_fee_tokens)
            
        # Als de brand genoeg tokens heeft, betaalt het de pool fee aan HB
        brand.betaal_pool_fee(token, hb, self.pool_fee)
            
    def deelname_activiteit(self, token, exchange, gebruiker, brand):
        # Gebruik de dynamisch berekende drempelwaarde
        threshold = 5 * self.bereken_threshold(exchange) # multiply factor van 5 omdat we verwachten dat host activiteiten minder snel gedaan worden
        
        if gebruiker.aciviteit_utility(token) > threshold:
            print("Gebruiker doet mee met de host activiteit")
            
            # Controleer of de Brand genoeg tokens heeft om de beloning uit te keren, anders kopen op de markt
            if brand.tokens < self.beloning:
                # Brand moet tokens kopen van de exchange om de pool fee te kunnen betalen
                missende_beloning_tokens = self.beloning - brand.tokens
                brand.koop_tokens(exchange, missende_beloning_tokens)
            
            if brand.tokens >= self.beloning:
                # Controleer of de gebruiker wint op basis van probability
                if random.random() < self.probability:
                    gebruiker.tokens += self.beloning
                    brand.tokens -= self.beloning
                    print("Gebruiker wint en ontvangt tokens van de Brand.")
                else:
                    print("Gebruiker verliest, geen tokens uitbetaald.")
            else:
                print("Brand heeft niet genoeg tokens om de beloning uit te keren.")
        else:
            print(f"{gebruiker.id} heeft niet genoeg utility om deel te nemen aan deze activiteit.")
  
class DataPool(Activiteiten):
     def __init__(self, beloning, probability, data_threshold, setup_fee):
         super().__init__(inleg=0, beloning=beloning, probability=probability, activity_threshold=data_threshold)
         self.setup_fee = setup_fee
         self.data_threshold = data_threshold
    
     def setup_activiteit(self, datapartner, token, hb, exchange):
         # De Data Partner moet eerst de setup fee betalen
         if datapartner.tokens < self.setup_fee:
             # Data Partner moet tokens kopen van de exchange om de setup fee te kunnen betalen
             missende_setup_fee_tokens = self.setup_fee - datapartner.tokens
             datapartner.koop_tokens(exchange, missende_setup_fee_tokens)
             
         # Als de data partner genoeg tokens heeft, betaalt het de setup fee aan HB
         datapartner.betaal_setup_fee(token, hb, self.setup_fee)
             
     def deelname_activiteit(self, token, exchange, gebruiker, datapartner):
         # Gebruik de dynamisch berekende drempelwaarde
         threshold = self.bereken_threshold(exchange)
         
         if gebruiker.data_utility > threshold:
             print("Gebruiker doet mee met de data activiteit")
             
             # Controleer of de Datapartner genoeg tokens heeft om de beloning uit te keren, anders kopen op de markt
             if datapartner.tokens < self.beloning:
                 # Data Partner moet tokens kopen van de exchange om de beloning te kunnen uitkeren
                 missende_beloning_tokens = self.beloning - datapartner.tokens
                 datapartner.koop_tokens(exchange, missende_beloning_tokens)
             
             if datapartner.tokens >= self.beloning:
                 # Controleer of de gebruiker wint op basis van probability
                 if random.random() < self.probability:
                     gebruiker.tokens += self.beloning
                     datapartner.tokens -= self.beloning
                     print("Gebruiker wint en ontvangt tokens van de Data Partner.")
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

    def koop_tokens(self, user, aantal_tokens, liquidity):
        totale_kosten = aantal_tokens * self.token.get_prijs()
        
        # Controleer of er genoeg tokens zijn op de excgabge
        if aantal_tokens > self.beschikbare_tokens:
            # Voeg tokens van Liquidity toe als er niet genoeg tokens beschikbaar zijn
            if liquidity.vrijgegeven_tokens > 0:
                self.voeg_tokens_toe(liquidity, liquidity.vrijgegeven_tokens, self.token)
                print("Liquidity tokens zijn toegevoegd aan de exchange omdat er niet genoeg tokens beschikbar waren.")
        
        # Controleer opnieuw of er nu genoeg tokens zijn na toevoeging van liquidity
        if aantal_tokens <= self.beschikbare_tokens and user.cash >= totale_kosten:
            self.beschikbare_tokens -= aantal_tokens
            user.tokens += aantal_tokens
            user.cash -= totale_kosten
            self.vraag += aantal_tokens
            print(f"{user.id} heeft {aantal_tokens} tokens gekocht voor {totale_kosten} cash.")
        else:
            print("Niet genoeg tokens beschikbaar of onvoldoende cash.")
            
    def verkoop_tokens(self, user, aantal_tokens):
        totale_opbrengst = aantal_tokens * self.token.get_prijs()
        if aantal_tokens <= user.tokens:
            self.beschikbare_tokens += aantal_tokens
            user.tokens -= aantal_tokens
            user.cash += totale_opbrengst
            self.aanbod += aantal_tokens
            print(f"{user.id} heeft {aantal_tokens} tokens verkocht voor {totale_opbrengst} cash.")
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
    config = Configuratie()
    token = Token(config.total_supply, config.initial_token_price)
    liquidity = Liquidity(config.total_supply)
    exchange = Exchange(token=token, liquidity=liquidity)

    hb = HB()

    FaF = FriendsAndFamily(config.total_supply)
    TaA = TeamAndAdvisors(config.total_supply)
    PSA = PublicSaleAirdrop(config.total_supply)
    Min = Mining(config.total_supply)
    Eco = Ecosystem(config.total_supply)

    DP = DataPartner(config.initial_cash_datapartner)
    Bra = Brand(config.initial_cash_brands)

    StandaardActiviteit1 = StandaardActiviteit(inleg=1000, beloning=1500, probability=0.9, activity_threshold=5)
    BurningActiviteit1 = BurningActiviteit(inleg=1000, beloning=1500, probability=0.9, activity_threshold=5)
    MiningActiviteit1 = MiningActiviteit(inleg=1000, beloning=1500, probability=0.9, activity_threshold=5)

    DataPool1 = DataPool(beloning=5000, probability=1, data_threshold=50, setup_fee=config.setup_fee)
    HostActiviteit1 = HostActiviteit(beloning=2000, probability=0.8, activity_threshold=10, pool_fee=config.pool_fee)

    activiteiten = [StandaardActiviteit1, BurningActiviteit1, MiningActiviteit1, DataPool1, HostActiviteit1]

    gebruikers = []
    aantal_gebruiker = config.aantal_gebruiker

    for i in range(aantal_gebruiker):
        gebruiker = Gebruiker(id, cash=config.initial_cash_user, data_utility=75)
        gebruikers.append(gebruiker)

    specs = []
    aantal_spec = config.aantal_speculators

    for i in range(aantal_spec):
        spec = Speculator(id, cash=config.initial_cash_speculator)
        specs.append(spec)

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

    activiteiten_utilities = {
        "Standaard": [],
        "Burning": [],
        "Mining": [],
        "Datapool": [],
        "Sponsored": []
    }

    gebruiker_utilities = []
    speculator_koop_utilities = []
    speculator_verkoop_utilities = []

    iterations = config.iterations
    for iteratie in range(iterations):
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

        exchange.voeg_tokens_toe(PSA, PSA.beschikbare_vrijgegeven_tokens, token)
        exchange.voeg_tokens_toe(FaF, FaF.beschikbare_vrijgegeven_tokens * 0.01, token)
        exchange.voeg_tokens_toe(TaA, TaA.beschikbare_vrijgegeven_tokens * 0.01, token)
        exchange.voeg_tokens_toe(Min, Min.beschikbare_vrijgegeven_tokens * 0.005, token)
        exchange.voeg_tokens_toe(Eco, Eco.beschikbare_vrijgegeven_tokens * 0.005, token)

        # Groeimodel voor gebruikers
        nieuw_aantal_gebruikers = int(len(gebruikers) * (1 + config.groeiratio_gebruiker))
        extra_gebruikers = nieuw_aantal_gebruikers - len(gebruikers)

        for i in range(extra_gebruikers):
            gebruiker = Gebruiker(id, cash=config.initial_cash_user, data_utility=75)
            gebruikers.append(gebruiker)

        # Utilities bijhouden
        gebruiker_utilities_iteratie = [gebruiker.aciviteit_utility(token) for gebruiker in gebruikers]
        gebruiker_utilities.append(sum(gebruiker_utilities_iteratie) / len(gebruikers))  # Gemiddelde utility van alle gebruikers

        speculator_koop_utilities_iteratie = [spec.koop_utility(token) for spec in specs]
        speculator_verkoop_utilities_iteratie = [spec.verkoop_utility(token) for spec in specs]

        speculator_koop_utilities.append(sum(speculator_koop_utilities_iteratie) / len(specs))  # Gemiddelde koop utility van alle speculators
        speculator_verkoop_utilities.append(sum(speculator_verkoop_utilities_iteratie) / len(specs))  # Gemiddelde verkoop utility van alle speculators

        for gebruiker in gebruikers:
            activiteit = random.choice(activiteiten)
            if isinstance(activiteit, StandaardActiviteit):
                activiteit.deelname_activiteit(token, exchange, gebruiker, hb)
            elif isinstance(activiteit, BurningActiviteit):
                activiteit.deelname_activiteit(token, exchange, gebruiker, Eco)
            elif isinstance(activiteit, MiningActiviteit):
                activiteit.deelname_activiteit(token, exchange, gebruiker, Min)
            elif isinstance(activiteit, DataPool):
                activiteit.setup_activiteit(DP, token, hb, exchange)
                activiteit.deelname_activiteit(token, exchange, gebruiker, DP)
            elif isinstance(activiteit, HostActiviteit):
                activiteit.setup_activiteit(Bra, token, hb, exchange)
                activiteit.deelname_activiteit(token, exchange, gebruiker, Bra)

        activiteiten_utilities["Standaard"].append(activiteiten[0].bereken_threshold(exchange))
        activiteiten_utilities["Burning"].append(activiteiten[1].bereken_threshold(exchange))
        activiteiten_utilities["Mining"].append(activiteiten[2].bereken_threshold(exchange))
        activiteiten_utilities["Datapool"].append(activiteiten[3].bereken_threshold(exchange))
        activiteiten_utilities["Sponsored"].append(activiteiten[4].bereken_threshold(exchange))

        # Groeimodel voor speculators
        nieuw_aantal_speculators = int(len(specs) * (1 + config.groeiratio_speculators))
        extra_speculators = nieuw_aantal_speculators - len(specs)

        for i in range(extra_speculators):
            spec = Speculator(id, cash=config.initial_cash_speculator)
            specs.append(spec)

        for spec in specs:
            handelbare_tokens = spec.bepaal_aantal_tokens_om_te_handelen(token)
            if spec.koop_utility(token) > spec.verkoop_utility(token):
                spec.koop_tokens(exchange, handelbare_tokens)
            elif spec.verkoop_utility(token) > spec.koop_utility(token):
                spec.verkoop_tokens(exchange, handelbare_tokens)

        exchange.update_marktprijs()

    st.write("Simulatie succesvol!")
    st.write(f"Finale Marktprijs: {token.get_prijs()}")
    st.write(f"Totale Circulerende Tokens: {token.get_circulerende_tokens()}")
    st.write(f"Totaal aantal tokens op de markt: {exchange.tokens_op_markt}")

    st.line_chart(vrijgave_per_iteratie)

    # Combineer de activiteit utilities en de gemiddelde gebruiker/speculator utilities in één plot
    combined_utilities = {
        "Standaard": activiteiten_utilities["Standaard"],
        "Burning": activiteiten_utilities["Burning"],
        "Mining": activiteiten_utilities["Mining"],
        "Datapool": activiteiten_utilities["Datapool"],
        "Sponsored": activiteiten_utilities["Sponsored"],
        "Gemiddelde Gebruiker Utility": gebruiker_utilities,
        "Gemiddelde Speculator Koop Utility": speculator_koop_utilities,
        "Gemiddelde Speculator Verkoop Utility": speculator_verkoop_utilities
    }

    # Gebruik Streamlit's line_chart voor de gecombineerde utilities
    st.line_chart(combined_utilities)