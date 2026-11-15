"""Built-in synthetic evaluation set.

Fictional online-bookstore domain. All data is invented for demo purposes:
no real books, customers, or production data are involved.
"""
from __future__ import annotations

from typing import TypedDict


class EvalCase(TypedDict):
    id: str
    question: str
    gold: str
    answer: str


# Each case ships with a sample agent answer so the service can run an
# evaluation with no request body at all. Most sample answers are good
# (they should pass); two are deliberately weak so the judge shows it
# can discriminate.
BUILTIN_CASES: list[EvalCase] = [
    {
        "id": "bks-01",
        "question": "Do you have 'The Starlight Atlas' in paperback?",
        "gold": "Yes, 'The Starlight Atlas' is in stock in paperback for $18.99.",
        "answer": "Yes, 'The Starlight Atlas' is available in paperback for $18.99 and in stock.",
    },
    {
        "id": "bks-02",
        "question": "What is the return window for a damaged book?",
        "gold": "Damaged books can be returned within 30 days for a full refund.",
        "answer": "You can return a damaged book within 30 days and get a full refund.",
    },
    {
        "id": "bks-03",
        "question": "How much is shipping to Canada?",
        "gold": "Shipping to Canada costs $6.99 and takes 5-8 business days.",
        "answer": "Shipping to Canada is $6.99 and usually takes 5-8 business days.",
    },
    {
        "id": "bks-04",
        "question": "Can I gift-wrap my order?",
        "gold": "Yes, gift wrapping is available for $3.50 per order.",
        "answer": "Yes, we offer gift wrapping for $3.50 per order.",
    },
    {
        "id": "bks-05",
        "question": "Do you sell ebooks?",
        "gold": "Yes, most titles are available as ebooks in EPUB and PDF formats.",
        "answer": "Yes, most of our titles are available as ebooks in EPUB and PDF.",
    },
    {
        "id": "bks-06",
        "question": "What is the price of 'Rivers of Ember' hardcover?",
        "gold": "The hardcover of 'Rivers of Ember' costs $27.50.",
        "answer": "The hardcover edition of 'Rivers of Ember' is $27.50.",
    },
    {
        "id": "bks-07",
        "question": "How do I track my order?",
        "gold": "Use the tracking link in your confirmation email or the Orders page in your account.",
        "answer": "You can track your order from the link in your confirmation email or on the Orders page.",
    },
    {
        "id": "bks-08",
        "question": "Is 'The Cartographer's Daughter' in stock?",
        "gold": "Yes, 'The Cartographer's Daughter' is in stock; 12 copies available.",
        "answer": "Yes, it is in stock with 12 copies available right now.",
    },
    {
        "id": "bks-09",
        "question": "Do you offer student discounts?",
        "gold": "Yes, students get 10% off with a valid student email address.",
        "answer": "Yes, students receive 10% off when they verify with a valid student email.",
    },
    {
        "id": "bks-10",
        "question": "Can I cancel an order before it ships?",
        "gold": "Yes, orders can be cancelled free of charge before they ship.",
        "answer": "Yes, you can cancel your order free of charge as long as it has not shipped yet.",
    },
    {
        "id": "bks-11",
        "question": "Which payment methods do you accept?",
        "gold": "We accept Visa, Mastercard, Amex, and PayPal.",
        "answer": "We accept Visa, Mastercard, American Express, and PayPal.",
    },
    {
        "id": "bks-12",
        "question": "How long does delivery take within the US?",
        "gold": "US delivery takes 3-5 business days with standard shipping.",
        "answer": "Standard shipping within the US takes 3-5 business days.",
    },
    {
        "id": "bks-13",
        "question": "Do you have a loyalty program?",
        "gold": "Yes, the Bookworm Club earns 1 point per dollar, redeemable for discounts.",
        "answer": "Yes, our Bookworm Club gives you 1 point per dollar spent, which you can redeem for discounts.",
    },
    {
        # Deliberately weak answer: wrong price, missing the key fact.
        "id": "bks-14",
        "question": "What is the price of 'The Midnight Bakery' paperback?",
        "gold": "The paperback of 'The Midnight Bakery' costs $14.99.",
        "answer": "It is a great book and everyone loves it. You should read it soon.",
    },
    {
        # Deliberately weak answer: off-topic.
        "id": "bks-15",
        "question": "Can I pick up my order in store?",
        "gold": "Yes, in-store pickup is available at our Portland location with 2 hours notice.",
        "answer": "Our store is open every day and we have lots of books on the shelves.",
    },
]
