import re
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
import requests
from rasa_sdk.events import SlotSet, AllSlotsReset
from dotenv import load_dotenv
import os

# Carica il contenuto del file .env
load_dotenv()

# Accedi alle variabili
API_KEY = os.getenv("RAPID_API_KEY")

HEADERS = {
    "x-rapidapi-key": API_KEY,
	"x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

URL_HOTELS = "https://booking-com15.p.rapidapi.com/api/v1/hotels"
URL_FLIGHTS = "https://booking-com15.p.rapidapi.com/api/v1/flights"
URL_ATTRACTIONS = "https://booking-com15.p.rapidapi.com/api/v1/attraction"

class resetSlot(Action):
    def name(self) -> Text:
        return "action_reset_slots"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [AllSlotsReset()]

class SeachHotels(Action):
    def name(self) -> Text:
        return "action_search_hotels"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        partenza = tracker.get_slot("partenza")
        ritorno = tracker.get_slot("ritorno")
        num_persone = tracker.get_slot("num_persone")
        num_camere = tracker.get_slot("num_camere")

        dest_id = tracker.get_slot("luogo")

        url = f"{URL_HOTELS}/searchHotels"

        querystring = {
            "dest_id":dest_id,
            "search_type":"CITY",
            "arrival_date":partenza,
            "departure_date":ritorno,
            "adults":num_persone,
            "room_qty":num_camere,
            "page_number":"1",
            "languagecode":"it",
            "currency_code":"EUR"
        }

        response = requests.get(url, headers=HEADERS, params=querystring)

        hotels = response.json()["data"]["hotels"][:10]

        hotels_data = []
        for i, hotel in enumerate(hotels):
            hotel = hotels[i]["property"]
            id_hotel = hotels[i]["hotel_id"]
            name = hotel["name"]
            if "-" in name:
                name = name.split("-")[0].strip()
            description = hotels[i]["accessibilityLabel"].split("\n")[2:]
            unwanted_keywords = {"EUR", "recensioni", "prezzo"}
            filtered_description = [line for line in description if not any(keyword.lower() in line.lower() for keyword in unwanted_keywords)]
            description = " ".join(filtered_description)
            photo_url = hotel["photoUrls"][0]
            checkin = f"{hotel['checkin']['fromTime']} - {hotel['checkin']['untilTime']}"
            checkout = f"{hotel['checkout']['fromTime']} - {hotel['checkout']['untilTime']}"
            review = f"{hotel['reviewScoreWord']} ({hotel['reviewScore']}/10) su {hotel['reviewCount']} recensioni"
            price = f"{hotel['priceBreakdown']['grossPrice']['value']} {hotel['priceBreakdown']['grossPrice']['currency']}"
            old_price = hotel["priceBreakdown"].get("strikethroughPrice", {}).get("value")

            hotel_info = {
                "name": name,
                "hotel_id": id_hotel
            }

            hotels_data.append(hotel_info)

            message = f"🏨 {name}\n📍 {description}\n🕑 Check-in: {checkin}\n🕛 Check-out: {checkout}\n⭐ Recensioni: {review}\n💰 Prezzo più basso: {price}"
            if old_price:
                message += f" (Scontato da {old_price} euro)"
            
            buttons = [
                {
                    "title": f"Mostra camere",
                    "payload": f"/mostra_camere{{\"nome_hotel\": \"{id_hotel}\"}}"
                },
                {
                    "title": f"Maggiori info",
                    "payload": f"/info_hotel{{\"nome_hotel\": \"{id_hotel}\"}}"
                }
            ]

            dispatcher.utter_message(text=message, buttons=buttons)

        return [SlotSet("hotels", hotels_data), SlotSet("nome_hotel", None)]
    
class validateSearchHotels(FormValidationAction):
    def name(self) -> Text:
        return "validate_hotel_form"

    def validate_luogo_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        if not slot_value:
            dispatcher.utter_message(text="❌ Per favore, inserisci una destinazione valida.")
            return {"luogo": None, "luogo_name": None}

        url = f"{URL_HOTELS}/searchDestination"

        querystring = {"query": slot_value}

        response = requests.get(url, headers=HEADERS, params=querystring)

        try:
            dest_id = response.json()["data"][0]["dest_id"]
        except:
            dispatcher.utter_message(text="❌ Non ho trovato questa destinazione. Riprova con un altro nome.")
            return {"luogo": None, "luogo_name": None}         
        
        return {"luogo_name": slot_value, "luogo": dest_id}
    
    def validate_partenza(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(pattern, slot_value):
            dispatcher.utter_message("❌ Formato data non valido. Usa il formato YYYY-MM-DD (es. 2024-03-05).")
            return {"partenza": None}
        
        return {"partenza": slot_value}
    
    def validate_ritorno(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(pattern, slot_value):
            dispatcher.utter_message("❌ Formato data non valido. Usa il formato YYYY-MM-DD (es. 2024-03-05).")
            return {"ritorno": None}
        
        return {"ritorno": slot_value}
    
    def validate_num_persone(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            num_persone = int(slot_value)
            if num_persone <= 0:
                dispatcher.utter_message("❌ Il numero di persone deve essere maggiore di 0.")
                return {"num_persone": None}
        except ValueError:
            dispatcher.utter_message("❌ Il numero di persone deve essere un valore numerico valido.")
            return {"num_persone": None}
        
        return {"num_persone": num_persone}

    def validate_num_camere(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            num_camere = int(slot_value)
            num_persone = tracker.get_slot("num_persone")

            if num_camere <= 0:
                dispatcher.utter_message("❌ Il numero di camere deve essere maggiore di 0.")
                return {"num_camere": None}

            if num_persone is not None:
                num_persone = int(num_persone)
                if num_camere > num_persone:
                    dispatcher.utter_message("❌ Il numero di camere non può essere maggiore del numero di persone.")
                    return {"num_camere": None}
        
        except ValueError:
            dispatcher.utter_message("❌ Il numero di camere deve essere un valore numerico valido.")
            return {"num_camere": None}
        
        return {"num_camere": num_camere}
    
class infoHotel(Action):
    def name(self) -> Text:
        return "action_info_hotel"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        hotels = tracker.get_slot("hotels")
        if not hotels:
            dispatcher.utter_message(text="❌ Nessun hotel trovato. Effettua prima una ricerca.")
            return []

        offer_index = None
        nome_hotel = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "nome_hotel":
                nome_hotel = entity.get("value")
        
        if nome_hotel is None:
            nome_hotel = tracker.get_slot("nome_hotel")
            
        if nome_hotel is None:
            dispatcher.utter_message(text="❌ Non so a quale hotel ti riferisci!")
            return[SlotSet("nome_hotel", None)]
        else:
            for hotel in hotels:
                    if hotel["name"].lower() == nome_hotel.lower():
                        offer_index = hotel['hotel_id']
                        break
        if offer_index is None:
            dispatcher.utter_message(text="❌ Non ho trovato l'hotel che cerchi!")
            return[SlotSet("nome_hotel", None)]

        partenza = tracker.get_slot("partenza")
        ritorno = tracker.get_slot("ritorno")
        num_persone = tracker.get_slot("num_persone")
        num_camere = tracker.get_slot("num_camere")

        querystring = {
            "hotel_id": offer_index,
            "arrival_date": partenza,
            "departure_date": ritorno,
            "adults": num_persone,
            "room_qty": num_camere,
            "languagecode": "it",
            "currency_code": "EUR"
        }
        
        url = f"{URL_HOTELS}/getHotelDetails"
        response = requests.get(url, headers=HEADERS, params=querystring)
        data = response.json()
        
        hotel = data.get("data", {})
        raw = data.get("rawData", {})
        block = data.get("block", [{}])[0]
        rooms = hotel.get("rooms", {})

        room_description = "Nessuna descrizione disponibile"
        if rooms:
            first_room = next(iter(rooms.values()))
            room_description = first_room.get("description", room_description)

        facilities = hotel.get("facilities_block", {}).get("facilities", [])
        facilities_str = ", ".join([f"{fac.get('name')} ({fac.get('icon')})" for fac in facilities])
        
        message = (
            f"🏨 {hotel.get('hotel_name')}\n"
            f"📍 Indirizzo: {hotel.get('address')}, {hotel.get('city')}, {hotel.get('country_trans')} (CAP: {hotel.get('zip')})\n"
            f"🛏️ Tipo: {hotel.get('accommodation_type_name')}\n"
            f"📏 Distanza dal centro: {hotel.get('distance_to_cc')} km\n"
            f"🛎️ Check-in: {hotel.get('arrival_date')} (dalle {raw.get('checkin', {}).get('fromTime')} alle {raw.get('checkin', {}).get('untilTime')})\n"
            f"🕙 Check-out: {hotel.get('departure_date')} (dalle {raw.get('checkout', {}).get('fromTime')} alle {raw.get('checkout', {}).get('untilTime')})\n"
            f"⭐ Recensioni: {hotel.get('review_nr')} recensioni - Voto: {raw.get('reviewScore')} ({raw.get('reviewScoreWord')})\n"
            f"💶 Prezzo a partire da: {hotel.get('product_price_breakdown', {}).get('gross_amount_hotel_currency', {}).get('amount_rounded')}\n"
            f"🗣️ Lingue parlate: {', '.join(hotel.get('spoken_languages', []))}\n"
            f"✅ Servizi: {facilities_str}\n"
            f"🛌 Descrizione: {room_description}\n"
            f"📜 Cancellazione: {block.get('block_text', {}).get('policies', [{}])[0].get('content')}\n"
            f"🔗 Maggiori info: {hotel.get('url')}"
        )
        
        dispatcher.utter_message(text=message)
        photo_urls = raw.get("photoUrls", [])

        if photo_urls:
            for url in photo_urls:
                dispatcher.utter_message(image=url)
        else:
            dispatcher.utter_message(text="Nessuna immagine disponibile.")
        return[SlotSet("nome_hotel", hotel.get('hotel_name'))]
        
class mostraCamere(Action):
    def name(self) -> Text:
        return "action_mostra_camere"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        hotels = tracker.get_slot("hotels")

        if not hotels:
            dispatcher.utter_message(text="❌ Nessun hotel trovato. Effettua prima una ricerca.")
            return []

        offer_index = None
        nome_hotel = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "nome_hotel":
                nome_hotel = entity.get("value")

        if nome_hotel is None:
            nome_hotel = tracker.get_slot("nome_hotel")
            
        if nome_hotel is None:
            dispatcher.utter_message(text="❌ Non so a quale hotel ti riferisci!")
            return[SlotSet("nome_hotel", None)]
        else:
            for hotel in hotels:
                    if hotel["name"].lower() == nome_hotel.lower():
                        offer_index = hotel['hotel_id']
                        break
        if offer_index is None:
            dispatcher.utter_message(text="❌ Non ho trovato l'hotel che cerchi!")
            return[SlotSet("nome_hotel", None)]
        
        partenza = tracker.get_slot("partenza")
        ritorno = tracker.get_slot("ritorno")
        num_persone = tracker.get_slot("num_persone")
        num_camere = tracker.get_slot("num_camere")

        url = f"{URL_HOTELS}/getRoomList"

        querystring = {
            "hotel_id": offer_index,
            "arrival_date": partenza,
            "departure_date": ritorno,
            "adults": num_persone,
            "room_qty": num_camere,
            "languagecode": "it",
            "currency_code": "EUR"
        }

        response = requests.get(url, headers=HEADERS, params=querystring)

        data = response.json().get("data", {})

        camere_block = data.get("block", [])
        camere_rooms = data.get("rooms", {})

        camere_uniche = {} 
        camere_data = []

        for camera in camere_block:
            id_camera = str(camera.get('room_id', ''))
            nome_camera = camera.get('name_without_policy', 'N/A')
            costo = camera.get('product_price_breakdown', {}).get('all_inclusive_amount_hotel_currency', {}).get('amount_unrounded', 'N/A')
            policies = camera.get('block_text', {}).get('policies', [])

            if id_camera in camere_rooms:
                room = camere_rooms[id_camera]
                highlights = room.get('highlights', [])
                descrizione = room.get('description', 'Descrizione non disponibile')
                foto_url = room.get('photos', [{}])[0].get('url_original', '')

                if id_camera not in camere_uniche:
                    
                    camera_info = {
                        "hotel_id": offer_index,
                        "name": nome_camera,
                        "id_camera": id_camera
                    }

                    camere_data.append(camera_info)
                    
                    camere_uniche[id_camera] = True

                    highlights_text = "✨"
                    policies_text = "✋🏼"
                    highlights_text += "\n✨".join([highlight['translated_name'] for highlight in highlights])
                    policies_text += "\n✋🏼".join([policy['content'] for policy in policies])

                    message = (
                        f"🏨 {nome_camera}\n"
                        f"📍 {descrizione}\n"
                        f"📜 Politiche:\n {policies_text}\n"
                        f"🏡 Punti forti:\n {highlights_text}\n"
                        f"💰 Prezzo: {costo}"
                    )
                    
                    button = [
                        {
                            "title": "Prenota camera",
                            "payload": f"/prenota_camera{{\"id_camera\": \"{id_camera}\"}}"   
                        }
                    ]

                    if foto_url:
                        dispatcher.utter_message(image=foto_url)  # 2️⃣ Poi la foto
                    dispatcher.utter_message(text=message, buttons=button)  # 1️⃣ Prima il messaggio

        if not camere_uniche:
            dispatcher.utter_message(text="❌ Nessuna camera trovata per questo hotel.")

        return [SlotSet("camere", camere_data), SlotSet("nome_hotel", nome_hotel)]

class prenotazioneCamera(Action):
    def name(self) -> Text:
        return "action_prenota_camera"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        camere = tracker.get_slot("camere")
        id_camera = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "id_camera":
                id_camera = entity.get("value")
                break

        if id_camera is None:
            dispatcher.utter_message(text="❌ Non ho trovato la camera!")
            return []
        
        dispatcher.utter_message(text=f"✅ Camera prenotata correttamente!")
        return [SlotSet("nome_hotel", None)]
    
class nearAttractions(Action):
    def name(self) -> Text:
        return "action_near_attractions"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        hotels = tracker.get_slot("hotels")

        if not hotels:
            dispatcher.utter_message(text="❌ Nessun hotel trovato. Effettua prima una ricerca.")
            return []

        offer_index = None
        nome_hotel = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "nome_hotel":
                nome_hotel = entity.get("value")

        if nome_hotel is None:
            nome_hotel = tracker.get_slot("nome_hotel")
            
        if nome_hotel is None:
            dispatcher.utter_message(text="❌ Non so a quale hotel ti riferisci!")
            return[SlotSet("nome_hotel", None)]
        else:
            for hotel in hotels:
                    if hotel["name"].lower() == nome_hotel.lower():
                        offer_index = hotel['hotel_id']
                        break
        if offer_index is None:
            dispatcher.utter_message(text="❌ Non ho trovato l'hotel cercato!")
            return[SlotSet("nome_hotel", None)]
        
        url = f"{URL_HOTELS}/getPopularAttractionNearBy"

        querystring = {
            "hotel_id": offer_index,
            "languagecode": "it"
        }

        response = requests.get(url, headers=HEADERS, params=querystring)

        data = response.json().get("data", {})

        # Estrai le liste dal json
        popular = data.get("popular_landmarks", [])
        closest = data.get("closest_landmarks", [])

        if not popular and not closest:
            dispatcher.utter_message(text=f"❌ Nessuna attrazione trovata nelle vicinanze dell'hotel {nome_hotel}!")
            return[]
        
        # Se popular_landmarks è vuoto, usa closest_landmarks
        if not popular:
            popular = closest.copy()  # copia per non modificare l'originale
        
        # Prendi le prime 10 attrazioni
        attractions = popular[:10]
        
        # Costruisci il messaggio
        message_lines = [f"🌟 Attrazioni principali vicine a {nome_hotel}:"]
        for attr in attractions:
            tag = attr.get("tag", "N/D")
            # Formatta la distanza a 2 decimali se è un numero
            distance = attr.get("distance", "N/D")
            if isinstance(distance, (float, int)):
                distance = f"{distance:.2f}"
            average = attr.get("average_out_of_10", "N/D")
            votes = attr.get("total_votes", "N/D")
            
            message_lines.append(
                f"🏛️ {tag}\n Distanza: {distance} km\n Voto medio: {average}/10\n Voti totali: {votes}"
            )
        
        message = "\n".join(message_lines)
        dispatcher.utter_message(text=message)

        return [SlotSet("nome_hotel", nome_hotel)]

class searchFlights(Action):
    def name(self) -> Text:
        return "action_search_flights"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        from_id = tracker.get_slot("from")
        to_id = tracker.get_slot("to")
        
        partenza = tracker.get_slot("partenza")
        ritorno = tracker.get_slot("ritorno")
        num_persone = tracker.get_slot("num_persone")
        
        querystring = {
            "fromId": from_id,
            "toId": to_id,
            "departDate": partenza,
            "returnDate": ritorno,
            "pageNo": "1",
            "adults": num_persone,
            "sort": "BEST",
            "cabinClass": "ECONOMY",
            "currency_code": "EUR"
        }
        
        url = f"{URL_FLIGHTS}/searchFlights"
        
        response = requests.get(url, headers=HEADERS, params=querystring)
        data = response.json()["data"]

        # Lista in cui accumuliamo i messaggi per ciascuna offerta
        message_list = []
        scali = {}
        flights=[]
        buttons = []
        # Itera su ogni flightOffer
        for offer_index, offer in enumerate(data.get("flightOffers", [])):  
            offer_message = []            
            segments = offer.get("segments", [])
            labels = ["andata"] + ["ritorno"] * (len(segments) - 1)
            scali_message = []
            offer_message.append(
                f"✈️ Volo #{offer_index}\n"
                f"━━━━━━━━━━━━━━━━━"
            )
            flights_info = {
                "index": offer_index
            }
            flights.append(flights_info)
            for label, seg in zip(labels, segments):
                dep_airport = seg.get("departureAirport", {})
                arr_airport = seg.get("arrivalAirport", {})
                departureTime = seg.get("departureTime", {})
                arrivalTime = seg.get("arrivalTime", {})
                totalTime = int(seg.get("totalTime", 0))
                hours = totalTime // 3600
                minutes = (totalTime % 3600) // 60
                legs = seg.get("legs", [])
                num_scali = 0 if len(legs) == 1 else len(legs)
                scali_msg = "Diretto" if num_scali == 0 else f"Numero scali: {num_scali - 1}"
                seg_message = (
                    f"🛫 {label.capitalize()}:\n"
                    f"📍 Da {dep_airport.get('name', 'N/D')} ({dep_airport.get('cityName', 'N/D')}, {dep_airport.get('province', 'N/D')})\n"
                    f"📍 A {arr_airport.get('name', 'N/D')} ({arr_airport.get('cityName', 'N/D')}, {arr_airport.get('province', 'N/D')})\n"
                    f"🕒 Partenza: {departureTime}\n"
                    f"🕓 Arrivo: {arrivalTime}\n"
                    f"🔀 {scali_msg}\n"
                    f"⏳ Durata totale: {hours} h {minutes} min\n"
                    f"━━━━━━━━━━━━━━━━━"
                )

                offer_message.append(seg_message)
                
                if num_scali != 0:
                    scali_message.append(
                        f"\n🏷️ {label.capitalize()}\n"
                        f"━━━━━━━━━━━━━━━━━"
                    )

                    for leg in legs:
                        dep_leg = leg.get("departureAirport", {})
                        arr_leg = leg.get("arrivalAirport", {})
                        total_time = int(leg.get("totalTime", 0))
                        hours = total_time // 3600
                        minutes = (total_time % 3600) // 60
                        departureTimeLeg = leg.get("departureTime", {})
                        arrivalTimeLeg = leg.get("arrivalTime", {})
                        leg_message = (
                            f"📍 Scalo:\n"
                            f"✈️ Da {dep_leg.get('name', 'N/D')} ({dep_leg.get('cityName', 'N/D')}, {dep_leg.get('province', 'N/D')})\n"
                            f"✈️ A {arr_leg.get('name', 'N/D')} ({arr_leg.get('cityName', 'N/D')}, {arr_leg.get('province', 'N/D')})\n"
                            f"🕒 Partenza: {departureTimeLeg}\n"
                            f"🕓 Arrivo: {arrivalTimeLeg}\n"
                            f"⏳ Durata: {hours}h {minutes}min\n"
                        )

                        # Estrae i nomi delle compagnie aeree
                        carriers = leg.get("carriersData", [])
                        carrier_name = carriers[0].get("name", "N/D")

                        # Aggiunge la compagnia aerea
                        leg_message += (
                            f"🛫 Compagnia: {carrier_name}\n"
                            f"━━━━━━━━━━━━━━━━━"
                        )

                        scali_message.append(leg_message)

                        scali[str(offer_index)] = "\n".join(scali_message)
                else:
                    compagnia = legs[0]["carriersData"][0]["name"]
                    seg_message = (
                        f"Compagnia: {compagnia}"
                    )
                    offer_message.append(seg_message)
                    
            price = offer.get("priceBreakdown", {}).get("total", {})
            # Combina unità e nanos (i nanos li interpretiamo qui in maniera semplificata)
            total_price = f"{price.get('currencyCode', '')} {price.get('units', 0)}.{str(price.get('nanos', 0))[:2]}"
            offer_message.append(f"💰 Prezzo Totale: {total_price}")
            #offer_message.append("\n".join(scali_message))
            
            # Aggiunge il messaggio completo per l'offerta corrente alla lista
            message_list.append("\n".join(offer_message))
            if num_scali != 0:
                buttons = [
                    {
                        "title": f"Visualizza scali",
                        "payload": f"/show_scali{{\"offer_index\": \"{offer_index}\"}}"
                    }
                ]
                dispatcher.utter_message(text="\n".join(offer_message), buttons=buttons, parse_mode="markdown")
            else:
                dispatcher.utter_message(text="\n".join(offer_message), parse_mode="markdown")

        
        return [SlotSet("scali", scali), SlotSet("flight_index", None), SlotSet("flights", flights)]
    
class ShowScali(Action):
    def name(self) -> Text:
        return "action_show_scali"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        offer_index = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "offer_index":
                offer_index = entity.get("value")
                break
        
        flights = None
        flights = tracker.get_slot("flights")
        if flights is None:
            dispatcher.utter_message(text="❌ Devi prima effettuare una ricerca!")
            return[SlotSet("flight_index", None)]
        
        exists_flight = any(str(item.get("index")) == str(offer_index) for item in flights)
        if offer_index is None or not exists_flight:
            dispatcher.utter_message(text="❌ Non ho trovato l'indice del volo!")
            return[SlotSet("flight_index", None)]
        
        try:
            stops_details = tracker.get_slot("scali")[0][offer_index]
        except: 
            dispatcher.utter_message(text="❌ Non ci sono scali per il viaggio scelto!")
            return[SlotSet("flight_index", None)]
        
        message = f"Informazione sugli scali del volo #{offer_index}\n"

        #message += stops_details[0][offer_index]
        message += stops_details
        dispatcher.utter_message(text=message, parse_mode="markdown")
        
        # Aggiungi il bottone per la prenotazione del volo
        booking_button = {
            "title": "Prenota Volo",
            "payload": f"/prenota_volo{{\"offer_index\": \"{offer_index}\"}}"
        }
        dispatcher.utter_message(
            text="Se desideri prenotare questo volo, clicca qui:",
            buttons=[booking_button]
        )
        
        return [SlotSet("flight_index", offer_index)]
    
class prenotazioneVolo(Action):
    def name(self) -> Text:
        return "action_prenota_volo"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        offer_index = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "offer_index":
                offer_index = entity.get("value")
                break

        flights = tracker.get_slot("flights")
        if flights is None:
            dispatcher.utter_message(text="❌ Devi prima effettuare una ricerca!")
            return[]

        if offer_index is None:
            offer_index = tracker.get_slot("flight_index")
        
        exists_index = any(str(item.get("index")) == str(offer_index) for item in flights)
        if offer_index is None or not exists_index:
            dispatcher.utter_message(text="❌ Non ho trovato l'indice del volo!")
            return [SlotSet("flight_index", None)]
        
        dispatcher.utter_message(text=f"✅ Volo {offer_index} prenotato correttamente!")
        return [SlotSet("flight_index", None)]
        
class validateSearchFlights(FormValidationAction):
    def name(self) -> Text:
        return "validate_flights_form"
    
    def validate_from_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verifica che il valore inserito non sia vuoto
        if not slot_value:
            dispatcher.utter_message(text="❌ Per favore, inserisci una destinazione valida.")
            return {"from": None, "from_name": None}

        url = f"{URL_FLIGHTS}/searchDestination"
        
        querystring = {"query":slot_value, "languagecode": "it"}
        
        response = requests.get(url, headers=HEADERS, params=querystring)

        try:
            from_id = response.json()["data"][0]["id"]     
        except:
            dispatcher.utter_message(text="❌ Il luogo inserito non esiste!")
            return {"from": None, "from_name": None}            
        
        return {"from": from_id, "from_name": slot_value}

    def validate_to_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verifica che il valore inserito non sia vuoto
        if not slot_value:
            dispatcher.utter_message(text="❌ Per favore, inserisci una destinazione valida.")
            return {"to": None, "to_name": None}

        url = f"{URL_FLIGHTS}/searchDestination"
        
        querystring = {"query":slot_value, "languagecode": "it"}
        
        response = requests.get(url, headers=HEADERS, params=querystring)

        try:
            to_id = response.json()["data"][0]["id"]     
        except:
            dispatcher.utter_message(text="❌ Il luogo inserito non esiste!")
            return {"to": None, "to_name": None}            
        
        return {"to": to_id, "to_name": slot_value}
    
    def validate_partenza(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(pattern, slot_value):
            dispatcher.utter_message("❌ Formato data non valido. Usa il formato YYYY-MM-DD (es. 2024-03-05).")
            return {"partenza": None}
        
        return {"partenza": slot_value}
    
    def validate_ritorno(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(pattern, slot_value):
            dispatcher.utter_message("❌ Formato data non valido. Usa il formato YYYY-MM-DD (es. 2024-03-05).")
            return {"ritorno": None}
        
        return {"ritorno": slot_value}
    
    def validate_num_persone(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            num_persone = int(slot_value)
            if num_persone <= 0:
                dispatcher.utter_message("❌ Il numero di persone deve essere maggiore di 0.")
                return {"num_persone": None}
        except ValueError:
            dispatcher.utter_message("❌ Il numero di persone deve essere un valore numerico valido.")
            return {"num_persone": None}
        
        return {"num_persone": num_persone}

class createItinerary(Action):
    def name(self) -> Text:
        return "action_create_itinerary"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        # Recupero degli slot necessari
        from_id = tracker.get_slot("from")
        dest_id = tracker.get_slot("to_name")
        to_id = tracker.get_slot("to")
        partenza = tracker.get_slot("partenza")
        ritorno = tracker.get_slot("ritorno")
        num_persone = tracker.get_slot("num_persone")
        num_camere = tracker.get_slot("num_camere")
        
        url = f"{URL_FLIGHTS}/searchDestination"
        
        querystring = {"query": dest_id, "languagecode": "it"}
        
        response = requests.get(url, headers=HEADERS, params=querystring)

        to_id = response.json()["data"][0]["id"]
        
        if not to_id:
            dispatcher.utter_message(text="❌ Il luogo inserito non esiste!")
            return []  
        
        querystring = {
            "fromId": from_id,
            "toId": to_id,
            "departDate": partenza,
            "returnDate": ritorno,
            "pageNo": "1",
            "adults": num_persone,
            "sort": "BEST",
            "cabinClass": "ECONOMY",
            "currency_code": "EUR"
        }
        
        url = f"{URL_FLIGHTS}/searchFlights"

        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            data = response.json()["data"]
            flight_offers = data.get("flightOffers", [])
        except Exception as e:
            dispatcher.utter_message(text=f"❌ Errore durante la ricerca dei voli: {e}")
            return []

        # Trova volo più economico
        cheapest_flight = None
        cheapest_flight_price = float('inf')

        for idx, offer in enumerate(flight_offers):
            price_info = offer.get("priceBreakdown", {}).get("total", {})
            units = price_info.get("units", "0")
            nanos = price_info.get("nanos", 0)
            flight_price_float = float(f"{units}.{str(nanos)[:2] if nanos else '00'}")
            
            if flight_price_float < cheapest_flight_price:
                cheapest_flight_price = flight_price_float
                cheapest_flight = (idx, offer)
                
        url = f"{URL_HOTELS}/searchDestination"

        querystring = {"query": dest_id}

        response = requests.get(url, headers=HEADERS, params=querystring)

        dest_id = response.json()["data"][0]["dest_id"]

        url = f"{URL_HOTELS}/searchHotels"
        querystring = {
            "dest_id":dest_id,
            "search_type":"CITY",
            "arrival_date":partenza,
            "departure_date":ritorno,
            "adults":num_persone,
            "room_qty":num_camere,
            "page_number":"1",
            "languagecode":"it",
            "currency_code":"EUR"
        }

        try:
            response = requests.get(url, headers=HEADERS, params=querystring)
            hotels = response.json()["data"]["hotels"]
        except Exception as e:
            dispatcher.utter_message(text=f"❌ Errore durante la ricerca degli hotel: {e}")
            return []

        cheapest_hotel = None
        cheapest_hotel_price = float('inf')

        for hotel_item in hotels:
            hotel_prop = hotel_item.get("property", {})
            price_info = hotel_prop.get("priceBreakdown", {}).get("grossPrice", {})
            current_price = price_info.get("value", 0)
            if current_price < cheapest_hotel_price:
                cheapest_hotel_price = current_price
                cheapest_hotel = hotel_item

        if not cheapest_flight:
            dispatcher.utter_message(text="Non ho trovato alcun volo disponibile per le date inserite.")
            return []
        if not cheapest_hotel:
            dispatcher.utter_message(text="Non ho trovato alcun hotel disponibile per le date inserite.")
            return []

        cheapest_flight_index, cheapest_flight_offer = cheapest_flight

        # -------------------------
        # 5) Costruisco output volo (simile a action_search_flights)
        # -------------------------
        volo_message_parts = []
        segments = cheapest_flight_offer.get("segments", [])

        volo_message_parts.append(
            "✈️ Il volo più economico che ho trovato\n"
            "━━━━━━━━━━━━━━━━━"
        )

        if segments:
            # la tua logica: la prima è "andata", le altre "ritorno"
            labels = ["andata"] + ["ritorno"] * (len(segments) - 1)
            scali_message = []
            for label, seg in zip(labels, segments):
                dep_airport = seg.get("departureAirport", {})
                arr_airport = seg.get("arrivalAirport", {})
                departureTime = seg.get("departureTime", {})
                arrivalTime = seg.get("arrivalTime", {})
                totalTime = int(seg.get("totalTime", 0))
                hours = totalTime // 3600
                minutes = (totalTime % 3600) // 60
                legs = seg.get("legs", [])
                num_scali = 0 if len(legs) == 1 else len(legs)
                scali_msg = "Diretto" if num_scali == 0 else f"Numero scali: {num_scali - 1}"
                seg_message = (
                    f"🛫 {label.capitalize()}:\n"
                    f"📍 Da {dep_airport.get('name', 'N/D')} ({dep_airport.get('cityName', 'N/D')}, {dep_airport.get('province', 'N/D')})\n"
                    f"📍 A {arr_airport.get('name', 'N/D')} ({arr_airport.get('cityName', 'N/D')}, {arr_airport.get('province', 'N/D')})\n"
                    f"🕒 Partenza: {departureTime}\n"
                    f"🕓 Arrivo: {arrivalTime}\n"
                    f"🔀 {scali_msg}\n"
                    f"⏳ Durata totale: {hours} h {minutes} min\n"
                    f"━━━━━━━━━━━━━━━━━"
                )

                volo_message_parts.append(seg_message)
                
                if num_scali != 0:
                    scali_message.append(
                        f"\n🏷️ {label.capitalize()}\n"
                        f"━━━━━━━━━━━━━━━━━"
                    )

                    for leg in legs:
                        dep_leg = leg.get("departureAirport", {})
                        arr_leg = leg.get("arrivalAirport", {})
                        total_time = int(leg.get("totalTime", 0))
                        hours = total_time // 3600
                        minutes = (total_time % 3600) // 60
                        departureTimeLeg = leg.get("departureTime", {})
                        arrivalTimeLeg = leg.get("arrivalTime", {})
                        leg_message = (
                            f"📍 Scalo:\n"
                            f"✈️ Da {dep_leg.get('name', 'N/D')} ({dep_leg.get('cityName', 'N/D')}, {dep_leg.get('province', 'N/D')})\n"
                            f"✈️ A {arr_leg.get('name', 'N/D')} ({arr_leg.get('cityName', 'N/D')}, {arr_leg.get('province', 'N/D')})\n"
                            f"🕒 Partenza: {departureTimeLeg}\n"
                            f"🕓 Arrivo: {arrivalTimeLeg}\n"
                            f"⏳ Durata: {hours}h {minutes}min\n"
                        )

                        # Estrae i nomi delle compagnie aeree
                        carriers = leg.get("carriersData", [])
                        carrier_name = carriers[0].get("name", "N/D")

                        # Aggiunge la compagnia aerea
                        leg_message += (
                            f"🛫 Compagnia: {carrier_name}\n"
                            f"━━━━━━━━━━━━━━━━━"
                        )

                        scali_message.append(leg_message)
                else:
                    compagnia = legs[0]["carriersData"][0]["name"]
                    seg_message = (
                        f"Compagnia: {compagnia}"
                    )
                    volo_message_parts.append(seg_message)
            
            # if scali_message:
                # volo_message_parts.append("Dettagli scali:\n" + "\n".join(scali_message))

        # Prezzo totale
        price_total = f"EUR {cheapest_flight_price:.2f}"
        volo_message_parts.append(f"\n💰 Prezzo Totale: {price_total}")

        if num_scali != 0:
            buttons_flight = [
                {
                    "title": f"Visualizza scali",
                    "payload": f"/show_scali{{\"offer_index\": \"{cheapest_flight_index}\"}}"
                }
            ]
            dispatcher.utter_message(text="\n".join(volo_message_parts), buttons=buttons_flight)
        else:
            dispatcher.utter_message(text="\n".join(volo_message_parts))

        # -------------------------
        # 6) Costruisco output hotel (simile a action_search_hotels)
        # -------------------------
        hotel_prop = cheapest_hotel.get("property", {})
        name = hotel_prop.get("name", "Hotel Sconosciuto")

        full_description = cheapest_hotel.get("accessibilityLabel", "")
        splitted_description = full_description.split("\n")[2:] if full_description else []
        unwanted_keywords = {"EUR", "recensioni", "prezzo"}
        filtered_description = [
            line for line in splitted_description 
            if not any(keyword.lower() in line.lower() for keyword in unwanted_keywords)
        ]
        description = " ".join(filtered_description) if filtered_description else "N/D"

        checkin_time = "N/D"
        checkout_time = "N/D"
        if "checkin" in hotel_prop:
            checkin_time = f"{hotel_prop['checkin'].get('fromTime', '')} - {hotel_prop['checkin'].get('untilTime', '')}"
        if "checkout" in hotel_prop:
            checkout_time = f"{hotel_prop['checkout'].get('fromTime', '')} - {hotel_prop['checkout'].get('untilTime', '')}"

        review_score_word = hotel_prop.get("reviewScoreWord", "N/D")
        review_score = hotel_prop.get("reviewScore", "N/D")
        review_count = hotel_prop.get("reviewCount", "N/D")
        review = f"{review_score_word} ({review_score}/10) su {review_count} recensioni"

        price_value = hotel_prop.get("priceBreakdown", {}).get("grossPrice", {}).get("value", 0)
        currency = hotel_prop.get("priceBreakdown", {}).get("grossPrice", {}).get("currency", "EUR")
        price_str = f"{price_value} {currency}"

        old_price_value = hotel_prop.get("priceBreakdown", {}).get("strikethroughPrice", {}).get("value")

        hotel_msg = (
            f"🏨 {name}\n"
            f"📍 {description}\n"
            f"🕑 Check-in: {checkin_time}\n"
            f"🕛 Check-out: {checkout_time}\n"
            f"⭐ Recensioni: {review}\n"
            f"💰 Prezzo più basso: {price_str}"
        )
        if old_price_value:
            hotel_msg += f" (Scontato da {old_price_value} EUR)"

        # Aggiungo pulsanti per l'hotel (Mostra camere e Info):
        buttons_hotel = [
            {
                "title": "Mostra camere",
                "payload": f'/mostra_camere{{"nome_hotel":"{name}"}}'
            },
            {
                "title": "Maggiori info",
                "payload": f'/info_hotel{{"nome_hotel":"{name}"}}'
            }
        ]

        # -------------------------
        # 7) Invio messaggi finali
        # -------------------------
        # Mando due messaggi separati: uno per il volo con pulsante, uno per l'hotel con pulsanti
        dispatcher.utter_message(text=hotel_msg, buttons=buttons_hotel)

        return [SlotSet("nome_hotel", name)]

class validateItinerary(FormValidationAction):
    def name(self) -> Text:
        return "validate_itinerary_form"
    
    def validate_from_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verifica che il valore inserito non sia vuoto
        if not slot_value:
            dispatcher.utter_message(text="❌ Per favore, inserisci una destinazione valida.")
            return {"from": None, "from_name": None}

        url = f"{URL_FLIGHTS}/searchDestination"
        
        querystring = {"query":slot_value, "languagecode": "it"}
        
        response = requests.get(url, headers=HEADERS, params=querystring)

        try:
            from_id = response.json()["data"][0]["id"]     
        except:
            dispatcher.utter_message(text="❌ Il luogo inserito non esiste!")
            return {"from": None, "from_name": None}            
        
        return {"from": from_id, "from_name": slot_value}

    def validate_to_name(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verifica che il valore inserito non sia vuoto
        if not slot_value:
            dispatcher.utter_message(text="❌ Per favore, inserisci una destinazione valida.")
            return {"to": None, "to_name": None}

        url = f"{URL_FLIGHTS}/searchDestination"
        
        querystring = {"query":slot_value, "languagecode": "it"}
        
        response = requests.get(url, headers=HEADERS, params=querystring)

        try:
            to_id = response.json()["data"][0]["id"]     
        except:
            dispatcher.utter_message(text="❌ Il luogo inserito non esiste!")
            return {"to": None, "to_name": None}            
        
        return {"to": to_id, "to_name": slot_value, "luogo": slot_value}
    
    def validate_partenza(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(pattern, slot_value):
            dispatcher.utter_message("❌ Formato data non valido. Usa il formato YYYY-MM-DD (es. 2024-03-05).")
            return {"partenza": None}
        
        return {"partenza": slot_value}
    
    def validate_ritorno(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
                
        pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(pattern, slot_value):
            dispatcher.utter_message("❌ Formato data non valido. Usa il formato YYYY-MM-DD (es. 2024-03-05).")
            return {"ritorno": None}
        
        return {"ritorno": slot_value}
    
    def validate_num_persone(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            num_persone = int(slot_value)
            if num_persone <= 0:
                dispatcher.utter_message("❌ Il numero di persone deve essere maggiore di 0.")
                return {"num_persone": None}
        except ValueError:
            dispatcher.utter_message("❌ Il numero di persone deve essere un valore numerico valido.")
            return {"num_persone": None}
        
        return {"num_persone": num_persone}

    def validate_num_camere(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            num_camere = int(slot_value)
            num_persone = tracker.get_slot("num_persone")

            if num_camere <= 0:
                dispatcher.utter_message("❌ Il numero di camere deve essere maggiore di 0.")
                return {"num_camere": None}

            if num_persone is not None:
                num_persone = int(num_persone)
                if num_camere > num_persone:
                    dispatcher.utter_message("❌ Il numero di camere non può essere maggiore del numero di persone.")
                    return {"num_camere": None}
        
        except ValueError:
            dispatcher.utter_message("❌ Il numero di camere deve essere un valore numerico valido.")
            return {"num_camere": None}
        
        return {"num_camere": num_camere}
