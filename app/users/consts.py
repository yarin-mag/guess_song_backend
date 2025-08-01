from google.cloud import firestore

NEW_USER_DATA = {
    "is_subscribed": False,
    "guesses_left": 5,
    "subscription_start_date": None,
    "subscription_end_date_net": None,
    "subscription_end_date_gross": None,
    "agree_to_conditions_and_terms": None,
    "subscription_id": None,
    "monthly_payment": None,
    "payment_history": []
}